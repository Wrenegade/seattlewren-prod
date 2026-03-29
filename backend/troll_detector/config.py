"""Configuration for the Patent Troll Defense System."""

# Troll Probability Score weights (must sum to 1.0)
TPS_WEIGHTS = {
    "filing_volume": 0.20,
    "domain_dispersion": 0.15,
    "claim_breadth": 0.20,
    "commercial_activity": 0.10,  # stubbed — returns neutral
    "linguistic_fingerprint": 0.25,
    "litigation_history": 0.10,  # stubbed — returns neutral
}

# TPS threshold for flagging a patent
TPS_FLAG_THRESHOLD = 55.0

# PatentsView API
PATENTSVIEW_BASE = "https://api.patentsview.org"
PATENTSVIEW_PATENTS = f"{PATENTSVIEW_BASE}/patents/query"
PATENTSVIEW_ASSIGNEES = f"{PATENTSVIEW_BASE}/assignees/query"

# Filing volume: how many filings in this window (days) triggers suspicion
FILING_VOLUME_WINDOW_DAYS = 365
FILING_VOLUME_HIGH = 50  # >50 filings/year = max score
FILING_VOLUME_LOW = 5    # <5 filings/year = min score

# Domain dispersion: how many unrelated CPC subclasses triggers suspicion
DISPERSION_HIGH = 6  # 6+ distinct CPC subclasses = max score
DISPERSION_LOW = 2   # 2 or fewer = min score

# Risk assessment: semantic similarity threshold
RISK_HIGH = 75
RISK_MEDIUM = 40

# Prior art search sources
PRIOR_ART_SOURCES = [
    "google_patents",
    "arxiv",
]
