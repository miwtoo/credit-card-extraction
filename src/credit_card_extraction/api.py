import os
import tempfile

from fastapi import FastAPI, File, HTTPException, UploadFile

from .extractor import parse_pdf
from .models import ExtractionResult

app = FastAPI(title="Credit Card Extraction", version="0.0.0")


@app.post("/parse", response_model=ExtractionResult)
async def parse_statement(file: UploadFile = File(...)) -> ExtractionResult:
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    filename = file.filename.lower()
    if not filename.endswith(".pdf") and file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported.")

    suffix = ".pdf" if not filename.endswith(".pdf") else ""
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            payload = await file.read()
            if not payload:
                raise HTTPException(status_code=400, detail="Uploaded file is empty.")
            tmp.write(payload)
            temp_path = tmp.name

        return parse_pdf(temp_path)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Failed to parse PDF.") from exc
    finally:
        if temp_path:
            try:
                os.remove(temp_path)
            except OSError:
                pass
