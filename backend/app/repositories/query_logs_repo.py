from sqlalchemy.orm import Session

from app.models.tables import QueryLog


def create(
    db: Session,
    user_query: str,
    detected_intent: str,
    response_text: str,
    extracted_material_code: str | None = None,
    extracted_material_name: str | None = None,
    matched_material_id: int | None = None,
) -> QueryLog:
    log = QueryLog(
        user_query=user_query,
        detected_intent=detected_intent,
        extracted_material_code=extracted_material_code,
        extracted_material_name=extracted_material_name,
        matched_material_id=matched_material_id,
        response_text=response_text,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_recent(db: Session, limit: int = 50) -> list[QueryLog]:
    return db.query(QueryLog).order_by(QueryLog.created_at.desc()).limit(limit).all()
