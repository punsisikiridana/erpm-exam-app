from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import Cookie, HTTPException, status
from jose import JWTError, jwt

from app.core.config import settings

ALGORITHM = "HS256"
ADMIN_COOKIE = "erpm_admin_session"
TESTTAKER_COOKIE = "erpm_testtaker_session"


def hash_passcode(raw: str) -> str:
    return bcrypt.hashpw(raw.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_passcode(raw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(raw.encode("utf-8")[:72], hashed.encode("utf-8"))
    except ValueError:
        return False


def create_session_token(subject: str, extra: dict, expires_hours: int = 12) -> str:
    payload = {"sub": subject, "exp": datetime.utcnow() + timedelta(hours=expires_hours), **extra}
    return jwt.encode(payload, settings.session_secret, algorithm=ALGORITHM)


def decode_session_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.session_secret, algorithms=[ALGORITHM])
    except JWTError:
        return None


def require_admin(erpm_admin_session: Optional[str] = Cookie(default=None, alias=ADMIN_COOKIE)) -> None:
    payload = decode_session_token(erpm_admin_session) if erpm_admin_session else None
    if not payload or payload.get("sub") != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin login required")


def get_current_test_taker_id(
    erpm_testtaker_session: Optional[str] = Cookie(default=None, alias=TESTTAKER_COOKIE),
) -> int:
    payload = decode_session_token(erpm_testtaker_session) if erpm_testtaker_session else None
    if not payload or "test_taker_id" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")
    return int(payload["test_taker_id"])
