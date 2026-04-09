import logging
import traceback
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.tables import ImportJob
from app.repositories import import_jobs_repo, materials_repo
from app.utils.excel_parser import parse_excel

logger = logging.getLogger(__name__)


def import_excel_file(db: Session, file_path: str, sheet_name: str = "Sheet1") -> ImportJob:
    """
    Importa un archivo Excel a la base de datos.
    Registra el proceso en import_jobs y hace upsert de materiales.
    """
    path = Path(file_path)
    job = import_jobs_repo.create(db, file_name=path.name, sheet_name=sheet_name)
    logger.info("Import job #%d iniciado para '%s'", job.id, path.name)

    try:
        rows = parse_excel(file_path=path, sheet_name=sheet_name)
    except Exception as exc:
        logger.error("Error parseando Excel: %s", exc)
        return import_jobs_repo.update_failed(db, job, error=str(exc))

    rows_total = len(rows)
    rows_inserted = 0
    rows_failed = 0
    errors: list[str] = []

    for i, row_data in enumerate(rows):
        try:
            row_data["source_file"] = path.name
            row_data["source_sheet"] = sheet_name
            materials_repo.upsert(db, row_data)
            rows_inserted += 1
        except Exception as exc:
            rows_failed += 1
            err_msg = f"Fila {i + 2}: {exc}"
            errors.append(err_msg)
            logger.warning(err_msg)

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("Error al commit final: %s", exc)
        return import_jobs_repo.update_failed(db, job, error=str(exc), rows_total=rows_total, rows_failed=rows_total)

    error_details = "\n".join(errors[:50]) if errors else None
    job = import_jobs_repo.update_success(
        db,
        job=job,
        rows_total=rows_total,
        rows_inserted=rows_inserted,
        rows_failed=rows_failed,
    )
    if error_details:
        job.error_details = error_details
        db.commit()

    logger.info(
        "Import job #%d completado: %d/%d filas ok, %d fallidas",
        job.id, rows_inserted, rows_total, rows_failed,
    )
    return job
