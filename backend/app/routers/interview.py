import os
import re
import json
import urllib.request
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, security
from ..database import get_db

router = APIRouter(prefix="/api/interview", tags=["interview"])


@router.get("/questions", response_model=List[schemas.InterviewQuestionOut])
def get_questions(role: str, difficulty: str = "Easy", db: Session = Depends(get_db)):
    questions = (
        db.query(models.InterviewQuestion)
        .filter(models.InterviewQuestion.role == role, models.InterviewQuestion.difficulty == difficulty)
        .all()
    )
    if not questions:
        raise HTTPException(status_code=404, detail="No questions found for this role/difficulty yet")
    return questions


def keyword_overlap_score(answer: str, reference: str) -> int:
    """Fallback scoring: overlap of meaningful words between answer and reference answer."""
    def tokenize(t: str):
        return {w for w in re.findall(r"[a-z]+", t.lower()) if len(w) > 3}

    ref_words = tokenize(reference)
    ans_words = tokenize(answer)
    if not ref_words:
        return 50 if len(answer.split()) > 3 else 20
    overlap = len(ref_words & ans_words) / len(ref_words)
    length_bonus = min(len(answer.split()) / 30, 1) * 20
    return int(min(overlap * 80 + length_bonus, 100))


def anthropic_feedback(role: str, qa_pairs: list, api_key: str) -> dict:
    prompt = (
        f"You are a technical interviewer for a {role} position. Given these Q&A pairs, "
        "return ONLY a JSON object with keys: score (0-100 integer, overall), "
        "feedback (string, 3-5 sentences of constructive feedback). No markdown, no preamble.\n\n"
        + json.dumps(qa_pairs)
    )
    body = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 800,
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
    raw_text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    cleaned = re.sub(r"^```json|```$", "", raw_text.strip()).strip()
    return json.loads(cleaned)


@router.post("/submit", response_model=schemas.InterviewResultOut)
def submit_interview(
    payload: schemas.InterviewSubmit,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    qa_pairs = []
    scores = []
    for ans in payload.answers:
        question = db.query(models.InterviewQuestion).filter(
            models.InterviewQuestion.id == ans.question_id
        ).first()
        if not question:
            continue
        ref = question.answer or ""
        scores.append(keyword_overlap_score(ans.answer, ref))
        qa_pairs.append({"question": question.question, "answer": ans.answer})

    if not qa_pairs:
        raise HTTPException(status_code=400, detail="No valid questions in submission")

    fallback_score = int(sum(scores) / len(scores))
    fallback_feedback = (
        "Good attempt overall. Focus on giving concrete examples and being more specific "
        "with technical terms where relevant."
    )

    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    try:
        result = anthropic_feedback(payload.role, qa_pairs, api_key) if api_key else {
            "score": fallback_score, "feedback": fallback_feedback
        }
    except Exception:
        result = {"score": fallback_score, "feedback": fallback_feedback}

    interview_result = models.InterviewResult(
        user_id=current_user.id,
        role=payload.role,
        score=result.get("score", fallback_score),
        feedback=result.get("feedback", fallback_feedback),
    )
    db.add(interview_result)
    db.commit()
    db.refresh(interview_result)
    return interview_result


@router.get("/results", response_model=List[schemas.InterviewResultOut])
def list_results(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    return (
        db.query(models.InterviewResult)
        .filter(models.InterviewResult.user_id == current_user.id)
        .order_by(models.InterviewResult.created_at.desc())
        .all()
    )
