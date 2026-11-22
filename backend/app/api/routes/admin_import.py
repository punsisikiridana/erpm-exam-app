from fastapi import APIRouter, Depends, HTTPException

from app.core.security import require_admin
from app.importer.mcqmed_importer import import_topic
from app.schemas import McqmedImportRequest

router = APIRouter(prefix="/api/admin", tags=["admin:import"], dependencies=[Depends(require_admin)])


@router.post("/import/mcqmed")
def run_mcqmed_import(body: McqmedImportRequest):
    try:
        import_topic(body.local_topic_id, body.mcqmed_topic_id)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}
