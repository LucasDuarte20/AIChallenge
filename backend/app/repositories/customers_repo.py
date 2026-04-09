from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.tables import Customer


def upsert_customer(db: Session, data: dict) -> tuple[Customer, bool]:
    """
    Upsert por (customer_number, office) si existe; si no, por nombre+dirección.
    """
    cust = None
    if data.get("customer_number"):
        cust = (
            db.query(Customer)
            .filter(
                func.lower(Customer.customer_number) == str(data["customer_number"]).lower(),
                func.lower(Customer.office) == str(data.get("office") or "").lower(),
            )
            .first()
        )
    if not cust:
        cust = (
            db.query(Customer)
            .filter(
                func.lower(Customer.name) == str(data.get("name") or "").lower(),
                func.lower(Customer.address_raw) == str(data.get("address_raw") or "").lower(),
            )
            .first()
        )

    if cust:
        for k, v in data.items():
            setattr(cust, k, v)
        db.flush()
        return cust, False

    cust = Customer(**data)
    db.add(cust)
    db.flush()
    return cust, True


def list_by_executive(db: Session, executive_code: str) -> list[Customer]:
    return (
        db.query(Customer)
        .filter(func.lower(Customer.executive_code) == executive_code.lower())
        .all()
    )


def list_all(db: Session) -> list[Customer]:
    return db.query(Customer).all()


def list_needing_geocode(db: Session, limit: int = 200) -> list[Customer]:
    return (
        db.query(Customer)
        .filter(Customer.lat.is_(None), Customer.address_raw.isnot(None))
        .limit(limit)
        .all()
    )

