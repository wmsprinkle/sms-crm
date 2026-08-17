from fastapi import APIRouter
from pydantic import BaseModel
from app.config import settings

router = APIRouter(prefix="/runtime", tags=["runtime"])


class AutoSend(BaseModel):
    enabled: bool


@router.get("")
def get_runtime():
    return {"auto_send": settings.auto_send, "dry_run": settings.dry_run}


@router.post("/auto-send")
def set_auto_send(body: AutoSend):
    settings.auto_send = body.enabled
    return {"ok": True, "auto_send": settings.auto_send, "dry_run": settings.dry_run}
