import os
import json
import urllib.request

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
FROM_EMAIL = os.getenv("FROM_EMAIL", "CareerMate AI <onboarding@resend.dev>").strip()


def send_email(to: str, subject: str, html_body: str) -> bool:
    """
    Sends an email via Resend's API. Returns True on success, False if
    RESEND_API_KEY isn't configured or the send fails (never raises, so a
    failed email never breaks the calling request).
    """
    if not RESEND_API_KEY:
        return False

    body = json.dumps({
        "from": FROM_EMAIL,
        "to": [to],
        "subject": subject,
        "html": html_body,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {RESEND_API_KEY}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 300
    except Exception:
        return False


def welcome_email_html(name: str) -> str:
    return f"""
    <div style="font-family:sans-serif; max-width:480px; margin:auto;">
      <h2>Welcome to CareerMate AI, {name}! 👋</h2>
      <p>Your account is ready. Here's what to do first:</p>
      <ul>
        <li>Upload your resume to get an ATS score</li>
        <li>Browse live jobs from across the internet</li>
        <li>Practice with a mock interview</li>
      </ul>
      <p>Good luck with the job search!</p>
    </div>
    """


def interview_scheduled_html(name: str, job_title: str, company: str, interview_date: str) -> str:
    return f"""
    <div style="font-family:sans-serif; max-width:480px; margin:auto;">
      <h2>Interview scheduled 🎯</h2>
      <p>Hi {name}, your interview for <strong>{job_title}</strong> at
      <strong>{company}</strong> is set for <strong>{interview_date}</strong>.</p>
      <p>Head to the Interview Prep section in CareerMate AI to practice beforehand.</p>
    </div>
    """


def interview_reminder_html(name: str, job_title: str, company: str, interview_date: str) -> str:
    return f"""
    <div style="font-family:sans-serif; max-width:480px; margin:auto;">
      <h2>Reminder: interview tomorrow ⏰</h2>
      <p>Hi {name}, just a heads up — your interview for <strong>{job_title}</strong>
      at <strong>{company}</strong> is tomorrow ({interview_date}).</p>
      <p>Good luck!</p>
    </div>
    """


def saved_jobs_digest_html(name: str, jobs: list) -> str:
    rows = "".join(
        f"<li><strong>{j['title']}</strong> — {j['company']} ({j['location']})</li>"
        for j in jobs
    )
    return f"""
    <div style="font-family:sans-serif; max-width:480px; margin:auto;">
      <h2>Your saved jobs 📌</h2>
      <p>Hi {name}, here's a reminder of the jobs you've saved:</p>
      <ul>{rows}</ul>
    </div>
    """
