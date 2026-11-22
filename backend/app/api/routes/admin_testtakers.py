from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.security import hash_passcode, require_admin
from app.models.models import TestTaker
from app.schemas import TestTakerCreate

router = APIRouter(prefix="/api/admin", tags=["admin:testtakers"], dependencies=[Depends(require_admin)])


@router.get("/testtakers")
def list_testtakers(session: Session = Depends(get_session)):
    takers = session.exec(select(TestTaker)).all()
    return [{"id": t.id, "name": t.name} for t in takers]


@router.post("/testtakers")
def create_testtaker(body: TestTakerCreate, session: Session = Depends(get_session)):
    if session.exec(select(TestTaker).where(TestTaker.name == body.name)).first():
        raise HTTPException(status_code=409, detail="A test-taker with that name already exists")
    taker = TestTaker(name=body.name, passcode_hash=hash_passcode(body.passcode))
    session.add(taker)
    session.commit()
    session.refresh(taker)
    return {"id": taker.id, "name": taker.name}


@router.delete("/testtakers/{taker_id}")
def delete_testtaker(taker_id: int, session: Session = Depends(get_session)):
    taker = session.get(TestTaker, taker_id)
    if not taker:
        raise HTTPException(status_code=404, detail="Test-taker not found")
    session.delete(taker)
    session.commit()
    return {"ok": True}
