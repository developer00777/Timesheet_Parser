"""FastAPI app for batch processing timesheet .xls files."""

import os
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, Security, Depends
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader

from app.parser import parse_timesheet

app = FastAPI(
    title="Timesheet Parser API",
    description="Batch process Avvas monthly timesheet .xls files and return structured JSON summaries.",
    version="1.0.0",
)

UPLOAD_DIR = Path("/tmp/timesheets")

# API Key auth
API_KEY = os.environ.get("API_KEY", "changeme")
api_key_header = APIKeyHeader(name="X-API-Key")


async def verify_api_key(key: str = Security(api_key_header)) -> str:
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key.")
    return key


@app.post("/parse", summary="Parse one or more timesheet .xls files")
async def parse_timesheets(
    files: list[UploadFile] = File(...),
    _: str = Depends(verify_api_key),
):
    """
    Upload one or more .xls timesheet files (up to 100).
    Returns a JSON object keyed by Avvas-ID with summary data.
    """
    if len(files) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 files per request.")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    results = {}
    errors = []

    for upload_file in files:
        if not upload_file.filename.endswith((".xls",)):
            errors.append({"file": upload_file.filename, "error": "Only .xls files are supported."})
            continue

        tmp_path = UPLOAD_DIR / upload_file.filename
        try:
            with open(tmp_path, "wb") as f:
                content = await upload_file.read()
                f.write(content)

            parsed = parse_timesheet(str(tmp_path))
            avvas_id = parsed["avvas_id"] or upload_file.filename

            results[avvas_id] = parsed["summary"]
        except Exception as e:
            errors.append({"file": upload_file.filename, "error": str(e)})
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    return JSONResponse(content={"results": results, "errors": errors})


@app.get("/health")
async def health():
    return {"status": "ok"}
