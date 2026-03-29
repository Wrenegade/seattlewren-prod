"""Data models for the Patent Troll Defense System."""

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class PatentFiling:
    application_num: str
    title: str
    filing_date: date | None = None
    inventor_name: str = ""
    assignee: str = ""
    cpc_codes: list[str] = field(default_factory=list)
    claims_text: str = ""
    abstract_text: str = ""
    tps_score: float = 0.0
    tps_breakdown: dict = field(default_factory=dict)
    flagged: bool = False
    id: int | None = None
    analyzed_at: datetime | None = None


@dataclass
class TPSBreakdown:
    filing_volume: float = 0.0
    domain_dispersion: float = 0.0
    claim_breadth: float = 0.0
    commercial_activity: float = 50.0  # stubbed neutral
    linguistic_fingerprint: float = 0.0
    litigation_history: float = 50.0  # stubbed neutral

    def to_dict(self) -> dict:
        return {
            "filing_volume": round(self.filing_volume, 1),
            "domain_dispersion": round(self.domain_dispersion, 1),
            "claim_breadth": round(self.claim_breadth, 1),
            "commercial_activity": round(self.commercial_activity, 1),
            "commercial_activity_note": "Stubbed — requires business registry API access",
            "linguistic_fingerprint": round(self.linguistic_fingerprint, 1),
            "litigation_history": round(self.litigation_history, 1),
            "litigation_history_note": "Stubbed — requires PACER access",
        }


@dataclass
class RiskResult:
    risk_score: float
    overlapping_patents: list[dict] = field(default_factory=list)
    description: str = ""
    suggestions: list[str] = field(default_factory=list)


@dataclass
class PriorArtRef:
    source: str
    title: str
    url: str
    date_published: str = ""
    relevance_score: float = 0.0
    relevance_note: str = ""
