"""
Single scoring engine. Receives normalized signals; returns integer score 0-3 only.
No decimals. No weighted scoring. No composite score. All scoring happens here only.

Score mapping:
  0 = No evidence
  1 = Literature-supported (PubMed only)
  2 = Clinical investigation (ClinicalTrials present)
  3 = Clinically advancing (Phase 2/3 trials OR strong multi-source support)
"""

from __future__ import annotations

# Internal thresholds only; never exposed
OPEN_TARGETS_THRESHOLD = 0.2  # >= this: count as open_targets in source aggregation
OPEN_TARGETS_STRONG = 0.5     # >= this: strong multi-source for score 3
CLINICAL_PHASE_1 = 1
CLINICAL_PHASE_2 = 2
CLINICAL_PHASE_3_OR_BEYOND = 3


def compute_score(signals: dict) -> int:
    """
    Deterministic mapping from normalized signals to integer 0-3.
    signals: literature_count (int), clinical_phase (int), open_targets_strength (float), fda_approved (bool).
    """
    literature_count = int(signals.get("literature_count") or 0)
    clinical_phase = int(signals.get("clinical_phase") or 0)
    ot = float(signals.get("open_targets_strength") or 0.0)
    ot = max(0.0, min(1.0, ot))
    fda_approved = bool(signals.get("fda_approved", False))

    pubmed_hits = literature_count > 0
    clinical_trials_present = clinical_phase >= CLINICAL_PHASE_1
    open_targets_assoc = ot >= OPEN_TARGETS_THRESHOLD
    strong_ot = ot >= OPEN_TARGETS_STRONG
    phase_2_or_3 = clinical_phase >= CLINICAL_PHASE_2

    # 0 = No evidence
    if not pubmed_hits and not clinical_trials_present and not open_targets_assoc:
        return 0

    # 3 = Clinically advancing (Phase 2/3 trials OR strong multi-source support)
    if fda_approved:
        return 3
    if clinical_phase >= CLINICAL_PHASE_3_OR_BEYOND:
        return 3
    if phase_2_or_3 and (strong_ot or pubmed_hits):
        return 3
    if clinical_trials_present and strong_ot and pubmed_hits:
        return 3

    # 2 = Clinical investigation (ClinicalTrials present)
    if clinical_trials_present:
        return 2
    if strong_ot and pubmed_hits:
        return 2

    # 1 = Literature-supported (PubMed only)
    if pubmed_hits:
        return 1
    if open_targets_assoc:
        return 1
    return 0
