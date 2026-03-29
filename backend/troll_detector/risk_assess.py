"""Risk Assessment Module — compares user invention descriptions against flagged patents.

Implements patent claim 1: "performing, by a risk assessment module, semantic similarity
analysis comparing the natural language description against flagged patent filings to
generate a risk score and identify overlapping claims."
"""

import logging

from .config import RISK_HIGH, RISK_MEDIUM
from .models import RiskResult
from .nlp import semantic_similarity

logger = logging.getLogger(__name__)


def assess_risk(
    description: str,
    flagged_patents: list[dict],
) -> RiskResult:
    """Assess risk of a user's invention description against flagged patents.

    Args:
        description: Plain-language invention description from user.
        flagged_patents: List of flagged patent dicts from database with keys:
            application_num, title, abstract_text, claims_text, tps_score, tps_breakdown
    """
    if not description or not description.strip():
        return RiskResult(risk_score=0.0, description="No description provided.")

    if not flagged_patents:
        return RiskResult(
            risk_score=0.0,
            description=description,
            suggestions=["No flagged patents in the database yet. System is still ingesting data."],
        )

    # Run semantic similarity against flagged patent corpus
    similar = semantic_similarity(description, top_n=10)

    if not similar:
        return RiskResult(
            risk_score=5.0,
            description=description,
            suggestions=["No significant overlap detected with flagged patents."],
        )

    # Build overlap list
    # similar returns (application_num, similarity_score)
    patent_lookup = {p["application_num"]: p for p in flagged_patents}
    overlapping = []
    for app_num, sim_score in similar:
        patent = patent_lookup.get(app_num)
        if patent:
            overlap_pct = round(sim_score * 100, 1)
            overlapping.append({
                "application_num": patent["application_num"],
                "title": patent["title"],
                "tps_score": patent["tps_score"],
                "overlap_score": overlap_pct,
                "abstract": patent.get("abstract_text", "")[:300],
                "tps_breakdown": patent.get("tps_breakdown", {}),
            })

    # Risk score = weighted combination of max overlap and number of overlaps
    if overlapping:
        max_overlap = max(o["overlap_score"] for o in overlapping)
        num_overlaps = len([o for o in overlapping if o["overlap_score"] > 10])
        # Primary: max overlap. Secondary: breadth of overlaps.
        risk_score = min(100.0, max_overlap * 0.7 + num_overlaps * 5)
    else:
        risk_score = 5.0

    # Generate suggestions (patent claim 5)
    suggestions = _generate_suggestions(risk_score, overlapping)

    return RiskResult(
        risk_score=round(risk_score, 1),
        overlapping_patents=overlapping,
        description=description,
        suggestions=suggestions,
    )


def _generate_suggestions(risk_score: float, overlapping: list[dict]) -> list[str]:
    """Generate plain-language suggestions based on risk level."""
    suggestions = []

    if risk_score >= RISK_HIGH:
        suggestions.append(
            "HIGH RISK: Your concept has significant overlap with one or more flagged "
            "patent filings. Consider consulting a patent attorney before proceeding."
        )
        suggestions.append(
            "Review the overlapping claims carefully. Focus on differentiating your "
            "specific implementation from the broad claims identified."
        )
        suggestions.append(
            "Use the 'Generate Defense Package' button to compile prior art references "
            "that may invalidate the overlapping claims."
        )
    elif risk_score >= RISK_MEDIUM:
        suggestions.append(
            "MODERATE RISK: Some overlap detected. Your concept shares language with "
            "flagged filings, but overlap may be superficial."
        )
        suggestions.append(
            "Consider narrowing your invention description to emphasize unique aspects "
            "and specific technical details."
        )
    else:
        suggestions.append(
            "LOW RISK: Minimal overlap with flagged patent filings. Your concept appears "
            "to be in relatively clear territory."
        )
        suggestions.append(
            "This assessment is based on currently ingested patent data. New filings "
            "are monitored continuously."
        )

    if overlapping:
        top = overlapping[0]
        suggestions.append(
            f"Closest match: \"{top['title']}\" (TPS: {top['tps_score']}, "
            f"overlap: {top['overlap_score']}%). Review this filing's claims "
            "for specific conflict points."
        )

    return suggestions
