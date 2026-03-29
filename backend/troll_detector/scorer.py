"""Troll Probability Score (TPS) computation engine.

Implements 4 real scoring factors and 2 stubs, as specified in patent claims 1-4.
"""

import logging

from .config import (
    TPS_WEIGHTS,
    TPS_FLAG_THRESHOLD,
    FILING_VOLUME_HIGH,
    FILING_VOLUME_LOW,
    DISPERSION_HIGH,
    DISPERSION_LOW,
)
from .models import PatentFiling, TPSBreakdown
from .nlp import claim_breadth_score, linguistic_fingerprint_score

logger = logging.getLogger(__name__)


def compute_tps(
    filing: PatentFiling,
    assignee_filing_count: int = 0,
    assignee_cpc_codes: list[str] | None = None,
    related_claims_texts: list[str] | None = None,
) -> TPSBreakdown:
    """Compute the Troll Probability Score breakdown for a patent filing.

    Args:
        filing: The patent filing to score.
        assignee_filing_count: Number of filings by same assignee in rolling window.
        assignee_cpc_codes: CPC codes across all assignee filings.
        related_claims_texts: Claim texts from other filings by same assignee
                              (for linguistic fingerprinting cross-comparison).
    """
    breakdown = TPSBreakdown()

    # (i) Filing Volume — patent claim 1
    breakdown.filing_volume = _scale_linear(
        assignee_filing_count, FILING_VOLUME_LOW, FILING_VOLUME_HIGH
    )

    # (ii) Domain Dispersion — patent claim 1
    if assignee_cpc_codes:
        # Count distinct CPC subclasses (e.g., G06F, H04L — first 4 chars)
        # High dispersion across unrelated subclasses = troll indicator
        subclasses = set(c[:4] if len(c) >= 4 else c for c in assignee_cpc_codes if c)
        breakdown.domain_dispersion = _scale_linear(
            len(subclasses), DISPERSION_LOW, DISPERSION_HIGH
        )

    # (iii) Claim Breadth Index — patent claim 3
    text = filing.claims_text or filing.abstract_text or ""
    breakdown.claim_breadth = claim_breadth_score(text)

    # (iv) Commercial Activity Correlation — patent claim 4 (STUBBED)
    breakdown.commercial_activity = 50.0

    # (v) Linguistic Fingerprinting — patent claim 2
    if related_claims_texts and len(related_claims_texts) >= 2:
        breakdown.linguistic_fingerprint = linguistic_fingerprint_score(
            related_claims_texts
        )
    else:
        # Single filing — use self-analysis of claim text
        if text:
            # Split into pseudo-documents by claim boundaries
            chunks = [c.strip() for c in text.split(';') if len(c.strip()) > 20]
            if len(chunks) >= 2:
                breakdown.linguistic_fingerprint = linguistic_fingerprint_score(chunks)
            else:
                breakdown.linguistic_fingerprint = 50.0
        else:
            breakdown.linguistic_fingerprint = 50.0

    # (vi) Litigation History (STUBBED)
    breakdown.litigation_history = 50.0

    return breakdown


def compute_weighted_tps(breakdown: TPSBreakdown) -> float:
    """Compute the weighted TPS from a breakdown."""
    score = (
        breakdown.filing_volume * TPS_WEIGHTS["filing_volume"]
        + breakdown.domain_dispersion * TPS_WEIGHTS["domain_dispersion"]
        + breakdown.claim_breadth * TPS_WEIGHTS["claim_breadth"]
        + breakdown.commercial_activity * TPS_WEIGHTS["commercial_activity"]
        + breakdown.linguistic_fingerprint * TPS_WEIGHTS["linguistic_fingerprint"]
        + breakdown.litigation_history * TPS_WEIGHTS["litigation_history"]
    )
    return round(max(0.0, min(100.0, score)), 1)


def is_flagged(tps_score: float) -> bool:
    return tps_score >= TPS_FLAG_THRESHOLD


def _scale_linear(value: float, low: float, high: float) -> float:
    """Scale a value linearly to 0-100 between low and high thresholds."""
    if value <= low:
        return 0.0
    if value >= high:
        return 100.0
    return ((value - low) / (high - low)) * 100.0
