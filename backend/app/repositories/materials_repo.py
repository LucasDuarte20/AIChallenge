import logging
from typing import Optional

from rapidfuzz import fuzz, process
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from app.models.tables import MaterialStock

logger = logging.getLogger(__name__)


def get_by_id(db: Session, material_id: int) -> Optional[MaterialStock]:
    return db.query(MaterialStock).filter(MaterialStock.id == material_id).first()


def get_by_code(db: Session, code: str) -> Optional[MaterialStock]:
    return (
        db.query(MaterialStock)
        .filter(func.lower(MaterialStock.material_code) == code.lower())
        .first()
    )


def get_by_mlfb(db: Session, mlfb: str) -> Optional[MaterialStock]:
    return (
        db.query(MaterialStock)
        .filter(func.lower(MaterialStock.material_mlfb) == mlfb.lower())
        .first()
    )


def search(db: Session, query: str, limit: int = 20) -> list[MaterialStock]:
    """Búsqueda por código, MLFB o nombre con ILIKE."""
    pattern = f"%{query}%"
    return (
        db.query(MaterialStock)
        .filter(
            or_(
                MaterialStock.material_code.ilike(pattern),
                MaterialStock.material_mlfb.ilike(pattern),
                MaterialStock.material_name.ilike(pattern),
                MaterialStock.material_raw.ilike(pattern),
            )
        )
        .limit(limit)
        .all()
    )


def fuzzy_search(db: Session, query: str, limit: int = 10, threshold: int = 60) -> list[MaterialStock]:
    """Búsqueda fuzzy usando rapidfuzz sobre material_name y material_raw."""
    all_materials = db.query(MaterialStock).all()
    if not all_materials:
        return []

    candidates = [(m.material_raw or "", m) for m in all_materials]
    names_only = [c[0] for c in candidates]

    matches = process.extract(query, names_only, scorer=fuzz.token_set_ratio, limit=limit * 3)
    results = []
    for match_str, score, idx in matches:
        if score >= threshold:
            results.append(candidates[idx][1])
        if len(results) >= limit:
            break

    return results


def get_with_pending_stock(db: Session) -> list[MaterialStock]:
    return (
        db.query(MaterialStock)
        .filter(MaterialStock.stock_pendiente > 0)
        .order_by(MaterialStock.stock_pendiente.desc())
        .all()
    )


def get_buy_list(db: Session) -> list[MaterialStock]:
    return (
        db.query(MaterialStock)
        .filter(MaterialStock.stock_a_comprar > 0)
        .order_by(MaterialStock.stock_a_comprar.desc())
        .all()
    )


def upsert(db: Session, data: dict) -> tuple[MaterialStock, bool]:
    """
    Actualiza si existe (material_code + material_mlfb), inserta si no.
    Retorna (material, was_inserted).
    """
    existing = None
    if data.get("material_code") and data.get("material_mlfb"):
        existing = (
            db.query(MaterialStock)
            .filter(
                func.lower(MaterialStock.material_code) == str(data["material_code"]).lower(),
                func.lower(MaterialStock.material_mlfb) == str(data["material_mlfb"]).lower(),
            )
            .first()
        )
    elif data.get("material_code"):
        existing = get_by_code(db, data["material_code"])

    if existing:
        for key, value in data.items():
            setattr(existing, key, value)
        db.flush()
        return existing, False
    else:
        material = MaterialStock(**data)
        db.add(material)
        db.flush()
        return material, True
