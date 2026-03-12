"""
Data contract (hard locked). Only these 6 fields allowed in API response.
No open_targets_score, evidence_strength, clinical_signal, validation_maturity, composite_score.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# Frontend: render only these columns; ignore any unexpected keys defensively.
API_RESPONSE_COLUMNS = ("sno", "biomarker", "type", "score", "source", "summary")


class BiomarkerResponse(BaseModel):
    """Strict 6-field API response. No additional fields permitted."""

    sno: int = Field(..., ge=0, description="Serial number")
    biomarker: str = Field(..., min_length=1, description="Biomarker name/symbol")
    type: str = Field(..., min_length=1, description="Biomarker type")
    score: int = Field(..., ge=0, le=3, description="Evidence score 0-3")
    source: str = Field(..., min_length=1, description="Contributing evidence label")
    summary: str = Field(..., min_length=1, description="1-2 line summary")

    model_config = {"extra": "forbid"}


class BiomarkerListResponse(BaseModel):
    """List of biomarker responses; each item is strictly 6-field."""

    items: list[BiomarkerResponse]
    total: int = Field(..., ge=0)

    model_config = {"extra": "forbid"}


class QueryRequest(BaseModel):
    """Request body for biomarker search by therapeutic area."""

    therapeutic_area: str = Field(..., min_length=1, description="Disease or therapeutic area")

    model_config = {"extra": "forbid"}
