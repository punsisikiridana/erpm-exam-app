from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import (
    admin_attempts,
    admin_questions,
    admin_subjects,
    admin_templates,
    admin_testtakers,
    auth,
    exam,
)
from app.core.database import init_db

app = FastAPI(title="ERPM Practice Exam")

app.include_router(auth.router)
app.include_router(admin_subjects.router)
app.include_router(admin_questions.router)
app.include_router(admin_templates.router)
app.include_router(admin_testtakers.router)
app.include_router(admin_attempts.router)
app.include_router(exam.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/api/health")
def health():
    return {"ok": True}


_frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
