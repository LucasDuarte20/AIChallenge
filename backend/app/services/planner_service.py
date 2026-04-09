import logging
import math
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.tables import Customer, VisitPlan
from app.repositories import plan_repo
from app.repositories.customers_repo import list_all, list_by_executive

logger = logging.getLogger(__name__)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _order_nearest_neighbor(customers: list[Customer]) -> list[Customer]:
    """
    Orden simple para que las visitas queden 'cerca' dentro de un grupo.
    Si no hay lat/lon, devuelve el orden original.
    """
    with_geo = [c for c in customers if c.lat is not None and c.lon is not None]
    without_geo = [c for c in customers if c.lat is None or c.lon is None]
    if len(with_geo) <= 2:
        return with_geo + without_geo

    remaining = with_geo[:]
    ordered: list[Customer] = [remaining.pop(0)]
    while remaining:
        last = ordered[-1]
        remaining.sort(key=lambda c: _haversine_km(last.lat or 0, last.lon or 0, c.lat or 0, c.lon or 0))
        ordered.append(remaining.pop(0))
    return ordered + without_geo


def _priority_score(c: Customer) -> float:
    """
    Mayor puntaje = más prioridad (agenda: aparecen antes en el año).
    Si faltan tipo/potencial, neutro (medio/medio).
    """
    size = (c.client_size or "").lower().strip()
    pot = (c.potential or "").lower().strip()
    sm = {"chico": 1.0, "medio": 2.0, "grande": 3.0}
    pm = {"bajo": 1.0, "medio": 2.0, "alto": 3.0}
    s = sm.get(size, 2.0)
    p = pm.get(pot, 2.0)
    return s * 10.0 + p


def _visits_per_year(c: Customer) -> int:
    """
    Reglas simples de frecuencia (MVP). Ajustables.
    Si faltan tipo/potencial => neutro.
    """
    size = (c.client_size or "medio").lower().strip()
    pot = (c.potential or "medio").lower().strip()
    # Matriz: (size, pot) -> visitas/año
    matrix = {
        ("grande", "alto"): 12,
        ("grande", "medio"): 6,
        ("grande", "bajo"): 4,
        ("medio", "alto"): 6,
        ("medio", "medio"): 4,
        ("medio", "bajo"): 2,
        ("chico", "alto"): 4,
        ("chico", "medio"): 2,
        ("chico", "bajo"): 1,
    }
    return int(matrix.get((size, pot), 4))


def _business_slots(
    start_day: date,
    horizon_days: int,
    visits_per_day: int,
) -> list[datetime]:
    """
    Genera slots de visitas en días hábiles (lun-vie) entre 09:00 y 18:00.
    MVP: slots equiespaciados (sin modelar duración variable ni tiempos de viaje).
    """
    visits_per_day = max(1, min(10, int(visits_per_day)))
    work_start = time(9, 0)
    work_end = time(18, 0)
    total_minutes = (work_end.hour * 60 + work_end.minute) - (work_start.hour * 60 + work_start.minute)
    step = max(30, total_minutes // visits_per_day)  # mínimo 30 min

    slots: list[datetime] = []
    d = start_day
    end_day = start_day + timedelta(days=int(horizon_days))
    while d < end_day:
        if d.weekday() < 5:
            base = datetime(d.year, d.month, d.day, work_start.hour, work_start.minute, tzinfo=timezone.utc)
            for i in range(visits_per_day):
                minute_offset = i * step
                if minute_offset >= total_minutes:
                    break
                slots.append(base + timedelta(minutes=minute_offset))
        d += timedelta(days=1)
    return slots


def generate_year_plan_for_executive(
    db: Session,
    year: int,
    executive_code: str,
    visits_per_day: int = 2,
    start_day: date | None = None,
    horizon_days: int = 365,
) -> dict:
    """
    Agenda por 1 año desde start_day (default: 1/1 del año si no se pasa; el endpoint usa hoy+14).
    Agrupa por departamento (vacío => SIN_DEPARTAMENTO).
    Dentro de cada depto: ordena por prioridad (Tipo/Potencial) y luego nearest-neighbor por coordenadas.
    Distribuye en días hábiles (09–18) con hasta N visitas por día.

    Frecuencia:
      - Si hay Tipo/Potencial: asigna visitas/año según matriz simple.
      - Si no hay: neutro (medio/medio).
    """
    customers = list_by_executive(db, executive_code)
    customers = [c for c in customers if c.name]
    customers_total = len(customers)
    if customers_total == 0:
        return {"executive_code": executive_code, "year": year, "customers_total": 0, "visits_planned": 0}

    if start_day is None:
        start_day = date(year, 1, 1)

    by_dept: dict[str, list[Customer]] = {}
    for c in customers:
        dept = (c.department or "SIN_DEPARTAMENTO").strip()
        by_dept.setdefault(dept, []).append(c)

    # Orden de departamentos: primero los que tengan más clientes (reduce saltos)
    dept_order = sorted(by_dept.keys(), key=lambda k: len(by_dept[k]), reverse=True)

    # Primero orden base por depto + prioridad + cercanía
    base_order: list[Customer] = []
    for dept in dept_order:
        group = by_dept[dept]
        group.sort(key=lambda c: -_priority_score(c))
        base_order.extend(_order_nearest_neighbor(group))

    # Expandir por frecuencia (visitas/año por cliente) y esparcirlas (round-robin)
    remaining = {c.id: _visits_per_year(c) for c in base_order}
    max_v = max(remaining.values()) if remaining else 1
    expanded: list[Customer] = []
    for _ in range(max_v):
        for c in base_order:
            if remaining.get(c.id, 0) > 0:
                expanded.append(c)
                remaining[c.id] -= 1

    slots = _business_slots(start_day=start_day, horizon_days=horizon_days, visits_per_day=visits_per_day)
    if not slots:
        raise ValueError("No se pudieron generar slots hábiles.")

    # Limpia plan anterior y genera nuevo
    plan_repo.clear_plan(db, year=year, executive_code=executive_code)

    visits: list[VisitPlan] = []
    for idx, c in enumerate(expanded):
        if idx >= len(slots):
            break  # si faltan slots, se recorta (MVP)
        visit_date = slots[idx]
        day_order = 1 + (idx % max(1, int(visits_per_day)))
        visits.append(
            VisitPlan(
                year=year,
                executive_code=executive_code,
                customer_id=c.id,
                visit_date=visit_date,
                day_order=day_order,
                customer_name=c.name,
                customer_address=c.address_raw,
                department=c.department,
            )
        )

    plan_repo.insert_visits(db, visits)

    return {
        "executive_code": executive_code,
        "year": year,
        "customers_total": customers_total,
        "visits_planned": len(visits),
        "visits_per_day": visits_per_day,
        "start_day": start_day.isoformat(),
        "horizon_days": horizon_days,
    }


def generate_year_plan(
    db: Session,
    year: int,
    executive_code: str | None = None,
    visits_per_day: int = 2,
    start_day: date | None = None,
    horizon_days: int = 365,
) -> list[dict]:
    if executive_code:
        return [generate_year_plan_for_executive(db, year, executive_code, visits_per_day, start_day=start_day, horizon_days=horizon_days)]

    customers = list_all(db)
    execs = sorted({(c.executive_code or "").strip() for c in customers if (c.executive_code or "").strip()})
    results: list[dict] = []
    for ex in execs:
        results.append(generate_year_plan_for_executive(db, year, ex, visits_per_day, start_day=start_day, horizon_days=horizon_days))
    return results

