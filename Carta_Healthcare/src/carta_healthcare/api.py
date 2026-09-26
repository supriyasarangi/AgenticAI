from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .config import load_settings
from .extraction import extract_record
from .schema import ClinicalRecord

app = FastAPI(
    title="Carta Healthcare",
    description="Clinical data extraction and structuring from health records",
    version="0.1.0",
)


class ExtractRequest(BaseModel):
    note_text: str = Field(..., min_length=1, max_length=50000, description="Clinical note text")


class ExtractResponse(BaseModel):
    record: ClinicalRecord


@app.post("/extract", response_model=ExtractResponse)
def extract(req: ExtractRequest) -> ExtractResponse:
    """Extract structured clinical data from a note."""
    settings = load_settings()
    result = extract_record(req.note_text, source_file="api-request", settings=settings)

    if not result.success:
        raise HTTPException(status_code=502, detail=f"Extraction failed: {result.error}")

    return ExtractResponse(record=result.record)


@app.get("/health")
def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}
