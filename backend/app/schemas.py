from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional, List


# ---------- Auth / Users ----------

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None


# ---------- Jobs ----------

class JobOut(BaseModel):
    id: int
    title: str
    company: Optional[str]
    location: Optional[str]
    salary: Optional[str]
    experience: Optional[str]
    description: Optional[str]
    apply_url: Optional[str]

    class Config:
        from_attributes = True


# ---------- Applications ----------

class ApplicationCreate(BaseModel):
    job_id: int


class ApplicationStatusUpdate(BaseModel):
    status: str
    interview_date: Optional[date] = None


class ApplicationOut(BaseModel):
    id: int
    job_id: int
    status: str
    applied_date: date
    interview_date: Optional[date]
    job: JobOut

    class Config:
        from_attributes = True


# ---------- Resume ----------

class ResumeOut(BaseModel):
    id: int
    file_url: str
    ats_score: Optional[int]
    analysis: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Interview ----------

class InterviewQuestionOut(BaseModel):
    id: int
    role: str
    question: str
    difficulty: str

    class Config:
        from_attributes = True


class InterviewAnswer(BaseModel):
    question_id: int
    answer: str


class InterviewSubmit(BaseModel):
    role: str
    answers: List[InterviewAnswer]


class InterviewResultOut(BaseModel):
    id: int
    role: str
    score: int
    feedback: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Dashboard ----------

class DashboardOut(BaseModel):
    resume_score: Optional[int] = None
    applications_count: int
    interviews_count: int
    saved_jobs_count: int
    latest_interview_score: Optional[int] = None
