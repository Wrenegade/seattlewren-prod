"""USPTO Patent Filing Monitor — fetches patent data from PatentsView API."""

import json
import logging
from datetime import date, timedelta

import httpx

from .config import (
    PATENTSVIEW_PATENTS,
    PATENTSVIEW_ASSIGNEES,
    FILING_VOLUME_WINDOW_DAYS,
)
from .models import PatentFiling

logger = logging.getLogger(__name__)

TIMEOUT = httpx.Timeout(30.0, connect=10.0)


async def fetch_recent_patents(
    days_back: int = 30,
    per_page: int = 100,
    page: int = 1,
) -> list[PatentFiling]:
    """Fetch recently published patents from PatentsView API."""
    since = (date.today() - timedelta(days=days_back)).isoformat()
    query = json.dumps({"_gte": {"patent_date": since}})
    fields = json.dumps([
        "patent_number", "patent_title", "patent_date", "patent_abstract",
        "patent_num_claims",
    ])
    options = json.dumps({"per_page": per_page, "page": page})

    params = {"q": query, "f": fields, "o": options}

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(PATENTSVIEW_PATENTS, params=params)
        resp.raise_for_status()
        data = resp.json()

    patents = []
    for p in data.get("patents", []):
        patents.append(PatentFiling(
            application_num=p.get("patent_number", ""),
            title=p.get("patent_title", ""),
            filing_date=_parse_date(p.get("patent_date")),
            abstract_text=p.get("patent_abstract", ""),
        ))
    return patents


async def fetch_patent_details(patent_number: str) -> dict | None:
    """Fetch detailed info for a single patent including claims and assignee."""
    query = json.dumps({"patent_number": patent_number})
    fields = json.dumps([
        "patent_number", "patent_title", "patent_date", "patent_abstract",
        "patent_num_claims",
    ])

    params = {"q": query, "f": fields}

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(PATENTSVIEW_PATENTS, params=params)
        resp.raise_for_status()
        data = resp.json()

    patents = data.get("patents", [])
    if not patents:
        return None
    return patents[0]


async def fetch_assignee_filing_count(assignee: str) -> int:
    """Count how many patents an assignee has filed in the rolling window."""
    if not assignee:
        return 0

    since = (date.today() - timedelta(days=FILING_VOLUME_WINDOW_DAYS)).isoformat()
    query = json.dumps({
        "_and": [
            {"_text_any": {"assignee_organization": assignee}},
            {"_gte": {"patent_date": since}},
        ]
    })
    fields = json.dumps(["patent_number"])
    options = json.dumps({"per_page": 1})

    params = {"q": query, "f": fields, "o": options}

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(PATENTSVIEW_PATENTS, params=params)
        resp.raise_for_status()
        data = resp.json()

    return data.get("total_patent_count", 0)


async def fetch_assignee_cpc_codes(assignee: str) -> list[str]:
    """Get distinct CPC codes for an assignee's filings."""
    if not assignee:
        return []

    query = json.dumps({"_text_any": {"assignee_organization": assignee}})
    fields = json.dumps(["patent_number", "cpc_group_id"])
    options = json.dumps({"per_page": 100})

    params = {"q": query, "f": fields, "o": options}

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(PATENTSVIEW_PATENTS, params=params)
        resp.raise_for_status()
        data = resp.json()

    cpc_codes = set()
    for p in data.get("patents", []):
        for cpc in p.get("cpcs", []):
            code = cpc.get("cpc_group_id", "")
            if code:
                # Extract the section letter (first char) for dispersion analysis
                cpc_codes.add(code)
    return list(cpc_codes)


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None
