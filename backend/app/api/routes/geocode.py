from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.services.geocode_service import geocode_missing_customers

router = APIRouter(prefix="/geocode", tags=["geocode"])


@router.post("/run")
async def run_geocode(
    batch_size: int = Query(50, ge=1, le=300),
    delay_seconds: float = Query(1.0, ge=0.0, le=10.0),
    db: Session = Depends(get_db),
):
    return await geocode_missing_customers(db, batch_size=batch_size, delay_seconds=delay_seconds)

