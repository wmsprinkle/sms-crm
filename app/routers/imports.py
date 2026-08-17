import json
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.ingest.csv_import import import_csv
from app.security import sanitize_string

router = APIRouter(prefix="/imports", tags=["imports"])

# Security limits
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_CONTENT_TYPES = {"text/csv", "text/plain", "application/csv"}


@router.post("")
async def upload_csv(
    file: UploadFile = File(...),
    sequence_id: int = Form(...),
    mapping: str = Form(...),                 # JSON: {"phone":"Phone","first_name":"First"}
    source: str = Form("csv"),
    db: Session = Depends(get_db),
):
    """Import leads from CSV file.

    Security:
    - File size limited to 5MB
    - Content type validated
    - JSON mapping validated
    - All fields sanitized
    """
    # Validate file
    if not file.filename:
        raise HTTPException(400, "filename required")

    if not file.content_type or file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(400, f"invalid file type: {file.content_type}")

    # Read and validate file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(400, f"file too large (max {MAX_FILE_SIZE} bytes)")

    if len(contents) == 0:
        raise HTTPException(400, "file is empty")

    # Validate mapping JSON
    try:
        mapping_data = json.loads(mapping)
        if not isinstance(mapping_data, dict):
            raise ValueError()
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(400, "mapping must be valid JSON object")

    # Validate sequence_id
    if sequence_id <= 0:
        raise HTTPException(400, "sequence_id must be positive")

    # Sanitize source
    source = sanitize_string(source, 50)

    # Import CSV
    try:
        result = import_csv(db, contents, mapping_data, sequence_id, source)
        return result
    except Exception as e:
        raise HTTPException(400, f"import failed: {str(e)}")
