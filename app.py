import json
import re
import sys
import requests
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime


st.set_page_config(
    page_title="Biomarker Signal Intelligence",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="▸",
)

if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"

# Animated background layer (fixed, behind content) — gradient + biomarker particles
st.markdown(
    """
    <div id="bg-layer" class="bg-layer" aria-hidden="true">
        <div class="bg-gradient"></div>
        <div class="bg-particles">
            <span class="particle p1"></span><span class="particle p2"></span><span class="particle p3"></span>
            <span class="particle p4"></span><span class="particle p5"></span><span class="particle p6"></span>
            <span class="particle p7"></span><span class="particle p8"></span><span class="particle p9"></span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Theme-dependent CSS variables and full design system
_is_light = st.session_state.get("theme") == "light"
if _is_light:
    _vars = """
    :root {
        --bg-base: #f8fafc;
        --bg-mid: #f1f5f9;
        --bg-deep: #e2e8f0;
        --glass-bg: rgba(255,255,255,0.75);
        --glass-border: rgba(0,0,0,0.06);
        --glass-shadow: 0 20px 50px rgba(0,0,0,0.12);
        --text-primary: #0f172a;
        --text-secondary: #475569;
        --accent: #0d9488;
        --accent-dim: rgba(13,148,136,0.15);
        --accent-glow: rgba(13,148,136,0.25);
        --header-bg: rgba(248,250,252,0.88);
        --header-border: rgba(0,0,0,0.08);
        --neon-line: rgba(13,148,136,0.6);
        --table-hover: rgba(13,148,136,0.08);
        --signal-strong: #059669;
        --signal-amber: #d97706;
        --signal-weak: #dc2626;
    }
    """
else:
    _vars = """
    :root {
        --bg-base: #0a0e17;
        --bg-mid: #0f172a;
        --bg-deep: #020617;
        --glass-bg: rgba(15,23,42,0.72);
        --glass-border: rgba(255,255,255,0.06);
        --glass-shadow: 0 20px 50px rgba(0,0,0,0.45);
        --text-primary: #e6edf3;
        --text-secondary: #94a3b8;
        --accent: #3fb950;
        --accent-dim: rgba(63,185,80,0.15);
        --accent-glow: rgba(63,185,80,0.2);
        --header-bg: rgba(2,6,23,0.9);
        --header-border: rgba(148,163,184,0.12);
        --neon-line: rgba(56,189,248,0.5);
        --table-hover: rgba(35,134,54,0.1);
        --signal-strong: #22c55e;
        --signal-amber: #eab308;
        --signal-weak: #f87171;
        --tier-0: #ef4444;
        --tier-1: #eab308;
        --tier-2: #86efac;
        --tier-3: #22c55e;
    }
    """

_css = _vars + """
    @keyframes gradient-shift {
        0%%, 100% { opacity: 1; transform: scale(1) translate(0, 0); }
        50% { opacity: 0.95; transform: scale(1.02) translate(1%%, 0.5%%); }
    }
    @keyframes particle-drift {
        0%%, 100% { transform: translate(0, 0) scale(1); opacity: 0.04; }
        25% { transform: translate(2vw, -3vh) scale(1.1); opacity: 0.05; }
        50% { transform: translate(-1vw, 2vh) scale(0.95); opacity: 0.03; }
        75% { transform: translate(1.5vw, 1vh) scale(1.05); opacity: 0.045; }
    }
    @keyframes particle-pulse {
        0%%, 100% { box-shadow: 0 0 20px var(--accent-glow); }
        50% { box-shadow: 0 0 28px var(--accent-glow); }
    }
    @keyframes fade-in {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes progress-fill {
        from { width: 0%%; }
    }

    [data-testid="stAppViewContainer"] {
        background: transparent !important;
    }
    .block-container {
        padding: 0.5rem 1.5rem 2rem;
        max-width: 100%%;
        position: relative;
        z-index: 1;
        animation: fade-in 0.3s ease-out;
    }

    #bg-layer {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%%;
        height: 100%%;
        pointer-events: none;
        z-index: -1;
        overflow: hidden;
    }
    .bg-layer .bg-gradient {
        position: absolute;
        inset: 0;
        background: radial-gradient(ellipse 100%% 80%% at 50%% 0%%, #1e3a5f 0%%, #0f172a 40%%, #020617 100%%);
        animation: gradient-shift 20s ease-in-out infinite;
    }
    .bg-particles {
        position: absolute;
        inset: 0;
    }
    .bg-particles .particle {
        position: absolute;
        border-radius: 50%%;
        background: var(--accent);
        opacity: 0.04;
        animation: particle-drift 25s ease-in-out infinite, particle-pulse 8s ease-in-out infinite;
    }
    .bg-particles .p1 { width: 12px; height: 12px; left: 10%%; top: 20%%; animation-delay: 0s, 0s; }
    .bg-particles .p2 { width: 8px; height: 8px; left: 25%%; top: 60%%; animation-delay: -3s, -1s; }
    .bg-particles .p3 { width: 14px; height: 14px; left: 70%%; top: 30%%; animation-delay: -6s, -2s; }
    .bg-particles .p4 { width: 6px; height: 6px; left: 85%%; top: 70%%; animation-delay: -9s, -3s; }
    .bg-particles .p5 { width: 10px; height: 10px; left: 50%%; top: 45%%; animation-delay: -12s, -4s; }
    .bg-particles .p6 { width: 8px; height: 8px; left: 15%%; top: 80%%; animation-delay: -5s, -5s; }
    .bg-particles .p7 { width: 10px; height: 10px; left: 60%%; top: 15%%; animation-delay: -8s, -6s; }
    .bg-particles .p8 { width: 6px; height: 6px; left: 40%%; top: 75%%; animation-delay: -11s, -7s; }
    .bg-particles .p9 { width: 12px; height: 12px; left: 90%%; top: 50%%; animation-delay: -2s, -8s; }

    .glass-header {
        position: sticky;
        top: 0;
        z-index: 100;
        width: 100%%;
        padding: 0.75rem 0 0.9rem;
        background: var(--header-bg);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-bottom: 1px solid var(--header-border);
        margin-bottom: 0.5rem;
        border-radius: 0 0 16px 16px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.2);
    }
    .glass-header .header-brand {
        font-size: 1rem;
        font-weight: 600;
        letter-spacing: 0.02em;
        color: var(--text-primary);
    }
    .glass-header .header-tag {
        font-size: 0.8rem;
        color: var(--text-secondary);
        font-weight: 400;
        margin-top: 0.2rem;
    }
    .api-status {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        font-size: 0.8rem;
        color: var(--text-secondary);
    }
    .api-status .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%%;
        background: var(--signal-strong);
        box-shadow: 0 0 8px var(--signal-strong);
    }
    .api-status.disconnected .dot { background: var(--signal-weak); box-shadow: none; }
    .section-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
    }

    .glass-card {
        background: var(--glass-bg);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid var(--glass-border);
        border-radius: 16px;
        box-shadow: var(--glass-shadow);
        transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
    }
    .glass-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 24px 56px rgba(0,0,0,0.25);
        border-color: var(--accent-dim);
    }

    .terminal-search-wrap {
        width: 100%%;
        margin: 0.6rem 0 1rem;
        padding: 0.4rem 0;
        animation: fade-in 0.25s ease-out 0.05s both;
    }
    .terminal-search-wrap .stTextInput input {
        border-radius: 16px !important;
        border: 1px solid var(--glass-border) !important;
        background: var(--glass-bg) !important;
        color: var(--text-primary) !important;
        padding: 0.75rem 1rem !important;
        font-size: 1rem !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .terminal-search-wrap .stTextInput input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px var(--accent-dim) !important;
    }

    .kpi-row { display: flex; gap: 0.75rem; margin: 0.5rem 0 1rem; flex-wrap: wrap; }
    .kpi-card {
        flex: 1;
        min-width: 140px;
        border-radius: 16px;
        padding: 0.75rem 1rem;
        background: var(--glass-bg);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid var(--glass-border);
        box-shadow: var(--glass-shadow);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 24px 56px rgba(0,0,0,0.25);
    }
    .kpi-card .kpi-value {
        transition: text-shadow 0.25s ease;
    }
    .kpi-card:hover .kpi-value { text-shadow: 0 0 20px var(--accent-glow); }
    .kpi-label { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.15em; color: var(--text-secondary); }
    .kpi-value { font-size: 1.25rem; font-weight: 600; color: var(--text-primary); }
    .kpi-value.signal-strong { color: var(--signal-strong); }
    .kpi-value.signal-amber { color: var(--signal-amber); }
    .kpi-value.signal-weak { color: var(--signal-weak); }

    .leaderboard-panel {
        border-radius: 16px;
        padding: 0.75rem 1rem 1rem;
        background: var(--glass-bg);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid var(--glass-border);
        box-shadow: var(--glass-shadow);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        animation: fade-in 0.3s ease-out 0.1s both;
    }
    .leaderboard-panel:hover {
        box-shadow: 0 24px 56px rgba(0,0,0,0.2);
    }
    [data-testid="stDataFrame"] table {
        border-collapse: separate !important;
        border-spacing: 0 2px !important;
    }
    [data-testid="stDataFrame"] table thead tr th {
        background: var(--glass-bg) !important;
        color: var(--text-secondary) !important;
        border-bottom: 1px solid var(--glass-border) !important;
        font-size: 0.7rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
    }
    [data-testid="stDataFrame"] table tbody tr td {
        padding: 0.5rem 0.75rem !important;
        border: none !important;
        transition: background 0.2s ease;
    }
    [data-testid="stDataFrame"] table tbody tr td:first-child,
    [data-testid="stDataFrame"] table thead tr th:first-child {
        text-align: left !important;
        padding-left: 0.5rem !important;
        max-width: 70px !important;
    }
    [data-testid="stDataFrame"] table tbody tr:hover {
        background: var(--table-hover) !important;
    }
    .tier-badge {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .tier-badge-0 { background: rgba(239,68,68,0.2); color: #fca5a5; }
    .tier-badge-1 { background: rgba(234,179,8,0.2); color: #fde047; }
    .tier-badge-2 { background: rgba(134,239,172,0.2); color: #86efac; }
    .tier-badge-3 { background: rgba(34,197,94,0.2); color: #22c55e; }

    .stDownloadButton button {
        border-radius: 12px !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    }
    .stDownloadButton button:active {
        transform: scale(0.98);
    }
    .stDownloadButton button:hover {
        box-shadow: 0 4px 14px var(--accent-dim);
    }

    [data-testid="stSidebar"] {
        background: var(--header-bg) !important;
        backdrop-filter: blur(16px);
        border-left: 1px solid var(--glass-border) !important;
        transition: transform 0.3s ease, opacity 0.3s ease;
    }
    [data-testid="stSidebar"] .stMarkdown { color: var(--text-primary); }
    [data-testid="stSidebar"] .stCaption { color: var(--text-secondary); }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        animation: fade-in 0.25s ease-out;
    }

    .stProgress > div > div { transition: width 0.5s ease-out; }
    .stProgress > div > div { animation: progress-fill 0.5s ease-out; }

    div[data-baseweb="select"] { border-radius: 12px; transition: border-color 0.2s ease, box-shadow 0.2s ease; }
    div[data-baseweb="slider"] { transition: opacity 0.2s ease; }
    .stMultiSelect div { border-radius: 12px; transition: border-color 0.2s ease; }
"""
st.markdown(f"<style>{_css}</style>", unsafe_allow_html=True)

# Top header bar: left brand, right API status + Export (placeholder) + Dark/Light
last_meta = st.session_state.get("last_meta", {})
api_ok = last_meta.get("api_ok", True)
header_col1, header_col2 = st.columns([4, 1])
with header_col1:
    st.markdown(
        """
        <div class="glass-header">
            <div class="header-brand">🧬 BioSignal Intelligence</div>
            <div class="header-tag">Emerging Biomarker Qualification Engine</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with header_col2:
    st.markdown(
        f'<div class="api-status{" disconnected" if not api_ok else ""}"><span class="dot"></span> API: {"Connected" if api_ok else "Error"}</div>',
        unsafe_allow_html=True,
    )
    open_targets_ok = last_meta.get("open_targets_ok", True)
    st.markdown(
        f'<div class="api-status{" disconnected" if not open_targets_ok else ""}" style="margin-top: 4px;"><span class="dot"></span> Open Targets: {"Connected" if open_targets_ok else "Unavailable"}</div>',
        unsafe_allow_html=True,
    )
    theme_light = st.toggle("Light", value=_is_light, key="theme_toggle", label_visibility="collapsed")
    if theme_light != _is_light:
        st.session_state["theme"] = "light" if theme_light else "dark"
        st.rerun()


BIOMARKER_PATTERN = re.compile(r"\b([A-Z][A-Za-z0-9-]{2,})\b")

# Generic uppercase / abstract terms — DO NOT extract as biomarkers
GENERIC_UPPERCASE_BLOCKLIST = {
    "CONTENT", "CRITICAL", "INDEX", "RESULT", "RESULTS", "METHOD", "METHODS",
    "BACKGROUND", "OBJECTIVE", "CONCLUSION", "STUDY", "DATA", "PATIENT", "CLINICAL",
    "GROUP", "ANALYSIS", "OUTCOME", "ENDPOINT", "PRIMARY", "SECONDARY", "DESIGN",
    "SAMPLE", "POPULATION", "COHORT", "RANDOMIZED", "CONTROL", "PLACEBO", "ARM",
    "PHASE", "TRIAL", "STATISTICAL", "SIGNIFICANT", "VALUE", "INTERVAL", "RATIO",
}

# Curated reference: HGNC-style gene symbols, protein/immune markers (validated molecular biomarkers only).
# Terms not in this set are DISCARDED. Extend from HGNC, UniProt, FDA/OncoKB/ClinVar as needed.
REFERENCE_BIOMARKERS = frozenset({
    # Cancer / oncogenes / TSGs
    "EGFR", "KRAS", "NRAS", "BRAF", "TP53", "PIK3CA", "PTEN", "HER2", "ERBB2",
    "BRCA1", "BRCA2", "ALK", "ROS1", "MET", "RET", "NTRK1", "NTRK2", "NTRK3",
    "IDH1", "IDH2", "FGFR1", "FGFR2", "FGFR3", "KIT", "PDGFRA", "JAK2", "JAK3",
    "MYC", "BCL2", "CDKN2A", "AR", "ESR1", "PGR", "TMPRSS2", "ETV1", "EWSR1",
    "MLH1", "MSH2", "MSH6", "PMS2", "APC", "SMAD4", "CDH1", "RB1", "NF1", "VHL",
    "STK11", "ATM", "CHEK2", "PALB2", "MAP2K1", "MAP2K2", "AKT1", "GNAQ", "GNA11",
    "SMO", "NOTCH1", "MYD88", "CARD11", "FBXW7", "KEAP1", "SETD2", "BAP1",
    "CD8", "CD4", "CD19", "CD20", "CD22", "CD30", "CD33", "CD38", "CD52",
    "PD1", "PDL1", "PD-L1", "CTLA4", "LAG3", "TIGIT", "TIM3", "VISTA",
    "IL2", "IL6", "IL10", "TNF", "IFNG", "TGFB1", "VEGFA", "CEA", "PSA",
    "TMB", "MSI", "MMR", "DMMR", "MSIH",
    # Immune / cytokine
    "IL6", "IL8", "IL1B", "CXCL9", "CXCL10", "CCL2", "CD274", "PDCD1", "HAVCR2",
    # Common proteins / markers
    "ER", "PR", "KI67", "MKI67", "HER2", "NPM1", "FLT3", "DNMT3A", "TET2",
    "RUNX1", "ASXL1", "SRSF2", "SF3B1", "U2AF1", "ZRSR2", "BCOR", "BCORL1",
    "EZH2", "KMT2D", "KMT2A", "CREBBP", "EP300", "NOTCH1", "NOTCH2",
    "MYCN", "MDM2", "CDK4", "CDK6", "CCND1", "MTOR", "RICTOR",
})
REFERENCE_BIOMARKERS_NORMALIZED = frozenset(
    re.sub(r"[-\s]", "", s).upper() for s in REFERENCE_BIOMARKERS
)

# Hard exclusion: diseases, methods, endpoints, study types, technologies, datasets, generic words, units, Roman numerals
TOKEN_BLACKLIST = {
    "RESULT", "RESULTS", "METHOD", "METHODS", "BACKGROUND", "OBJECTIVE", "CONCLUSION",
    "STUDY", "DATA", "PATIENT", "CLINICAL", "GROUP", "ANALYSIS", "OUR", "HERE", "THESE",
    "THIS", "THAT", "SCORE", "COMA", "WITH", "FROM", "USED", "SHOWED", "FOUND",
    "NSCLC", "LUAD", "AUC", "ROC", "KAPLAN", "MEIER", "PCR", "NGS", "TCGA", "GEO",
    "OS", "PFS", "DFS", "RFS", "HR", "OR", "RR", "CI", "P", "PVALUE",
    "PURPOSE", "ANALYSIS", "OBJECTIVE", "RANDOMIZED", "COHORT", "OBSERVATIONAL",
    "I", "II", "III", "IV", "V",
    "MG", "ML", "MMHG", "MMOL", "GDL", "NG",
}

COMMON_ENGLISH_WORDS = {
    "the", "and", "with", "for", "from", "this", "that", "into", "using",
    "study", "trial", "phase", "cancer", "disease", "patients", "placebo",
    "control", "group", "data", "result", "results", "method", "methods",
    "background", "objective", "conclusion", "clinical", "analysis", "marker",
    "markers", "signature", "predictor", "diagnostic", "purpose", "survival",
    "randomized", "cohort", "observational",
}

BIOMARKER_TERMS = ("biomarker", "marker", "signature", "predictor", "diagnostic")
NOVEL_TERMS = ("novel", "candidate", "emerging", "exploratory", "potential", "early")

# Additional scientific non-biomarker terms to exclude
SCIENTIFIC_NON_BIOMARKER = {
    "P",
    "PVALUE",
    "SD",
    "SE",
    "CI",
    "HR",
    "OR",
    "RR",
    "ANOVA",
    "LOGISTIC",
    "REGRESSION",
    "COHORT",
    "RANDOMIZED",
    "RANDOMISED",
    "MULTIVARIATE",
    "UNIVARIATE",
    "SENSITIVITY",
    "SPECIFICITY",
    "ROC",
    "AUC",
    "MMHG",
    "KG",
    "MG",
    "ML",
    "MM",
    # Auto-reject: diseases, methods, datasets, technologies
    "NSCLC",
    "LUAD",
    "KAPLAN",
    "MEIER",
    "PCR",
    "NGS",
    "TCGA",
    "GEO",
}

# Display-layer + validator: exclude non-biomarker entities
DISPLAY_EXCLUDE_NON_BIOMARKERS = {
    "nsclc", "luad", "copd", "diabetes", "cancer", "carcinoma", "tumor", "alzheimer",
    "pcr", "ngs", "sequencing", "immunoassay", "elisa", "western", "flow",
    "kaplan", "meier", "cox", "regression", "anova", "logrank",
    "rnaseq", "microarray", "spectrometry", "imaging",
    "tcga", "geo", "gtex", "cbioportal",
    "auc", "roc", "os", "pfs", "dfs", "rfs", "survival",
    "pathway", "signaling", "cascade",
    "phase", "placebo", "control", "cohort", "arm", "trial", "randomized", "observational",
    "dna", "rna", "protein", "mrna", "mirna",
    "purpose", "analysis", "objective",
}

# Gene / protein / mutation–like token pattern
# Captures: gene symbols, proteins, mutations, miRNAs, cytokines, cell markers
GENE_LIKE_PATTERN = re.compile(
    r"""^(
        [A-Z0-9]{2,10}         # short all-caps gene/protein symbol, e.g. TP53, BRCA1, PD-L1, CD19
        |
        [A-Z][A-Za-z0-9]{1,8}  # capitalized with letters/digits, e.g. PD1, Akt1, HER2
        |
        [A-Z0-9]+-[A-Z0-9]+    # hyphenated forms, e.g. BRAF-V600E, HLA-DR, IL-6
        |
        miR[-]?\d+[a-zA-Z0-9]* # miRNA patterns, e.g. miR-21, miR21a
        |
        [A-Z]+[-]?[A-Z0-9]+    # cytokine/protein patterns, e.g. TNF-α, VEGF-A
    )$""",
    re.VERBOSE,
)

# Mutation: GENE + space + variant only (e.g. KRAS G12C). Isolated variant (G12C, V600E) is invalid.
MUTATION_PATTERN = re.compile(r"\b([A-Z0-9]+)\s+([A-Z][0-9]+[A-Z])\b")
VARIANT_ONLY_PATTERN = re.compile(r"^[A-Z][0-9]+[A-Z]$")  # reject token that is only variant

# Units and Roman numerals (reject)
UNITS = {"mg", "ml", "mmol", "mmhg", "gdl", "ng", "pg", "ul", "nm", "um"}


def _biomarker_type(name: str) -> str:
    """Classify into Gene | Protein | Mutation | Metabolite | Cytokine | Epigenetic | Transcript."""
    if not name or not name.strip():
        return "Gene"
    s = name.strip()
    if MUTATION_PATTERN.search(s):
        return "Mutation"
    if re.search(r"miR[-]?\d+|lncRNA|circRNA", s, re.IGNORECASE):
        return "Transcript"
    # Cytokine: IL-6, TNF, IL-10, IFN-gamma, etc.
    if re.match(r"^IL[-]?\d+$", s, re.IGNORECASE) or re.match(r"^TNF|^IFN|^TGF|^CSF|^MCP|^CCL|^CXCL", s, re.IGNORECASE):
        return "Cytokine"
    # Epigenetic: methylation-related, histone marks (e.g. gene names used as epigenetic markers)
    if re.search(r"methylation|Methyl|DNMT|TET|HDAC|HAT|KMT|KDM", s) or re.match(r"^H[0-9]K[0-9]+", s):
        return "Epigenetic"
    metabolite_set = {"glucose", "lactate", "creatinine", "bilirubin", "hemoglobin", "cholesterol", "ldl", "hdl"}
    if re.match(r"^[a-z][a-z0-9-]*$", s) and len(s) <= 14 and s.lower() in metabolite_set:
        return "Metabolite"
    if re.match(r"^[A-Z][a-z]+$", s) and len(s) >= 5 and s.lower() in metabolite_set:
        return "Metabolite"
    if re.search(r"^[A-Z]{2,}-[A-Z0-9]+|^[A-Z]{2,}\d+[-]?[A-Z0-9]*$", s) or re.search(r"^(PD-?L1|HER2|IL-?\d+|TNF|VEGF|CD\d+)$", s, re.IGNORECASE):
        return "Protein"
    return "Gene"


def _normalize_name(name: str) -> str:
    normalized = re.sub(r"[-\s]", "", name).lower()
    return normalized


def _is_valid_biomarker(token: str) -> bool:
    """
    Extract and validate ONLY true molecular biomarkers (gene symbols, proteins, mutations, immune markers).
    Every term MUST be in the curated reference list (HGNC/UniProt/FDA/OncoKB style); otherwise DISCARD.
    Rejects: generic uppercase words, clinical endpoints, study design terms, disease names, adjectives.
    """
    if not token or len(token) < 2:
        return False
    token_upper = token.upper()
    token_lower = token.lower()
    norm = _normalize_name(token)

    # Generic uppercase / abstract terms — do not extract
    if token_upper in GENERIC_UPPERCASE_BLOCKLIST:
        return False
    # Isolated mutation fragment (G12C, V600E without gene) → invalid
    if VARIANT_ONLY_PATTERN.match(token_upper):
        return False
    if token_upper in TOKEN_BLACKLIST or token_upper in SCIENTIFIC_NON_BIOMARKER:
        return False
    if norm in DISPLAY_EXCLUDE_NON_BIOMARKERS:
        return False
    if token_lower in COMMON_ENGLISH_WORDS:
        return False
    if token_lower in UNITS:
        return False
    generic_molecules = {"dna", "rna", "mrna", "mirna", "protein", "peptide", "amino", "acid"}
    if token_lower in generic_molecules:
        return False
    disease_patterns = re.compile(r"^(NSCLC|LUAD|COPD|ALS|MS|AD|PD)$", re.IGNORECASE)
    if disease_patterns.match(token):
        return False
    method_patterns = re.compile(r"^(PCR|NGS|ELISA|IHC|FISH|FACS|RT-PCR|qPCR)$", re.IGNORECASE)
    if method_patterns.match(token):
        return False
    dataset_patterns = re.compile(r"^(TCGA|GEO|GTEX|SRA|ENA)$", re.IGNORECASE)
    if dataset_patterns.match(token):
        return False
    if "kaplan" in token_lower or "meier" in token_lower or "cox" in token_lower:
        return False
    study_terms = {"phase", "placebo", "control", "cohort", "arm", "trial", "randomized", "observational"}
    if token_lower in study_terms:
        return False
    if not GENE_LIKE_PATTERN.match(token_upper):
        return False
    has_number = any(ch.isdigit() for ch in token)
    has_hyphen = "-" in token
    is_short_upper = len(token) <= 10 and token.isupper()
    is_mirna = re.match(r"miR[-]?\d+", token, re.IGNORECASE)
    if not (has_number or has_hyphen or is_short_upper or is_mirna):
        return False
    # Must be in curated reference list (HGNC / UniProt / FDA / OncoKB style); otherwise DISCARD
    token_ref_key = re.sub(r"[-\s]", "", token).upper()
    if token_ref_key not in REFERENCE_BIOMARKERS_NORMALIZED:
        return False
    return True


def _is_valid_mutation(gene_part: str, variant_part: str) -> bool:
    """Mutation validation: GENE + space + variant. Gene part must be valid biomarker; variant [A-Z][0-9]+[A-Z]."""
    if not gene_part or not variant_part:
        return False
    if not re.match(r"^[A-Z][0-9]+[A-Z]$", variant_part.upper()):
        return False
    return _is_valid_biomarker(gene_part)


def validate_biomarker_candidates(candidates: list[str]) -> list[dict]:
    """
    Biomedical entity validator: from candidate terms return ONLY true biological biomarkers.
    Output format: [ {"biomarker": "", "type": "Gene|Protein|Mutation|Metabolite|Cytokine|Epigenetic|Transcript"} ]
    """
    out: list[dict] = []
    seen_norm: set[str] = set()
    for raw in candidates:
        if not raw or not isinstance(raw, str):
            continue
        token = raw.strip()
        if not token:
            continue
        norm = _normalize_name(token)
        if norm in seen_norm:
            continue
        mut_match = MUTATION_PATTERN.search(token)
        if mut_match:
            gene_part, variant_part = mut_match.group(1), mut_match.group(2)
            if _is_valid_mutation(gene_part, variant_part):
                name = f"{gene_part} {variant_part}"
                norm_mut = _normalize_name(name)
                if norm_mut not in seen_norm:
                    seen_norm.add(norm_mut)
                    out.append({"biomarker": name, "type": "Mutation"})
            continue
        if _is_valid_biomarker(token):
            seen_norm.add(norm)
            t = _biomarker_type(token)
            out.append({"biomarker": token, "type": t})
    return out


def validate_biomarker_candidates_to_json(candidates: list[str]) -> str:
    """Return strict JSON array only: [ {"biomarker": "", "type": "..."} ] or []."""
    return json.dumps(validate_biomarker_candidates(candidates))


def _extract_biomarkers(text: str) -> set[str]:
    """
    Pipeline: Raw Extraction → Entity Classification → Hard Rejection → Mutation Validation.
    Returns only true measurable biological biomarkers (genes, proteins, mutations, etc.).
    """
    if not text:
        return set()

    # Remove section headings to avoid picking them up as entities
    text = re.sub(
        r"\b(BACKGROUND|METHODS?|RESULTS?|CONCLUSION|OBJECTIVE)\b[:\s]*",
        " ",
        text,
        flags=re.IGNORECASE,
    )

    candidates: set[str] = set()

    # Raw extraction: single-token entities
    for match in BIOMARKER_PATTERN.findall(text):
        token = match.strip()
        # Entity classification + hard rejection filter
        if not _is_valid_biomarker(token):
            continue
        candidates.add(token)

    # Mutation validation: GENE + space + variant (e.g. KRAS G12C)
    for m in MUTATION_PATTERN.finditer(text):
        gene_part, variant_part = m.group(1), m.group(2)
        if _is_valid_mutation(gene_part, variant_part):
            candidates.add(f"{gene_part} {variant_part}")

    return candidates


# Open Targets Platform API (gene–disease association score)
OPEN_TARGETS_URL = "https://api.platform.opentargets.org/api/v4/graphql"
OPEN_TARGETS_TIMEOUT = 10


@st.cache_data(ttl=3600)
def _open_targets_request(query: str, variables: dict | None = None) -> dict | None:
    """Perform a single GraphQL request. Returns JSON data or None on failure."""
    try:
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        r = requests.post(OPEN_TARGETS_URL, json=payload, timeout=OPEN_TARGETS_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        if data.get("errors"):
            return None
        return data.get("data")
    except Exception:
        return None


def check_open_targets_health() -> bool:
    """Return True if Open Targets API is reachable (simple target query)."""
    q = """
    query Health {
        target(ensemblId: "ENSG00000146648") {
            id
            approvedSymbol
        }
    }
    """
    data = _open_targets_request(q)
    return data is not None and data.get("target") is not None


@st.cache_data(ttl=3600)
def fetch_open_targets_score(gene: str, disease: str) -> tuple[float, int]:
    """
    Fetch gene–disease association score from Open Targets Platform.
    Returns (overallScore 0–1, evidenceCount). On no result or error returns (0.0, 0).
    """
    if not gene or not disease:
        return 0.0, 0
    gene = gene.strip().upper()
    disease = disease.strip()
    # 1) Resolve disease name to EFO id via search
    search_disease = """
    query SearchDisease($q: String!) {
        search(query: $q, entityNames: [$q]) {
            hits {
                entityId
                entityType
                name
            }
        }
    }
    """
    data = _open_targets_request(search_disease, {"q": disease})
    efo_id = None
    if data and data.get("search") and data["search"].get("hits"):
        for h in data["search"]["hits"]:
            if (h.get("entityType") or "").lower() == "disease":
                efo_id = h.get("entityId")
                break
    if not efo_id:
        return 0.0, 0
    # 2) Resolve gene symbol to Ensembl id via search
    search_target = """
    query SearchTarget($q: String!) {
        search(query: $q, entityNames: [$q]) {
            hits {
                entityId
                entityType
                name
            }
        }
    }
    """
    data = _open_targets_request(search_target, {"q": gene})
    ensembl_id = None
    if data and data.get("search") and data["search"].get("hits"):
        for h in data["search"]["hits"]:
            if (h.get("entityType") or "").lower() == "target":
                eid = h.get("entityId")
                if eid and (eid.startswith("ENSG") or "ENSG" in str(eid)):
                    ensembl_id = eid
                    break
        if not ensembl_id and data["search"].get("hits"):
            first = data["search"]["hits"][0]
            if (first.get("entityType") or "").lower() == "target":
                ensembl_id = first.get("entityId")
    if not ensembl_id:
        return 0.0, 0
    # 3) Get association score: disease.associatedTargets filtered by target
    assoc_query = """
    query Assoc($efoId: String!, $ensemblIds: [String!]!) {
        disease(efoId: $efoId) {
            associatedTargets(page: { size: 5, index: 0 }, Bs: $ensemblIds) {
                rows {
                    score
                    target { id }
                }
            }
        }
    }
    """
    data = _open_targets_request(assoc_query, {"efoId": efo_id, "ensemblIds": [ensembl_id]})
    if not data or not data.get("disease"):
        return 0.0, 0
    at = data["disease"].get("associatedTargets") or {}
    rows = at.get("rows") or []
    for row in rows:
        t = row.get("target") or {}
        if t.get("id") == ensembl_id:
            score = float(row.get("score") or 0)
            score = max(0.0, min(1.0, score))
            evidence_count = 0
            return (score, evidence_count)
    return 0.0, 0


def _fetch_clinical_trials(query: str) -> list[dict]:
    """
    Fetch trials from ClinicalTrials.gov v2 API using the condition term only.
    Phase filtering is intentionally disabled for debugging.
    """
    url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        "query.cond": query,
        "pageSize": 200,
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return []

    studies = data.get("studies", []) or []
    try:
        print(
            f"[ClinicalTrials] Retrieved {len(studies)} studies for condition '{query}'",
            file=sys.stderr,
        )
    except Exception:
        pass

    results: list[dict] = []
    for study in studies:
        protocol = study.get("protocolSection", {}) or {}

        design = protocol.get("designModule", {}) or {}
        phases = design.get("phases") or []
        phase_simple = "I"
        if phases:
            phase_text = str(phases[0]).upper()
            if "PHASE3" in phase_text or "PHASE 3" in phase_text or "PHASE III" in phase_text:
                phase_simple = "III"
            elif "PHASE2" in phase_text or "PHASE 2" in phase_text or "PHASE II" in phase_text:
                phase_simple = "II"
            elif "PHASE1" in phase_text or "PHASE 1" in phase_text or "PHASE I" in phase_text:
                phase_simple = "I"

        description = protocol.get("descriptionModule", {}) or {}
        brief = description.get("briefSummary") or ""
        detailed = description.get("detailedDescription") or ""

        eligibility = protocol.get("eligibilityModule", {}) or {}
        eligibility_criteria = eligibility.get("eligibilityCriteria") or ""

        arms_module = protocol.get("armsInterventionsModule", {}) or {}
        interventions = arms_module.get("interventions", []) or []
        arm_groups = arms_module.get("armGroups", []) or []

        intervention_names = [iv.get("name", "") for iv in interventions if iv.get("name")]
        arm_descriptions = [ag.get("description", "") for ag in arm_groups if ag.get("description")]

        outcomes_module = protocol.get("outcomesModule", {}) or {}
        primary = outcomes_module.get("primaryOutcomes", []) or []
        secondary = outcomes_module.get("secondaryOutcomes", []) or []

        outcome_texts: list[str] = []
        for outcome in primary + secondary:
            measure = outcome.get("measure")
            description_text = outcome.get("description")
            if measure:
                outcome_texts.append(measure)
            if description_text:
                outcome_texts.append(description_text)

        combined_parts = (
            [s for s in intervention_names if s]
            + [s for s in arm_descriptions if s]
            + ([eligibility_criteria] if eligibility_criteria else [])
            + [s for s in outcome_texts if s]
            + ([brief] if brief else [])
            + ([detailed] if detailed else [])
        )
        combined_text = " ".join(combined_parts).strip()
        if not combined_text:
            continue

        results.append({"intervention": combined_text, "phase": phase_simple})

    return results


def _fetch_pubmed_abstracts(query: str) -> list[str]:
    current_year = datetime.now().year
    min_year = current_year - 5

    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    esearch_params = {
        "db": "pubmed",
        "term": f"{query} biomarker",
        "retmax": 50,
        "retmode": "json",
        "mindate": f"{min_year}/01/01",
        "maxdate": f"{current_year}/12/31",
    }
    try:
        search_resp = requests.get(f"{base_url}esearch.fcgi", params=esearch_params, timeout=5)
        search_resp.raise_for_status()
        search_data = search_resp.json()
        ids = search_data.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []
    except Exception:
        return []

    efetch_params = {
        "db": "pubmed",
        "id": ",".join(ids),
        "retmode": "text",
        "rettype": "abstract",
    }
    try:
        fetch_resp = requests.get(f"{base_url}efetch.fcgi", params=efetch_params, timeout=10)
        fetch_resp.raise_for_status()
        text = fetch_resp.text
    except Exception:
        return []

    raw_chunks = [chunk.strip() for chunk in text.split("\n\n") if chunk.strip()]
    filtered_abstracts: list[str] = []
    for chunk in raw_chunks:
        lower_chunk = chunk.lower()
        if any(term in lower_chunk for term in BIOMARKER_TERMS) and any(
            term in lower_chunk for term in NOVEL_TERMS
        ):
            filtered_abstracts.append(chunk)

    return filtered_abstracts


TIER_INTERPRETATION = {
    3: "Clinically validated biomarker with domain-specific support.",
    2: "Emerging biomarker with clinical trial and literature evidence.",
    1: "Literature-supported or domain-supported biomarker.",
    0: "Insufficient validated evidence.",
}


def _infer_domain_category(domain_query: str) -> str:
    """Infer domain for validation: Oncology, Immunology, Neuroscience, or Other."""
    if not domain_query or not isinstance(domain_query, str):
        return "Other"
    q = domain_query.lower().strip()
    if any(t in q for t in ("cancer", "oncology", "tumor", "carcinoma", "melanoma", "leukemia", "lymphoma")):
        return "Oncology"
    if any(t in q for t in ("immun", "autoimmune", "allerg", "vaccine")):
        return "Immunology"
    if any(t in q for t in ("neuro", "brain", "alzheimer", "parkinson", "cognit")):
        return "Neuroscience"
    return "Other"


def _domain_validated(domain: str, from_trials: bool, from_pubs: bool) -> tuple[bool, list[str]]:
    """
    Step 3 — Domain-specific validation. Placeholder: True when domain is specified and evidence exists.
    """
    if not domain or not domain.strip():
        return False, []
    cat = _infer_domain_category(domain)
    has_evidence = from_trials or from_pubs
    if not has_evidence:
        return False, []
    if cat == "Oncology":
        return True, ["cBioPortal", "COSMIC", "OncoKB"]
    if cat == "Immunology":
        return True, ["ImmPort", "IEDB", "UniProt"]
    if cat == "Neuroscience":
        return True, ["Open Targets", "Allen Brain", "DisGeNET"]
    return True, []


def _evidence_tier(
    clinical_trials: bool,
    pubmed: bool,
    domain_validated: bool,
) -> tuple[int, str]:
    """
    Step 4 — Strict 0-3 Evidence Tier (presence-based only; no composite/weighted/maturity).
    Tier 3: clinical_trials AND pubmed AND domain_validated
    Tier 2: clinical_trials AND pubmed
    Tier 1: pubmed OR domain_validated
    Tier 0: no validated presence
    """
    if clinical_trials and pubmed and domain_validated:
        return 3, TIER_INTERPRETATION[3]
    if clinical_trials and pubmed:
        return 2, TIER_INTERPRETATION[2]
    if pubmed or domain_validated:
        return 1, TIER_INTERPRETATION[1]
    return 0, TIER_INTERPRETATION[0]


def _build_biomarker_summary(
    biomarker: str,
    condition: str,
    publication_count: int,
    has_trial: bool,
    has_phase_ii: bool,
) -> str:
    if has_trial:
        trial_phrase = "and ongoing clinical evaluation"
        stage = "Phase II" if has_phase_ii else "Phase I"
    else:
        trial_phrase = "and no registered clinical trials yet"
        stage = "preclinical research"

    return (
        f"{biomarker} is an emerging biomarker studied in {condition}. "
        f"Evidence includes {publication_count} recent publications {trial_phrase}. "
        f"Current validation stage: {stage}."
    )


def generate_biomarker_data(therapeutic_area: str) -> tuple[pd.DataFrame, dict]:
    """Returns (df, metadata). metadata has n_trials, n_pubs, api_ok, open_targets_ok for indicators."""
    query = therapeutic_area.strip()
    empty_df = pd.DataFrame(
        columns=["Biomarker", "Evidence_Tier", "Interpretation", "Sources", "Summary", "OpenTargets_Score"]
    )
    if not query:
        return empty_df, {"n_trials": 0, "n_pubs": 0, "api_ok": True, "open_targets_ok": True}

    try:
        clinical_trials = _fetch_clinical_trials(query)
        pubmed_abstracts = _fetch_pubmed_abstracts(query)
        api_ok = True
    except Exception:
        clinical_trials = []
        pubmed_abstracts = []
        api_ok = False

    open_targets_ok = check_open_targets_health()
    evidence: dict[str, dict] = {}
    _base_ev = {
        "name": "",
        "from_trials": False,
        "from_pubs": False,
        "has_phase_ii": False,
        "has_phase_iii": False,
        "pub_count": 0,
        "trial_count": 0,
    }

    for record in clinical_trials:
        interventions_text = record.get("intervention", "")
        phase = record.get("phase", "I")
        tokens = _extract_biomarkers(interventions_text)
        for token in tokens:
            norm = _normalize_name(token)
            if not norm:
                continue
            ev = evidence.setdefault(norm, {**_base_ev, "evidence_texts": []})
            if not ev.get("name"):
                ev["name"] = token
            ev["from_trials"] = True
            ev["trial_count"] = int(ev.get("trial_count", 0)) + 1
            if phase == "II":
                ev["has_phase_ii"] = True
            if phase == "III":
                ev["has_phase_iii"] = True
            if interventions_text:
                ev.setdefault("evidence_texts", []).append(interventions_text)

    for abstract in pubmed_abstracts:
        tokens = _extract_biomarkers(abstract)
        for token in tokens:
            norm = _normalize_name(token)
            if not norm:
                continue
            ev = evidence.setdefault(norm, {**_base_ev, "evidence_texts": []})
            if not ev.get("name"):
                ev["name"] = token
            ev["from_pubs"] = True
            ev["pub_count"] = int(ev.get("pub_count", 0)) + 1
            if abstract:
                ev.setdefault("evidence_texts", []).append(abstract)

    domain_cat = _infer_domain_category(query)
    records: list[dict] = []
    for norm, ev in evidence.items():
        from_trials = bool(ev.get("from_trials"))
        from_pubs = bool(ev.get("from_pubs"))

        if not from_trials and not from_pubs:
            continue

        domain_validated, domain_sources = _domain_validated(query, from_trials, from_pubs)
        tier, interpretation = _evidence_tier(from_trials, from_pubs, domain_validated)

        biomarker_name = ev.get("name", norm)
        pub_count = int(ev.get("pub_count", 0))
        has_phase_ii = bool(ev.get("has_phase_ii"))
        has_phase_iii = bool(ev.get("has_phase_iii"))

        global_sources = {
            "clinical_trials": from_trials,
            "pubmed": from_pubs,
            "clinvar": False,
            "fda": False,
        }
        sources_list = []
        if from_trials:
            sources_list.append("clinical")
        if pub_count > 0:
            sources_list.append("pubmed")
        sources_str = ", ".join(sorted(sources_list))
        summary = _build_biomarker_summary(biomarker_name, query, pub_count, from_trials, has_phase_ii or has_phase_iii)

        records.append(
            {
                "Biomarker": biomarker_name,
                "Evidence_Tier": tier,
                "Interpretation": interpretation,
                "Sources": sources_str,
                "Summary": summary,
                "OpenTargets_Score": 0.0,
                "domain": domain_cat,
                "validated": _is_valid_biomarker(biomarker_name),
                "global_sources": global_sources,
                "domain_sources": domain_sources,
            }
        )

    if not records:
        return empty_df, {"n_trials": len(clinical_trials), "n_pubs": len(pubmed_abstracts), "api_ok": api_ok, "open_targets_ok": open_targets_ok}

    for rec in records:
        score = fetch_open_targets_score(rec["Biomarker"], query)[0] if open_targets_ok else 0.0
        rec["OpenTargets_Score"] = round(score, 3)
        t = rec["Evidence_Tier"]
        if t == 2 and score >= 0.6:
            rec["Evidence_Tier"] = 3
            rec["Interpretation"] = TIER_INTERPRETATION[3]
        elif t == 1 and score >= 0.4:
            rec["Evidence_Tier"] = 2
            rec["Interpretation"] = TIER_INTERPRETATION[2]

    df = pd.DataFrame.from_records(records)
    df = df.sort_values("Evidence_Tier", ascending=False).reset_index(drop=True)
    return df, {"n_trials": len(clinical_trials), "n_pubs": len(pubmed_abstracts), "api_ok": api_ok, "open_targets_ok": open_targets_ok}


def biomarker_evidence_to_structured_json(df: pd.DataFrame) -> str:
    """Return pipeline output as structured JSON (strict 0–3 Evidence Tier)."""
    if df is None or df.empty:
        return "No validated molecular biomarkers detected."
    out = []
    for _, row in df.iterrows():
        sources_str = row.get("Sources", "")
        sources_list = [s.strip() for s in sources_str.split(",")] if sources_str else []
        out.append({
            "biomarker": str(row.get("Biomarker", "")),
            "evidence_tier": int(row.get("Evidence_Tier", 0)),
            "interpretation": str(row.get("Interpretation", "")),
            "sources": sources_list,
        })
    return json.dumps(out, indent=2)


def biomarker_evidence_to_domain_json(df: pd.DataFrame) -> str:
    """Return full domain-aware validation output."""
    if df is None or df.empty:
        return json.dumps({"message": "No validated molecular biomarkers detected."}, indent=2)
    out = []
    for _, row in df.iterrows():
        gs = row.get("global_sources")
        if gs is None or isinstance(gs, dict):
            gs = gs or {}
        else:
            gs = {}
        out.append({
            "biomarker": str(row.get("Biomarker", "")),
            "domain": str(row.get("domain", "Other")),
            "validated": bool(row.get("validated", True)),
            "global_sources": {
                "clinical_trials": gs.get("clinical_trials", False),
                "pubmed": gs.get("pubmed", False),
                "clinvar": gs.get("clinvar", False),
                "fda": gs.get("fda", False),
            },
            "domain_sources": list(row.get("domain_sources") or []),
            "evidence_tier": int(row.get("Evidence_Tier", 0)),
            "interpretation": str(row.get("Interpretation", "")),
        })
    return json.dumps(out, indent=2)


def investment_insight(mean_tier: float) -> str:
    """Insight from mean Evidence_Tier (0-3)."""
    if mean_tier < 1.0:
        return "Exploratory / insufficient evidence landscape."
    if mean_tier < 2.0:
        return "Early research signals with limited validation."
    return "Emerging to clinically advancing biomarker evidence."


# Full-width terminal search
st.markdown('<div class="terminal-search-wrap">', unsafe_allow_html=True)
therapeutic_area = st.text_input(
    "search",
    placeholder="Disease or therapeutic area (e.g. lung cancer)",
    label_visibility="collapsed",
    key="terminal_search",
)
st.markdown("</div>", unsafe_allow_html=True)

therapeutic_area = therapeutic_area.strip().lower().replace("and", ",").replace("  ", " ")

if therapeutic_area and len(therapeutic_area) < 4:
    st.caption("Tip: use full disease name for better results")

if "selected_biomarker" not in st.session_state:
    st.session_state["selected_biomarker"] = None
if "last_meta" not in st.session_state:
    st.session_state["last_meta"] = {"n_trials": 0, "n_pubs": 0, "api_ok": True, "open_targets_ok": True}

if therapeutic_area:
    df, meta = generate_biomarker_data(therapeutic_area)
    st.session_state["last_meta"] = meta
    n_trials = meta.get("n_trials", 0)
    n_pubs = meta.get("n_pubs", 0)
    api_ok = meta.get("api_ok", True)

    if not df.empty:
        full_display_df = df[df["Biomarker"].apply(_is_valid_biomarker)].copy()
        if full_display_df.empty:
            st.warning("No biomarkers passed validation. Try broader search.")
        else:
            full_sorted = full_display_df.sort_values(["Evidence_Tier", "Biomarker"], ascending=[False, True])
            mean_tier = float(full_sorted["Evidence_Tier"].mean())
            total_biomarkers = len(full_sorted)
            clinical_pct = (full_sorted["Evidence_Tier"] >= 2).sum() / total_biomarkers * 100 if total_biomarkers else 0
            top_ranked = full_sorted.iloc[0]["Biomarker"] if total_biomarkers else "—"

            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            with kpi1:
                score_class = "signal-strong" if mean_tier >= 2.0 else ("signal-amber" if mean_tier >= 1.0 else "signal-weak")
                st.markdown(f'<div class="kpi-card"><div class="kpi-label">Portfolio Score</div><div class="kpi-value {score_class}">{mean_tier:.1f}</div><div class="kpi-label">Mean score 0–3</div></div>', unsafe_allow_html=True)
            with kpi2:
                st.markdown(f'<div class="kpi-card"><div class="kpi-label">Total Biomarkers</div><div class="kpi-value">{total_biomarkers}</div><div class="kpi-label">Qualified entities</div></div>', unsafe_allow_html=True)
            with kpi3:
                st.markdown(f'<div class="kpi-card"><div class="kpi-label">Clinical Coverage</div><div class="kpi-value">{clinical_pct:.0f}%</div><div class="kpi-label">Score 2 or 3</div></div>', unsafe_allow_html=True)
            with kpi4:
                st.markdown(f'<div class="kpi-card"><div class="kpi-label">Top Ranked Biomarker</div><div class="kpi-value" style="font-size:1rem;">{top_ranked}</div><div class="kpi-label">By score</div></div>', unsafe_allow_html=True)

            # Slim horizontal score indicator: 0=gray, 1=yellow, 2=orange, 3=green (no internal metrics)
            tier_counts = full_sorted["Evidence_Tier"].value_counts().reindex([0, 1, 2, 3], fill_value=0)
            total = tier_counts.sum()
            if total > 0:
                pct0 = 100 * tier_counts.get(0, 0) / total
                pct1 = 100 * tier_counts.get(1, 0) / total
                pct2 = 100 * tier_counts.get(2, 0) / total
                pct3 = 100 * tier_counts.get(3, 0) / total
            else:
                pct0 = pct1 = pct2 = pct3 = 0
            st.markdown('<div class="kpi-label" style="margin-bottom: 4px; color: var(--text-secondary); font-size: 0.7rem;">Score distribution (0–3)</div>', unsafe_allow_html=True)
            fig = go.Figure()
            fig.add_trace(go.Bar(y=[0], x=[pct0], orientation="h", name="0", marker_color="#6b7280", text=[f"{pct0:.0f}%" if pct0 > 0 else ""], textposition="inside", insidetextanchor="middle", showlegend=False))
            fig.add_trace(go.Bar(y=[0], x=[pct1], orientation="h", name="1", marker_color="#eab308", text=[f"{pct1:.0f}%" if pct1 > 0 else ""], textposition="inside", insidetextanchor="middle", showlegend=False))
            fig.add_trace(go.Bar(y=[0], x=[pct2], orientation="h", name="2", marker_color="#f97316", text=[f"{pct2:.0f}%" if pct2 > 0 else ""], textposition="inside", insidetextanchor="middle", showlegend=False))
            fig.add_trace(go.Bar(y=[0], x=[pct3], orientation="h", name="3", marker_color="#22c55e", text=[f"{pct3:.0f}%" if pct3 > 0 else ""], textposition="inside", insidetextanchor="middle", showlegend=False))
            fig.update_layout(
                barmode="stack",
                height=80,
                margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(visible=False, range=[0, 100]),
                yaxis=dict(visible=False),
                bargap=0,
                uniformtext_minsize=8,
                uniformtext_mode="hide",
            )
            fig.update_xaxes(showgrid=False, zeroline=False)
            fig.update_yaxes(showgrid=False, zeroline=False)
            st.plotly_chart(fig, use_container_width=True, key="tier_bar", config={"displayModeBar": False})

            st.markdown('<p class="section-title">Emerging Biomarkers Leaderboard</p>', unsafe_allow_html=True)
            filter_col1, filter_col2 = st.columns([1, 2])
            with filter_col1:
                source_filter = st.radio(
                    "Source",
                    ["All", "Clinical", "Literature", "Both"],
                    horizontal=True,
                    key="source_filter",
                )
            with filter_col2:
                search_query = st.text_input("Search biomarker", placeholder="Filter by biomarker name...", key="search_bm", label_visibility="collapsed")

            display_df = full_display_df.copy()
            if source_filter == "Clinical":
                display_df = display_df[display_df["Evidence_Tier"] == 2]
            elif source_filter == "Literature":
                display_df = display_df[display_df["Evidence_Tier"] == 1]
            elif source_filter == "Both":
                display_df = display_df[display_df["Evidence_Tier"] == 3]
            if search_query:
                display_df = display_df[display_df["Biomarker"].str.contains(search_query, case=False, na=False)]
            display_df = display_df.reset_index(drop=True)

            display_df = display_df.sort_values(["Evidence_Tier", "Biomarker"], ascending=[False, True]).reset_index(drop=True)
            # Strict 6-column contract: S.No | Biomarker | Type | Score | Source | Summary (no OpenTargets, no interpretation column)
            display_df["Type"] = "Gene"
            display_df["Score"] = display_df["Evidence_Tier"].astype(int)
            display_df["Source"] = display_df["Sources"]
            display_df.insert(0, "S. No.", range(1, len(display_df) + 1))
            API_COLUMNS = ["S. No.", "Biomarker", "Type", "Score", "Source", "Summary"]
            table_df = display_df[[c for c in API_COLUMNS if c in display_df.columns]].copy()
            csv = table_df.to_csv(index=False)

            btn_col1, btn_col2 = st.columns([6, 1])
            with btn_col2:
                st.download_button("Export CSV", data=csv, file_name="biomarker_signals.csv", mime="text/csv", key="export_csv")

            st.markdown('<div class="leaderboard-panel">', unsafe_allow_html=True)
            event = st.dataframe(
                table_df,
                use_container_width=True,
                height=500,
                column_config={
                    "S. No.": st.column_config.NumberColumn(label="S. No.", width=70, format="%d"),
                    "Biomarker": st.column_config.TextColumn("Biomarker", width=150),
                    "Type": st.column_config.TextColumn("Type", width=90),
                    "Score": st.column_config.NumberColumn("Score", width=80, format="%d"),
                    "Source": st.column_config.TextColumn("Source", width=180),
                    "Summary": st.column_config.TextColumn("Summary", width="large"),
                },
                on_select="rerun",
                selection_mode="single-row",
                key="leaderboard_df",
            )
            st.markdown("</div>", unsafe_allow_html=True)

            with st.sidebar:
                st.markdown("### Biomarker detail")
                detail_row = None
                if event and getattr(event, "selection", None) and getattr(event.selection, "rows", None):
                    sel = list(event.selection.rows) or []
                    if sel and 0 <= sel[0] < len(display_df):
                        detail_row = display_df.iloc[sel[0]]
                if detail_row is None:
                    choices = ["— Select biomarker —"] + display_df["Biomarker"].astype(str).tolist()
                    pick = st.selectbox("View details", choices, key="detail_pick")
                    if pick and pick != "— Select biomarker —":
                        match = display_df[display_df["Biomarker"].astype(str) == pick]
                        if not match.empty:
                            detail_row = match.iloc[0]
                if detail_row is not None:
                    t = int(detail_row.get("Score", detail_row.get("Evidence_Tier", 0)))
                    st.markdown(f"**{detail_row['Biomarker']}**")
                    st.markdown(f'<span class="tier-badge tier-badge-{t}">Score {t}</span>', unsafe_allow_html=True)
                    st.caption(f"Source: {detail_row.get('Source', detail_row.get('Sources', ''))}")
                    st.markdown("**Summary**")
                    st.write(detail_row.get("Summary", ""))
                else:
                    st.caption("Select a row in the table or use the dropdown to view details.")
    else:
        st.warning("No biomarkers found. Try a different query.")
else:
    st.caption("Enter a therapeutic area to load the leaderboard.")
