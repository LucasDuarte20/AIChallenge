import os
import shutil
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.database import get_db
from app.repositories import import_jobs_repo
from app.schemas.import_jobs import ImportJobRead, ImportJobResult
from app.services.import_service import import_excel_file

router = APIRouter(prefix="/import-excel", tags=["import"])
logger = logging.getLogger(__name__)


@router.post("", response_model=ImportJobResult)
def import_excel(
    file: UploadFile = File(...),
    sheet_name: str = Form("Sheet1"),
    db: Session = Depends(get_db),
):
    """Sube y procesa un archivo Excel. El archivo se guarda en DATA_DIR."""
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos .xlsx o .xls")

    dest = Path(settings.data_dir) / file.filename
    try:
        with dest.open("wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as exc:
        logger.error("Error guardando archivo: %s", exc)
        raise HTTPException(status_code=500, detail=f"Error guardando archivo: {exc}")

    job = import_excel_file(db, file_path=str(dest), sheet_name=sheet_name)

    return ImportJobResult(
        job=ImportJobRead.model_validate(job),
        message=f"Importación {'exitosa' if job.status == 'success' else 'fallida'}: "
                f"{job.rows_inserted or 0} filas procesadas.",
    )


@router.get("/jobs", response_model=list[ImportJobRead])
def list_jobs(db: Session = Depends(get_db)):
    return import_jobs_repo.get_all(db)


@router.get("/jobs/{job_id}", response_model=ImportJobRead)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = import_jobs_repo.get_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    return job
