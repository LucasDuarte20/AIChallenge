from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ImportJobRead(BaseModel):
    id: int
    file_name: str
    sheet_name: Optional[str] = None
    status: str
    rows_total: Optional[int] = None
    rows_inserted: Optional[int] = None
    rows_failed: Optional[int] = None
    error_details: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ImportJobResult(BaseModel):
    job: ImportJobRead
    message: str
