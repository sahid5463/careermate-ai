import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .database import Base, engine
from .routers import auth, users, resumes, jobs, applications, interview, dashboard, notifications

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CareerMate AI API", version="1.0.0")

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5500")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://127.0.0.1:5500", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(resumes.router)
app.include_router(jobs.router)
app.include_router(applications.router)
app.include_router(interview.router)
app.include_router(dashboard.router)
app.include_router(notifications.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "CareerMate AI API"}
