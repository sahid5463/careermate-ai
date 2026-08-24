from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, security
from ..database import get_db

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=List[schemas.JobOut])
def list_jobs(
    q: Optional[str] = None,
    location: Optional[str] = None,
    experience: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Job)
    if q:
        query = query.filter(models.Job.title.ilike(f"%{q}%"))
    if location:
        query = query.filter(models.Job.location.ilike(f"%{location}%"))
    if experience:
        query = query.filter(models.Job.experience.ilike(f"%{experience}%"))
    return query.order_by(models.Job.created_at.desc()).all()


@router.get("/{job_id}", response_model=schemas.JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/{job_id}/save")
def save_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    exists = db.query(models.SavedJob).filter_by(user_id=current_user.id, job_id=job_id).first()
    if exists:
        return {"detail": "Already saved"}

    db.add(models.SavedJob(user_id=current_user.id, job_id=job_id))
    db.commit()
    return {"detail": "Job saved"}


@router.get("/saved/list", response_model=List[schemas.JobOut])
def list_saved_jobs(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    return (
        db.query(models.Job)
        .join(models.SavedJob, models.SavedJob.job_id == models.Job.id)
        .filter(models.SavedJob.user_id == current_user.id)
        .all()
    )
