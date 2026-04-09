from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.tables import MaterialStock
from app.repositories import materials_repo
from app.schemas.materials import MaterialStockRead, MaterialStockSearchResult
from app.services.search_service import search_materials

router = APIRouter(prefix="/materials", tags=["materials"])


@router.get("/search", response_model=MaterialStockSearchResult)
def search(
    q: str = Query(..., min_length=1, description="Texto de búsqueda"),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
):
    results = search_materials(db, q, limit=limit)
    return MaterialStockSearchResult(
        items=[MaterialStockRead.model_validate(m) for m in results],
        total=len(results),
        query=q,
    )


@router.get("/{material_code}", response_model=MaterialStockRead)
def get_by_code(material_code: str, db: Session = Depends(get_db)):
    material = materials_repo.get_by_code(db, material_code)
    if not material:
        raise HTTPException(status_code=404, detail=f"Material '{material_code}' no encontrado")
    return MaterialStockRead.model_validate(material)


@router.get("", response_model=list[MaterialStockRead])
def list_materials(
    limit: int = Query(50, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    materials = db.query(MaterialStock).offset(offset).limit(limit).all()
    return [MaterialStockRead.model_validate(m) for m in materials]
