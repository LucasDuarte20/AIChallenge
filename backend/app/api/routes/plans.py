from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.database import get_db
from app.repositories.plan_repo import list_visits
from app.services.plan_export_service import export_plan_to_xlsx
from app.services.planner_service import generate_year_plan

router = APIRouter(prefix="/plans", tags=["plans"])


@router.post("/generate")
def generate_plan(
    year: int = Query(..., ge=2020, le=2100),
    executive_code: str | None = Query(None, description="Si se omite, genera para todos los vendedores"),
    visits_per_day: Optional[int] = Query(
        None,
        ge=1,
        le=10,
        description="Si se omite, usa VISITS_PER_DAY del .env (default 2)",
    ),
    start_day: str | None = Query(None, description="YYYY-MM-DD. Si se omite: hoy + 14 días"),
    horizon_days: int = Query(365, ge=30, le=400, description="Duración del plan en días (default 365)"),
    db: Session = Depends(get_db),
):
    if start_day:
        sd = date.fromisoformat(start_day)
    else:
        sd = date.today() + timedelta(days=14)
    vpd = visits_per_day if visits_per_day is not None else settings.visits_per_day_default
    return {
        "results": generate_year_plan(
            db,
            year=year,
            executive_code=executive_code,
            visits_per_day=vpd,
            start_day=sd,
            horizon_days=horizon_days,
        )
    }


@router.get("/{executive_code}")
def get_plan(executive_code: str, year: int = Query(...), db: Session = Depends(get_db)):
    visits = list_visits(db, executive_code=executive_code, year=year)
    return {
        "executive_code": executive_code,
        "year": year,
        "total": len(visits),
        "items": [
            {
                "visit_date": v.visit_date.isoformat(),
                "day_order": v.day_order,
                "customer_name": v.customer_name,
                "customer_address": v.customer_address,
                "department": v.department,
            }
            for v in visits
        ],
    }


@router.get("/{executive_code}/export.xlsx")
def export_plan(executive_code: str, year: int = Query(...), db: Session = Depends(get_db)):
    path = export_plan_to_xlsx(db, executive_code=executive_code, year=year)
    if not path.exists():
        raise HTTPException(status_code=404, detail="No se pudo generar el archivo")
    return FileResponse(
        path=str(path),
        filename=path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

