from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.tables import PlanJob, VisitPlan


def create_plan_job(db: Session, year: int, executive_code: str | None) -> PlanJob:
    job = PlanJob(year=year, scope_executive_code=executive_code, status="started")
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def finish_plan_job_success(db: Session, job: PlanJob, customers_total: int, visits_planned: int) -> PlanJob:
    job.status = "success"
    job.customers_total = customers_total
    job.visits_planned = visits_planned
    job.finished_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    return job


def finish_plan_job_failed(db: Session, job: PlanJob, error_details: str) -> PlanJob:
    job.status = "failed"
    job.error_details = error_details
    job.finished_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    return job


def clear_plan(db: Session, year: int, executive_code: str | None = None) -> int:
    q = db.query(VisitPlan).filter(VisitPlan.year == year)
    if executive_code:
        q = q.filter(func.lower(VisitPlan.executive_code) == executive_code.lower())
    deleted = q.delete(synchronize_session=False)
    db.commit()
    return deleted


def insert_visits(db: Session, visits: list[VisitPlan]) -> None:
    db.add_all(visits)
    db.commit()


def list_visits(db: Session, executive_code: str, year: int) -> list[VisitPlan]:
    return (
        db.query(VisitPlan)
        .filter(func.lower(VisitPlan.executive_code) == executive_code.lower(), VisitPlan.year == year)
        .order_by(VisitPlan.visit_date.asc(), VisitPlan.day_order.asc().nulls_last())
        .all()
    )

