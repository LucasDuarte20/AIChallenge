from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.repositories import materials_repo
from app.schemas.materials import MaterialStockRead
from app.services.search_service import search_materials

router = APIRouter(tags=["stock"])


@router.get("/stock")
def get_stock(
    material_code: str = Query(..., description="Código del material"),
    db: Session = Depends(get_db),
):
    material = materials_repo.get_by_code(db, material_code)
    if not material:
        raise HTTPException(status_code=404, detail=f"Material '{material_code}' no encontrado")
    return {
        "material_code": material.material_code,
        "material_raw": material.material_raw,
        "stock_actual": material.stock_actual,
        "stock_en_viaje": material.stock_en_viaje,
        "stock_pendiente": material.stock_pendiente,
        "stock_a_comprar": material.stock_a_comprar,
    }


@router.get("/price")
def get_price(
    material_code: str = Query(..., description="Código del material"),
    db: Session = Depends(get_db),
):
    material = materials_repo.get_by_code(db, material_code)
    if not material:
        raise HTTPException(status_code=404, detail=f"Material '{material_code}' no encontrado")
    return {
        "material_code": material.material_code,
        "material_raw": material.material_raw,
        "costo_estante_usd_unit": material.costo_estante_usd_unit,
        "stock_actual_x_costo_usd": material.stock_actual_x_costo_usd,
    }
