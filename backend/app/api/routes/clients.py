import logging
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.database import get_db
from app.schemas.import_jobs import ImportJobRead, ImportJobResult
from app.services.clients_import_service import import_clients_excel

router = APIRouter(prefix="/clients", tags=["clients"])
logger = logging.getLogger(__name__)


@router.post("/import-excel", response_model=ImportJobResult)
def import_clients(
    file: UploadFile = File(...),
    sheet_name: str = Form("LISTA DE INDUSTRIA"),
    # 0 = auto-detectar fila de encabezados (recomendado). 2 o 3 si tu Excel es fijo.
    header_row_index: int = Form(0),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos .xlsx o .xls")

    dest = Path(settings.data_dir) / file.filename
    try:
        with dest.open("wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as exc:
        logger.error("Error guardando archivo: %s", exc)
        raise HTTPException(status_code=500, detail=f"Error guardando archivo: {exc}")

    job = import_clients_excel(db, file_path=str(dest), sheet_name=sheet_name, header_row_index=header_row_index)
    return ImportJobResult(
        job=ImportJobRead.model_validate(job),
        message=f"Importación clientes {'exitosa' if job.status == 'success' else 'fallida'}: "
        f"{job.rows_total or 0} filas leídas.",
    )


@router.get("/executives")
def list_executives(db: Session = Depends(get_db)):
    """
    Lista códigos de Vendedor disponibles con cantidad de clientes.
    Útil para saber qué executive_code usar en /plans/generate.
    """
    from sqlalchemy import func
    from app.models.tables import Customer

    rows = (
        db.query(Customer.executive_code, func.count(Customer.id))
        .filter(Customer.executive_code.isnot(None))
        .group_by(Customer.executive_code)
        .order_by(func.count(Customer.id).desc())
        .all()
    )
    return [{"executive_code": code, "customers": count} for code, count in rows if code]

