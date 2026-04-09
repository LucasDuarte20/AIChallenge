import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.repositories import import_jobs_repo
from app.repositories.customers_repo import upsert_customer
from app.utils.clients_excel_parser import parse_clients_excel

logger = logging.getLogger(__name__)


def import_clients_excel(db: Session, file_path: str, sheet_name: str = "LISTA DE INDUSTRIA", header_row_index: int = 0):
    path = Path(file_path)
    job = import_jobs_repo.create(db, file_name=path.name, sheet_name=sheet_name)

    try:
        rows = parse_clients_excel(path, sheet_name=sheet_name, header_row_index=header_row_index)
    except Exception as exc:
        logger.error("Error parseando Excel clientes: %s", exc)
        return import_jobs_repo.update_failed(db, job, error=str(exc))

    total = len(rows)
    inserted = 0
    failed = 0
    errors: list[str] = []

    for i, r in enumerate(rows, start=1):
        try:
            r["source_file"] = path.name
            r["source_sheet"] = sheet_name
            _, was_inserted = upsert_customer(db, r)
            if was_inserted:
                inserted += 1
        except Exception as exc:
            failed += 1
            errors.append(f"Fila {i}: {exc}")

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        return import_jobs_repo.update_failed(db, job, error=str(exc), rows_total=total, rows_failed=total)

    job = import_jobs_repo.update_success(db, job, rows_total=total, rows_inserted=inserted, rows_failed=failed)
    if errors:
        job.error_details = "\n".join(errors[:50])
        db.commit()
    return job

