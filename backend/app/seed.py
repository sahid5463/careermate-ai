"""
Run this once after creating the tables to populate sample data:
    python -m app.seed
"""
from .database import SessionLocal, engine, Base
from . import models


SAMPLE_JOBS = [
    dict(title="Software Developer", company="TechNova Pvt Ltd", location="Bhopal",
         salary="4-6 LPA", experience="Fresher",
         description="Build and maintain web applications using Python and React. "
                     "Freshers with strong DSA fundamentals encouraged to apply.",
         apply_url="https://example.com/jobs/software-developer"),
    dict(title="Python Developer", company="CodeCraft Solutions", location="Remote",
         salary="5-7 LPA", experience="Fresher",
         description="Work on backend APIs using FastAPI/Django, integrate with PostgreSQL, "
                     "and collaborate with the frontend team.",
         apply_url="https://example.com/jobs/python-developer"),
    dict(title="Graduate Engineer Trainee", company="Infratech Industries", location="Indore",
         salary="3.5-5 LPA", experience="Fresher",
         description="One-year rotational training program across engineering teams for "
                     "recent B.Tech graduates.",
         apply_url="https://example.com/jobs/get-program"),
    dict(title="Frontend Developer (React)", company="PixelWorks", location="Remote",
         salary="6-9 LPA", experience="0-1 years",
         description="Build responsive UI with React and Tailwind CSS. Experience with "
                     "REST APIs and Git required.",
         apply_url="https://example.com/jobs/frontend-react"),
    dict(title="Data Analyst", company="InsightAI", location="Bhopal",
         salary="4-6 LPA", experience="Fresher",
         description="Analyze business data using SQL and Python (pandas). Build dashboards "
                     "and support data-driven decision making.",
         apply_url="https://example.com/jobs/data-analyst"),
]

SAMPLE_QUESTIONS = [
    # Software Developer - Easy
    dict(role="Software Developer", difficulty="Easy",
         question="What is Object-Oriented Programming (OOP)?",
         answer="OOP is a programming paradigm based on objects and classes, using concepts "
                "like encapsulation, inheritance, polymorphism and abstraction to structure code."),
    dict(role="Software Developer", difficulty="Easy",
         question="What is the difference between a list and a tuple in Python?",
         answer="Lists are mutable and defined with square brackets; tuples are immutable "
                "and defined with parentheses. Tuples are generally faster and used for fixed data."),
    dict(role="Software Developer", difficulty="Easy",
         question="What is a REST API?",
         answer="REST is an architectural style for APIs using HTTP methods like GET, POST, "
                "PUT, DELETE to perform operations on resources identified by URLs, usually "
                "exchanging data as JSON."),
    # Software Developer - Medium
    dict(role="Software Developer", difficulty="Medium",
         question="Explain the concept of database indexing and why it matters.",
         answer="An index is a data structure that improves the speed of data retrieval "
                "operations on a table at the cost of additional writes and storage. It works "
                "like a lookup table so the database doesn't scan every row."),
    dict(role="Software Developer", difficulty="Medium",
         question="What is the difference between SQL and NoSQL databases?",
         answer="SQL databases are relational, use structured schemas and tables with ACID "
                "guarantees, e.g. PostgreSQL. NoSQL databases are non-relational, schema-flexible, "
                "and optimized for scale or unstructured data, e.g. MongoDB."),
    # Python Developer - Easy
    dict(role="Python Developer", difficulty="Easy",
         question="What are Python decorators?",
         answer="A decorator is a function that wraps another function to extend or modify "
                "its behavior without changing its source code, commonly used with the @syntax."),
    dict(role="Python Developer", difficulty="Easy",
         question="What is the Global Interpreter Lock (GIL)?",
         answer="The GIL is a mutex in CPython that allows only one thread to execute Python "
                "bytecode at a time, which limits true parallelism in multi-threaded CPU-bound programs."),
    # HR-style questions (role-agnostic, tagged generically)
    dict(role="HR", difficulty="Easy",
         question="Tell me about yourself.",
         answer="A concise summary of your education, key skills, relevant projects/internships, "
                "and what you're looking for in this role."),
    dict(role="HR", difficulty="Easy",
         question="Why do you want to work with us?",
         answer="Show you've researched the company, connect their mission or work to your "
                "skills and career goals, and be specific rather than generic."),
    dict(role="HR", difficulty="Medium",
         question="Describe a time you faced a conflict in a team project and how you resolved it.",
         answer="Use the STAR method: Situation, Task, Action, Result. Focus on communication, "
                "compromise, and the positive outcome."),
]


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(models.Job).count() == 0:
            for j in SAMPLE_JOBS:
                db.add(models.Job(**j))
            print(f"Inserted {len(SAMPLE_JOBS)} sample jobs")
        else:
            print("Jobs table already has data, skipping")

        if db.query(models.InterviewQuestion).count() == 0:
            for q in SAMPLE_QUESTIONS:
                db.add(models.InterviewQuestion(**q))
            print(f"Inserted {len(SAMPLE_QUESTIONS)} sample interview questions")
        else:
            print("Interview questions already exist, skipping")

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    run()
