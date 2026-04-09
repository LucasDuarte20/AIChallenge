import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.tables import MaterialStock
from app.repositories import materials_repo

logger = logging.getLogger(__name__)


def find_material(
    db: Session,
    code: Optional[str] = None,
    mlfb: Optional[str] = None,
    name_query: Optional[str] = None,
    fuzzy: bool = False,
) -> Optional[MaterialStock]:
    """
    Busca un material por código, MLFB o nombre.
    Prioridad: code > mlfb > name_query (exact/ilike) > fuzzy.
    """
    if code:
        material = materials_repo.get_by_code(db, code)
        if material:
            return material

    if mlfb:
        material = materials_repo.get_by_mlfb(db, mlfb)
        if material:
            return material

    if name_query:
        results = materials_repo.search(db, name_query, limit=1)
        if results:
            return results[0]
        if fuzzy:
            results = materials_repo.fuzzy_search(db, name_query, limit=1, threshold=55)
            if results:
                return results[0]

    return None


def search_materials(db: Session, query: str, limit: int = 20) -> list[MaterialStock]:
    """Búsqueda combinada: primero ILIKE, luego fuzzy si hay pocos resultados."""
    results = materials_repo.search(db, query, limit=limit)
    if len(results) < 3:
        fuzzy_results = materials_repo.fuzzy_search(db, query, limit=limit, threshold=55)
        seen_ids = {m.id for m in results}
        for m in fuzzy_results:
            if m.id not in seen_ids:
                results.append(m)
                seen_ids.add(m.id)
    return results[:limit]
