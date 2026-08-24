from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas, security
from ..database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=schemas.DashboardOut)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    latest_resume = (
        db.query(models.Resume)
        .filter(models.Resume.user_id == current_user.id)
        .order_by(models.Resume.created_at.desc())
        .first()
    )
    applications_count = (
        db.query(models.Application).filter(models.Application.user_id == current_user.id).count()
    )
    interviews_count = (
        db.query(models.Application)
        .filter(models.Application.user_id == current_user.id, models.Application.status == "Interview")
        .count()
    )
    saved_jobs_count = (
        db.query(models.SavedJob).filter(models.SavedJob.user_id == current_user.id).count()
    )
    latest_interview = (
        db.query(models.InterviewResult)
        .filter(models.InterviewResult.user_id == current_user.id)
        .order_by(models.InterviewResult.created_at.desc())
        .first()
    )

    return schemas.DashboardOut(
        resume_score=latest_resume.ats_score if latest_resume else None,
        applications_count=applications_count,
        interviews_count=interviews_count,
        saved_jobs_count=saved_jobs_count,
        latest_interview_score=latest_interview.score if latest_interview else None,
    )
