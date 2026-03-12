"""
Biomarker Intelligence API. Main only handles route logic.
Returns list of biomarker objects (strict 6-field schema). No extra columns.
"""

from __future__ import annotations

import re
from contextlib import asynccontextmanager

import requests
from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import models, schemas
from app.aggregator import build_biomarker_response

# ---------------------------------------------------------------------------
# Biomarker discovery (internal)
# ---------------------------------------------------------------------------
BIOMARKER_PATTERN = re.compile(r"\b([A-Z][A-Za-z0-9-]{2,10})\b")
ALLOWLIST = frozenset({
    "EGFR", "KRAS", "BRAF", "TP53", "PIK3CA", "PTEN", "HER2", "BRCA1", "BRCA2",
    "ALK", "ROS1", "MET", "RET", "NTRK1", "PD1", "PDL1", "CTLA4", "IL2", "IL6",
    "TNF", "VEGFA", "CD19", "CD20", "CD8", "CD4", "ER", "PR", "AR", "ESR1",
    "FGFR1", "FGFR2", "KIT", "JAK2", "MYC", "BCL2", "IDH1", "IDH2", "TMB", "MSI",
})


def _discover_biomarkers(therapeutic_area: str) -> list[tuple[str, str]]:
    """Return list of (biomarker_name, type)."""
    candidates: set[str] = set()
    try:
        r = requests.get(
            "https://clinicaltrials.gov/api/v2/studies",
            params={"query.cond": therapeutic_area, "pageSize": 100},
            timeout=10,
        )
        if r.ok:
            for study in r.json().get("studies", []) or []:
                arms = (study.get("protocolSection") or {}).get("armsInterventionsModule") or {}
                for iv in (arms.get("interventions") or []):
                    name = (iv.get("name") or "").strip()
                    for m in BIOMARKER_PATTERN.findall(name):
                        if m.upper() in ALLOWLIST:
                            candidates.add(m)
    except Exception:
        pass
    try:
        current_year = __import__("datetime").datetime.now().year
        r = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={
                "db": "pubmed",
                "term": f"{therapeutic_area} biomarker",
                "retmax": 30,
                "retmode": "json",
            },
            timeout=10,
        )
        if r.ok:
            ids = r.json().get("esearchresult", {}).get("idlist", [])[:10]
            if ids:
                r2 = requests.get(
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
                    params={"db": "pubmed", "id": ",".join(ids), "retmode": "text", "rettype": "abstract"},
                    timeout=10,
                )
                if r2.ok:
                    for m in BIOMARKER_PATTERN.findall(r2.text):
                        if m.upper() in ALLOWLIST:
                            candidates.add(m)
    except Exception:
        pass
    return [(c, "Gene") for c in sorted(candidates)]


# ---------------------------------------------------------------------------
# App & DB
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    models.init_db()
    yield


app = FastAPI(
    title="Biomarker Intelligence API",
    description="Strict 6-field response: sno, biomarker, type, score, source, summary.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = models.SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Endpoints — strict schema only
# ---------------------------------------------------------------------------
@app.get(
    "/api/v1/biomarkers",
    response_model=schemas.BiomarkerListResponse,
    response_model_exclude_none=True,
)
def list_biomarkers(
    therapeutic_area: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    """Return biomarkers. Only fields: sno, biomarker, type, score, source, summary."""
    discovered = _discover_biomarkers(therapeutic_area)
    if not discovered:
        return schemas.BiomarkerListResponse(items=[], total=0)

    results: list[schemas.BiomarkerResponse] = []
    for sno, (biomarker_name, biom_type) in enumerate(discovered, start=1):
        strict = build_biomarker_response(sno, biomarker_name, biom_type, therapeutic_area)
        results.append(schemas.BiomarkerResponse(**strict))
        rec = models.BiomarkerRecord(
            biomarker=strict["biomarker"],
            type=strict["type"],
            score=strict["score"],
            source=strict["source"],
            summary=strict["summary"],
            therapeutic_area=therapeutic_area,
        )
        db.add(rec)
    db.commit()
    return schemas.BiomarkerListResponse(items=results, total=len(results))


@app.get("/health")
def health():
    return {"status": "ok"}
