from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, security
from ..database import get_db

router = APIRouter(prefix="/api/applications", tags=["applications"])


@router.post("", response_model=schemas.ApplicationOut)
def create_application(
    payload: schemas.ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    job = db.query(models.Job).filter(models.Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    existing = (
        db.query(models.Application)
        .filter_by(user_id=current_user.id, job_id=payload.job_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Already applied to this job")

    application = models.Application(user_id=current_user.id, job_id=payload.job_id, status="Applied")
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@router.get("", response_model=List[schemas.ApplicationOut])
def list_applications(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    return (
        db.query(models.Application)
        .filter(models.Application.user_id == current_user.id)
        .order_by(models.Application.applied_date.desc())
        .all()
    )


@router.put("/{application_id}", response_model=schemas.ApplicationOut)
def update_application(
    application_id: int,
    payload: schemas.ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    application = (
        db.query(models.Application)
        .filter(models.Application.id == application_id, models.Application.user_id == current_user.id)
        .first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    application.status = payload.status
    if payload.interview_date:
        application.interview_date = payload.interview_date
    db.commit()
    db.refresh(application)
    return application
