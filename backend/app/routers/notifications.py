import os
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from .. import models, security, email_utils
from ..database import get_db

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

CRON_SECRET = os.getenv("CRON_SECRET", "").strip()


@router.api_route("/interview-reminders", methods=["GET", "POST"])
def send_interview_reminders(
    db: Session = Depends(get_db),
    secret: str = "",
    x_cron_secret: str = Header(default=""),
):
    """
    Emails everyone whose interview is TOMORROW. Meant to be called once a
    day by an external free cron service (e.g. cron-job.org), not by the
    frontend. Protected by a shared secret, accepted either as a query
    param (?secret=...) for simple GET-only cron tools, or as an
    X-Cron-Secret header for tools that support custom headers.
    """
    provided = secret or x_cron_secret
    if not CRON_SECRET or provided != CRON_SECRET:
        raise HTTPException(status_code=401, detail="Invalid or missing cron secret")

    tomorrow = date.today() + timedelta(days=1)
    ...
    applications = (
        db.query(models.Application)
        .filter(models.Application.interview_date == tomorrow)
        .all()
    )

    sent = 0
    for app in applications:
        user = db.query(models.User).filter(models.User.id == app.user_id).first()
        job = db.query(models.Job).filter(models.Job.id == app.job_id).first()
        if not user or not job:
            continue
        ok = email_utils.send_email(
            to=user.email,
            subject=f"Reminder: interview tomorrow for {job.title}",
            html_body=email_utils.interview_reminder_html(
                name=user.name,
                job_title=job.title,
                company=job.company or "the company",
                interview_date=str(app.interview_date),
            ),
        )
        if ok:
            sent += 1

    return {"checked": len(applications), "emails_sent": sent}


@router.post("/saved-jobs-digest")
def email_saved_jobs_digest(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    """On-demand: email the current user a summary of their saved jobs."""
    jobs = (
        db.query(models.Job)
        .join(models.SavedJob, models.SavedJob.job_id == models.Job.id)
        .filter(models.SavedJob.user_id == current_user.id)
        .all()
    )
    if not jobs:
        raise HTTPException(status_code=400, detail="You haven't saved any jobs yet")

    job_dicts = [{"title": j.title, "company": j.company or "", "location": j.location or ""} for j in jobs]
    ok = email_utils.send_email(
        to=current_user.email,
        subject="Your saved jobs on CareerMate AI",
        html_body=email_utils.saved_jobs_digest_html(current_user.name, job_dicts),
    )
    if not ok:
        raise HTTPException(status_code=502, detail="Email service isn't configured or failed to send")

    return {"detail": f"Sent digest of {len(jobs)} saved jobs to {current_user.email}"}
