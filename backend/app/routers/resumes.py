import os
import re
import json
import urllib.request
from typing import List

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from pypdf import PdfReader
import docx

from .. import models, schemas, security
from ..database import get_db

router = APIRouter(prefix="/api/resume", tags=["resume"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Master skill list used for keyword-based detection.
# Extend this list freely as your job data grows.
SKILL_BANK = [
    "python", "java", "c++", "c", "javascript", "typescript", "react", "node.js",
    "express", "fastapi", "django", "flask", "sql", "postgresql", "mysql", "mongodb",
    "git", "docker", "kubernetes", "aws", "azure", "gcp", "html", "css", "tailwind",
    "rest api", "graphql", "machine learning", "deep learning", "nlp", "pandas",
    "numpy", "tensorflow", "pytorch", "linux", "data structures", "algorithms",
    "oop", "dbms", "operating systems", "computer networks", "system design",
]

SECTION_KEYWORDS = {
    "education": ["education", "b.tech", "bachelor", "college", "university", "cgpa", "gpa"],
    "experience": ["experience", "internship", "worked at", "employment"],
    "projects": ["projects", "project"],
    "skills": ["skills", "technologies", "technical skills"],
    "summary": ["summary", "objective", "about me"],
    "contact": ["email", "phone", "linkedin", "github"],
}


def extract_text(file_path: str, filename: str) -> str:
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(file_path)
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    elif filename.lower().endswith(".docx"):
        d = docx.Document(file_path)
        return "\n".join(p.text for p in d.paragraphs)
    else:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")


def detect_skills(text: str) -> List[str]:
    lower = text.lower()
    return sorted({s for s in SKILL_BANK if s in lower})


def detect_sections(text: str) -> dict:
    lower = text.lower()
    return {
        section: any(kw in lower for kw in keywords)
        for section, keywords in SECTION_KEYWORDS.items()
    }


def rule_based_analysis(text: str) -> dict:
    """Fallback analysis with no external API required."""
    skills_found = detect_skills(text)
    sections = detect_sections(text)

    # Simple weighted ATS score
    score = 0
    score += min(len(skills_found), 10) * 4          # up to 40 pts for skill coverage
    score += 15 if sections["education"] else 0
    score += 15 if sections["experience"] or sections["projects"] else 0
    score += 10 if sections["skills"] else 0
    score += 10 if sections["summary"] else 0
    score += 10 if sections["contact"] else 0
    score = min(score, 100)

    missing = []
    if not sections["projects"]:
        missing.append("Add a Projects section with 2-3 concrete projects")
    if not sections["summary"]:
        missing.append("Add a short professional summary at the top")
    if len(skills_found) < 5:
        missing.append("List more relevant technical skills explicitly")
    if not sections["contact"]:
        missing.append("Make sure email/phone/LinkedIn/GitHub are clearly visible")

    return {
        "ats_score": score,
        "skills_detected": skills_found,
        "sections_detected": sections,
        "suggestions": missing or ["Resume looks solid — consider tailoring keywords per job description"],
    }


def anthropic_analysis(text: str, api_key: str) -> dict:
    """Optional: richer analysis using Claude, if an API key is configured."""
    prompt = (
        "You are an ATS resume reviewer. Given the resume text below, return ONLY a JSON object "
        "with keys: ats_score (0-100 integer), skills_detected (array of strings), "
        "suggestions (array of short actionable strings, max 5). "
        "No markdown, no preamble.\n\nResume text:\n" + text[:6000]
    )
    body = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 1000,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    raw_text = "".join(
        block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"
    )
    cleaned = re.sub(r"^```json|```$", "", raw_text.strip()).strip()
    return json.loads(cleaned)


@router.post("/upload", response_model=schemas.ResumeOut)
def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    dest_path = os.path.join(UPLOAD_DIR, f"user{current_user.id}_{file.filename}")
    with open(dest_path, "wb") as f:
        f.write(file.file.read())

    text = extract_text(dest_path, file.filename)
    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from this file")

    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    try:
        result = anthropic_analysis(text, api_key) if api_key else rule_based_analysis(text)
    except Exception:
        # Any API failure silently falls back to the rule-based path
        result = rule_based_analysis(text)

    resume = models.Resume(
        user_id=current_user.id,
        file_url=dest_path,
        ats_score=result.get("ats_score", 0),
        analysis=json.dumps(result),
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.get("/analysis", response_model=schemas.ResumeOut)
def latest_analysis(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    resume = (
        db.query(models.Resume)
        .filter(models.Resume.user_id == current_user.id)
        .order_by(models.Resume.created_at.desc())
        .first()
    )
    if not resume:
        raise HTTPException(status_code=404, detail="No resume uploaded yet")
    return resume
