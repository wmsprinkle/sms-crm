import json
from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.ingest.csv_import import import_csv

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("")
async def upload_csv(
    file: UploadFile = File(...),
    sequence_id: int = Form(...),
    mapping: str = Form(...),                 # JSON: {"phone":"Phone","first_name":"First"}
    source: str = Form("csv"),
    db: Session = Depends(get_db),
):
    result = import_csv(db, await file.read(), json.loads(mapping),
                        sequence_id, source)
    return result                             # {"imported","skipped","duplicates"}
