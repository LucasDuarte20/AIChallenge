import asyncio
import logging

from sqlalchemy.orm import Session

from app.repositories.customers_repo import list_needing_geocode
from app.utils.geocode import geocode_uy_address

logger = logging.getLogger(__name__)


async def geocode_missing_customers(db: Session, batch_size: int = 50, delay_seconds: float = 1.0) -> dict:
    """
    Geocodifica clientes que no tengan lat/lon.
    MVP: Nominatim requiere rate limit; usamos un delay simple.
    """
    customers = list_needing_geocode(db, limit=batch_size)
    updated = 0
    failed = 0

    for c in customers:
        try:
            res = await geocode_uy_address(c.address_raw or "")
            c.lat = res.lat
            c.lon = res.lon
            c.department = res.department
            c.geocode_status = res.status
            c.geocode_provider = res.provider
            updated += 1 if res.status == "ok" else 0
            failed += 1 if res.status != "ok" else 0
        except Exception as exc:
            logger.warning("Fallo geocode customer id=%s: %s", c.id, exc)
            c.geocode_status = "failed"
            failed += 1

        db.commit()
        await asyncio.sleep(delay_seconds)

    return {"batch_size": len(customers), "updated_ok": updated, "failed_or_missing": failed}

