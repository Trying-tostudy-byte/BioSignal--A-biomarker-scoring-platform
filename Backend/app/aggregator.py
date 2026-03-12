"""
Aggregator: combines source signals, generates final source string and summary.
Uses data_sources (raw) and scoring_engine (score only). No extra fields exposed.
"""

from __future__ import annotations

from typing import Any

from app.data_sources import clinical_trials, pubmed
from app.data_sources.open_targets import fetch_opentargets_strength
from app.scoring_engine import OPEN_TARGETS_THRESHOLD, compute_score


def _normalize_signals(
    therapeutic_area: str,
    biomarker: str,
) -> dict[str, Any]:
    """Fetch raw data from all sources; return normalized signals dict (internal only)."""
    pub = pubmed.fetch_pubmed_signals(therapeutic_area, biomarker)
    clin = clinical_trials.fetch_clinical_signals(therapeutic_area, biomarker)
    ot = fetch_opentargets_strength(therapeutic_area, biomarker)
    return {
        "literature_count": int(pub.get("literature_count") or 0),
        "clinical_phase": int(clin.get("clinical_phase") or 0),
        "fda_approved": bool(clin.get("fda_approved", False)),
        "open_targets_strength": max(0.0, min(1.0, float(ot.get("open_targets_strength") or 0.0))),
    }


def _source_string(signals: dict) -> str:
    """
    Aggregate sources into single comma-separated string. No separate OpenTargets column.
    Rule: if pubmed_hits > 0 -> pubmed; if clinical_trials > 0 -> clinical_trials;
          if open_targets_assoc > threshold -> open_targets.
    """
    sources: list[str] = []
    if (int(signals.get("literature_count") or 0)) > 0:
        sources.append("pubmed")
    if (int(signals.get("clinical_phase") or 0)) >= 1:
        sources.append("clinical_trials")
    ot = float(signals.get("open_targets_strength") or 0.0)
    if ot >= OPEN_TARGETS_THRESHOLD:
        sources.append("open_targets")
    if not sources:
        return "no_evidence"
    return ", ".join(sources)


def _summary_text(biomarker: str, therapeutic_area: str, signals: dict, score: int) -> str:
    """Generate 1-2 line summary. No internal metrics in text."""
    area = therapeutic_area or "therapeutic area"
    clinical_phase = int(signals.get("clinical_phase") or 0)
    fda_approved = bool(signals.get("fda_approved", False))
    has_lit = (int(signals.get("literature_count") or 0)) > 0

    if score == 3:
        if fda_approved:
            return f"{biomarker} has FDA-approved indication in {area} with established evidence base."
        if clinical_phase >= 3:
            return f"{biomarker} is under Phase 3 or later investigation in {area} with strong validation."
        return f"{biomarker} is a clinically advancing biomarker in {area} with active targeted therapies."
    if score == 2:
        if clinical_phase >= 1:
            phase_label = "Phase 2" if clinical_phase >= 2 else "Phase 1"
            return f"{biomarker} is in active {phase_label} clinical investigation in {area}."
        return f"{biomarker} has strong multi-source support in {area}; clinical trials evolving."
    if score == 1:
        if has_lit:
            return f"{biomarker} has literature support in {area}; no active clinical trials."
        return f"{biomarker} has early database association in {area}; evidence evolving."
    return f"{biomarker} has limited validated evidence in {area}."


def build_biomarker_response(
    sno: int,
    biomarker: str,
    biom_type: str,
    therapeutic_area: str,
) -> dict[str, Any]:
    """
    Fetch signals, compute score, build source string and summary.
    Returns only: sno, biomarker, type, score, source, summary. Nothing else.
    """
    signals = _normalize_signals(therapeutic_area, biomarker)
    score = compute_score(signals)
    source = _source_string(signals)
    summary = _summary_text(biomarker, therapeutic_area, signals, score)
    return {
        "sno": sno,
        "biomarker": biomarker,
        "type": biom_type,
        "score": score,
        "source": source,
        "summary": summary,
    }
