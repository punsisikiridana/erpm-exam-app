from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session, select

from app.core.config import settings
from app.core.database import get_session
from app.core.security import (
    ADMIN_COOKIE,
    TESTTAKER_COOKIE,
    create_session_token,
    verify_passcode,
)
from app.models.models import TestTaker
from app.schemas import AdminLoginRequest, TestTakerLoginRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/admin/login")
def admin_login(body: AdminLoginRequest, response: Response):
    if not settings.admin_password_hash or not verify_passcode(body.password, settings.admin_password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    token = create_session_token(subject="admin", extra={})
    response.set_cookie(ADMIN_COOKIE, token, httponly=True, samesite="lax", max_age=12 * 3600)
    return {"ok": True}


@router.post("/admin/logout")
def admin_logout(response: Response):
    response.delete_cookie(ADMIN_COOKIE)
    return {"ok": True}


@router.post("/testtaker/login")
def testtaker_login(body: TestTakerLoginRequest, response: Response, session: Session = Depends(get_session)):
    taker = session.exec(select(TestTaker).where(TestTaker.name == body.name)).first()
    if not taker or not verify_passcode(body.passcode, taker.passcode_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid name or passcode")
    token = create_session_token(subject="testtaker", extra={"test_taker_id": taker.id})
    response.set_cookie(TESTTAKER_COOKIE, token, httponly=True, samesite="lax", max_age=12 * 3600)
    return {"ok": True, "test_taker_id": taker.id, "name": taker.name}


@router.post("/testtaker/logout")
def testtaker_logout(response: Response):
    response.delete_cookie(TESTTAKER_COOKIE)
    return {"ok": True}
