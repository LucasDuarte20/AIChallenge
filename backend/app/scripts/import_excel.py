"""Script CLI para importar Excel desde línea de comandos.

Uso:
    python -m app.scripts.import_excel nombre_archivo.xlsx [Sheet1]
"""
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    if len(sys.argv) < 2:
        print("Uso: python -m app.scripts.import_excel <archivo.xlsx> [nombre_hoja]")
        sys.exit(1)

    file_name = sys.argv[1]
    sheet_name = sys.argv[2] if len(sys.argv) > 2 else "Sheet1"

    from app.core.config import settings
    from app.models.database import SessionLocal, engine
    from app.models.tables import Base
    from app.services.import_service import import_excel_file

    Base.metadata.create_all(bind=engine)

    file_path = Path(settings.data_dir) / file_name
    if not file_path.exists():
        print(f"ERROR: Archivo no encontrado: {file_path}")
        sys.exit(1)

    db = SessionLocal()
    try:
        job = import_excel_file(db, str(file_path), sheet_name)
        print(f"\nResultado importación:")
        print(f"  Status:   {job.status}")
        print(f"  Total:    {job.rows_total}")
        print(f"  Ok:       {job.rows_inserted}")
        print(f"  Fallidas: {job.rows_failed}")
        if job.error_details:
            print(f"  Errores:\n{job.error_details[:500]}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
