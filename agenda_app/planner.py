from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Iterable

from agenda_app.models import ClientRow


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _priority_score(c: ClientRow) -> float:
    size = (c.client_size or "").lower().strip()
    pot = (c.potential or "").lower().strip()
    sm = {"chico": 1.0, "medio": 2.0, "grande": 3.0}
    pm = {"bajo": 1.0, "medio": 2.0, "alto": 3.0}
    s = sm.get(size, 2.0)
    p = pm.get(pot, 2.0)
    return s * 10.0 + p


def _visits_per_year(c: ClientRow) -> int:
    size = (c.client_size or "medio").lower().strip()
    pot = (c.potential or "medio").lower().strip()
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


def scheduling_urgency(c: ClientRow, ref_date: date) -> float:
    """
    Mayor valor = debe recibir slots antes en la agenda.
    Combina valor del cliente y tiempo desde último contacto.
    """
    value = _priority_score(c)
    
    # 1. INCLUSIÓN OBLIGATORIA (Siguiente visita agendada)
    if c.next_visit is not None:
        # Si la fecha agendada es hoy o futuro
        if c.next_visit >= ref_date:
            return 1e9 + value  # Prioridad absoluta
            
    # 2. CLIENTES NUEVOS (Sin fecha de última visita)
    if c.last_visit is None:
        return 1e6 + (value * 100.0) # Muy alta prioridad

    # 3. PRIORIDAD POR ANTIGÜEDAD
    # Asegurar que ambos son objetos date
    lv = c.last_visit
    if isinstance(lv, datetime):
        lv = lv.date()
        
    days = max(0, (ref_date - lv).days)
    return value * (10.0 * math.log1p(days) + 0.05 * days)


def _order_nearest_neighbor(clients: list[ClientRow]) -> list[ClientRow]:
    with_geo = [c for c in clients if c.lat is not None and c.lon is not None]
    without_geo = [c for c in clients if c.lat is None or c.lon is None]
    if len(with_geo) <= 2:
        return with_geo + without_geo

    remaining = with_geo[:]
    ordered: list[ClientRow] = [remaining.pop(0)]
    while remaining:
        last = ordered[-1]
        remaining.sort(
            key=lambda c: _haversine_km(last.lat or 0, last.lon or 0, c.lat or 0, c.lon or 0)
        )
        ordered.append(remaining.pop(0))
    return ordered + without_geo


def _business_slots(
    start_day: date,
    horizon_days: int,
    visits_per_day: int,
) -> list[datetime]:
    visits_per_day = max(1, min(10, int(visits_per_day)))
    work_start = time(9, 0)
    work_end = time(18, 0)
    total_minutes = (work_end.hour * 60 + work_end.minute) - (work_start.hour * 60 + work_start.minute)
    step = max(30, total_minutes // visits_per_day)

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


def next_monday_after(today: date) -> date:
    """Próximo lunes estrictamente posterior a `today` (si hoy es lunes, el siguiente lunes)."""
    days_ahead = (7 - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return today + timedelta(days=days_ahead)


def monday_week_after_next(today: date) -> date:
    """Lunes de la semana subsiguiente a la 'próxima semana'."""
    first = next_monday_after(today)
    return first + timedelta(days=7)


def start_date_from_choice(choice: str, today: date) -> date:
    c = choice.lower().strip()
    if c == "hoy":
        return today
    if c == "mañana" or c == "manana":
        return today + timedelta(days=1)
    if c in ("próxima semana", "proxima semana", "semana_siguiente"):
        return next_monday_after(today)
    if c in ("en dos semanas", "semana_posterior", "siguiente_a_la_siguiente"):
        return monday_week_after_next(today)
    return today


@dataclass
class PlannedVisit:
    client: ClientRow
    visit_at: datetime


def build_agenda(
    clients: list[ClientRow],
    start_day: date,
    horizon_days: int,
    visits_per_day: int = 2,
    include_empresas: bool = True,
    include_personas: bool = True,
    include_mvd: bool = True,
    include_interior: bool = True,
) -> tuple[list[PlannedVisit], dict[int, date]]:
    """
    Ordena por urgencia + depto + vecino más cercano,
    expande por frecuencia anual y asigna slots.
    Devuelve visitas planificadas y mapa row_index -> primera fecha de próxima visita en el horizonte.
    """
    pool = []
    for c in clients:
        if not c.name:
            continue
            
        tipo = (c.client_size or "").lower().strip()
        is_empresa = (tipo == "empresa")
        is_persona = (tipo == "persona")
        
        if tipo:
            if not include_empresas and is_empresa:
                continue
            if not include_personas and is_persona:
                continue

        dep = (c.department or "").lower().strip()
        is_mvd = (dep == "montevideo")
        
        if dep:
            if not include_mvd and is_mvd:
                continue
            if not include_interior and not is_mvd:
                continue
                
        pool.append(c)

    if not pool:
        return [], {}

    by_dept: dict[str, list[ClientRow]] = {}
    for c in pool:
        dept = (c.department or "SIN_DEPARTAMENTO").strip()
        by_dept.setdefault(dept, []).append(c)

    dept_order = sorted(by_dept.keys(), key=lambda k: len(by_dept[k]), reverse=True)

    base_order: list[ClientRow] = []
    for dept in dept_order:
        group = by_dept[dept][:]
        group.sort(key=lambda c: -scheduling_urgency(c, start_day))
        base_order.extend(_order_nearest_neighbor(group))

    remaining = {}
    for c in base_order:
        freq = _visits_per_year(c)
        # Si tiene visita agendada vigente, asegurar al menos 1 aparición primordial
        if c.next_visit and c.next_visit >= start_day:
            freq = max(1, freq)
        remaining[id(c)] = freq

    max_v = max(remaining.values()) if remaining else 1
    expanded: list[ClientRow] = []
    for _ in range(max_v):
        for c in base_order:
            if remaining.get(id(c), 0) > 0:
                expanded.append(c)
                remaining[id(c)] -= 1

    slots = _business_slots(start_day=start_day, horizon_days=horizon_days, visits_per_day=visits_per_day)
    if not slots:
        raise ValueError("No hay días hábiles en el horizonte indicado.")

    visits: list[PlannedVisit] = []
    for idx, c in enumerate(expanded):
        if idx >= len(slots):
            break
        visits.append(PlannedVisit(client=c, visit_at=slots[idx]))

    first_next: dict[int, date] = {}
    for pv in visits:
        rid = pv.client.row_index
        d = pv.visit_at.date()
        if rid not in first_next:
            first_next[rid] = d

    return visits, first_next


def visits_to_simple_rows(visits: Iterable[PlannedVisit]) -> list[dict]:
    out = []
    for pv in visits:
        vd = pv.visit_at
        out.append(
            {
                "fecha": vd.date().isoformat(),
                "hora": vd.strftime("%H:%M"),
                "cliente": pv.client.name,
                "dirección": pv.client.address_raw or "",
                "departamento": pv.client.department or "",
            }
        )
    return out
