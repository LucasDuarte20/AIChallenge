from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.tables import ImportJob


def create(db: Session, file_name: str, sheet_name: str) -> ImportJob:
    job = ImportJob(file_name=file_name, sheet_name=sheet_name, status="started")
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def update_success(db: Session, job: ImportJob, rows_total: int, rows_inserted: int, rows_failed: int) -> ImportJob:
    job.status = "success"
    job.rows_total = rows_total
    job.rows_inserted = rows_inserted
    job.rows_failed = rows_failed
    job.finished_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(job)
    return job


def update_failed(db: Session, job: ImportJob, error: str, rows_total: int = 0, rows_failed: int = 0) -> ImportJob:
    job.status = "failed"
    job.rows_total = rows_total
    job.rows_failed = rows_failed
    job.error_details = error
    job.finished_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(job)
    return job


def get_all(db: Session, limit: int = 20) -> list[ImportJob]:
    return db.query(ImportJob).order_by(ImportJob.started_at.desc()).limit(limit).all()


def get_by_id(db: Session, job_id: int) -> Optional[ImportJob]:
    return db.query(ImportJob).filter(ImportJob.id == job_id).first()
