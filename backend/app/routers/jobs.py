import os
import json
import urllib.request
import urllib.parse
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, security
from ..database import get_db

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "").strip()
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "").strip()
ADZUNA_COUNTRY = os.getenv("ADZUNA_COUNTRY", "in").strip()  # in = India


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


@router.get("/live/search")
def live_job_search(
    q: str = "software developer",
    location: Optional[str] = None,
    page: int = 1,
):
    """
    Searches real, current job listings from across the internet via the
    Adzuna job-search API (a legitimate aggregator, not scraping). Requires
    ADZUNA_APP_ID and ADZUNA_APP_KEY to be set as environment variables —
    get free credentials at https://developer.adzuna.com
    """
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        raise HTTPException(
            status_code=503,
            detail=(
                "Live job search isn't configured yet. Get a free App ID and "
                "App Key at https://developer.adzuna.com and set ADZUNA_APP_ID "
                "and ADZUNA_APP_KEY as environment variables."
            ),
        )

    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": 20,
        "what": q,
        "content-type": "application/json",
    }
    if location:
        params["where"] = location

    url = (
        f"https://api.adzuna.com/v1/api/jobs/{ADZUNA_COUNTRY}/search/{page}"
        f"?{urllib.parse.urlencode(params)}"
    )

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CareerMateAI/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Could not reach job search provider: {e}")

    results = []
    for item in data.get("results", []):
        results.append({
            "title": item.get("title"),
            "company": (item.get("company") or {}).get("display_name"),
            "location": (item.get("location") or {}).get("display_name"),
            "salary_min": item.get("salary_min"),
            "salary_max": item.get("salary_max"),
            "description": item.get("description"),
            "apply_url": item.get("redirect_url"),
            "created": item.get("created"),
        })

    return {"count": data.get("count", len(results)), "results": results}


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
