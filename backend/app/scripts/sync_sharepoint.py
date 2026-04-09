"""
Syncer simple: descarga Excel desde SharePoint y lo importa a PostgreSQL.
Pensado para correr en un contenedor aparte con un loop cada N segundos.
"""

import asyncio
import logging
import time
from pathlib import Path

from app.core.config import settings
from app.models.database import SessionLocal, engine
from app.models.tables import Base
from app.services.import_service import import_excel_file
from app.services.sharepoint_service import download_sharepoint_excel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


async def run_once() -> None:
    Base.metadata.create_all(bind=engine)

    dest_dir = Path(settings.data_dir) / "incoming"
    xlsx_path = await download_sharepoint_excel(dest_dir=dest_dir)

    db = SessionLocal()
    try:
        job = import_excel_file(db, file_path=str(xlsx_path), sheet_name=settings.sp_sheet_name)
        logger.info("Sync SharePoint -> import job #%s status=%s inserted=%s failed=%s",
                    job.id, job.status, job.rows_inserted, job.rows_failed)
    finally:
        db.close()


async def main() -> None:
    if not settings.sync_enabled:
        logger.info("SYNC_ENABLED=false. Saliendo.")
        return

    interval = max(60, int(settings.sync_interval_seconds))
    logger.info("Syncer SharePoint habilitado. Intervalo: %ds", interval)

    while True:
        try:
            await run_once()
        except Exception as exc:
            logger.exception("Fallo sync SharePoint: %s", exc)
        time.sleep(interval)


if __name__ == "__main__":
    asyncio.run(main())

