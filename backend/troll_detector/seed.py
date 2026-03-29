"""Seed script — fetches real patent data from PatentsView and computes TPS scores.

Run inside the backend container:
    python -m troll_detector.seed
"""

import asyncio
import json
import logging
import os
import sys

import asyncpg
import httpx

# Adjust path so we can import sibling modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from troll_detector.config import TPS_FLAG_THRESHOLD, PATENTSVIEW_PATENTS
from troll_detector.models import PatentFiling
from troll_detector.scorer import compute_tps, compute_weighted_tps, is_flagged
from troll_detector.nlp import fit_vectorizer, claim_breadth_score, linguistic_fingerprint_score

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@host.docker.internal:5432/seattle_wren"
)

TIMEOUT = httpx.Timeout(30.0, connect=10.0)

# Queries designed to find patents that look troll-ish:
# high-volume filers, broad AI/software claims, NPE-associated terms
SEED_QUERIES = [
    # Recent broad AI patents
    {
        "q": json.dumps({"_and": [
            {"_gte": {"patent_date": "2025-01-01"}},
            {"_text_any": {"patent_abstract": "artificial intelligence machine learning system method"}},
        ]}),
        "f": json.dumps([
            "patent_number", "patent_title", "patent_date", "patent_abstract",
            "patent_num_claims",
        ]),
        "o": json.dumps({"per_page": 50, "page": 1}),
    },
    # Recent blockchain/crypto patents (common troll target)
    {
        "q": json.dumps({"_and": [
            {"_gte": {"patent_date": "2025-01-01"}},
            {"_text_any": {"patent_abstract": "blockchain distributed ledger cryptocurrency token"}},
        ]}),
        "f": json.dumps([
            "patent_number", "patent_title", "patent_date", "patent_abstract",
            "patent_num_claims",
        ]),
        "o": json.dumps({"per_page": 25, "page": 1}),
    },
    # Recent IoT/smart device patents
    {
        "q": json.dumps({"_and": [
            {"_gte": {"patent_date": "2025-06-01"}},
            {"_text_any": {"patent_abstract": "internet of things smart device sensor connected"}},
        ]}),
        "f": json.dumps({"per_page": 25, "page": 1}),
    },
    # Recent broad software method patents
    {
        "q": json.dumps({"_and": [
            {"_gte": {"patent_date": "2025-06-01"}},
            {"_text_any": {"patent_abstract": "computer implemented method processing data platform"}},
        ]}),
        "f": json.dumps([
            "patent_number", "patent_title", "patent_date", "patent_abstract",
            "patent_num_claims",
        ]),
        "o": json.dumps({"per_page": 50, "page": 1}),
    },
]


async def fetch_patents(query_params: dict) -> list[dict]:
    """Fetch patents from PatentsView API."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            resp = await client.get(PATENTSVIEW_PATENTS, params=query_params)
            resp.raise_for_status()
            data = resp.json()
            return data.get("patents", [])
        except Exception as e:
            logger.warning(f"PatentsView query failed: {e}")
            return []


async def seed():
    logger.info("Starting patent data seed...")

    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=3)

    # Ensure tables exist
    await pool.execute("""
        CREATE TABLE IF NOT EXISTS patent_filings (
            id              SERIAL PRIMARY KEY,
            application_num TEXT UNIQUE NOT NULL,
            title           TEXT,
            filing_date     DATE,
            inventor_name   TEXT DEFAULT '',
            assignee        TEXT DEFAULT '',
            cpc_codes       TEXT[] DEFAULT '{}',
            claims_text     TEXT DEFAULT '',
            abstract_text   TEXT DEFAULT '',
            tps_score       REAL DEFAULT 0,
            tps_breakdown   JSONB DEFAULT '{}',
            flagged         BOOLEAN DEFAULT FALSE,
            analyzed_at     TIMESTAMPTZ DEFAULT now()
        )
    """)

    all_patents = []
    for i, params in enumerate(SEED_QUERIES):
        logger.info(f"Running seed query {i+1}/{len(SEED_QUERIES)}...")
        patents = await fetch_patents(params)
        logger.info(f"  Got {len(patents)} patents")
        all_patents.extend(patents)

    logger.info(f"Total patents fetched: {len(all_patents)}")

    # De-duplicate by patent number
    seen = set()
    unique = []
    for p in all_patents:
        num = p.get("patent_number", "")
        if num and num not in seen:
            seen.add(num)
            unique.append(p)

    logger.info(f"Unique patents: {len(unique)}")

    # Score and insert each patent
    inserted = 0
    flagged_count = 0
    all_abstracts = []
    all_ids = []

    for p in unique:
        patent_num = p.get("patent_number", "")
        title = p.get("patent_title", "")
        abstract = p.get("patent_abstract", "")
        filing_date = p.get("patent_date")
        num_claims = p.get("patent_num_claims")

        filing = PatentFiling(
            application_num=patent_num,
            title=title,
            abstract_text=abstract,
            filing_date=None,
        )
        if filing_date:
            try:
                from datetime import date
                filing.filing_date = date.fromisoformat(filing_date)
            except ValueError:
                pass

        # Compute TPS with what we have (no assignee data in bulk query)
        # Use abstract as proxy for claims text
        breakdown = compute_tps(
            filing,
            assignee_filing_count=0,
            assignee_cpc_codes=[],
            related_claims_texts=None,
        )

        # Boost score slightly for patents with many claims (correlates with breadth)
        if num_claims and int(num_claims) > 20:
            breakdown.claim_breadth = min(100, breakdown.claim_breadth + 15)

        tps = compute_weighted_tps(breakdown)
        flagged = is_flagged(tps)

        try:
            await pool.execute(
                """INSERT INTO patent_filings
                   (application_num, title, filing_date, abstract_text, tps_score, tps_breakdown, flagged)
                   VALUES ($1, $2, $3, $4, $5, $6, $7)
                   ON CONFLICT (application_num) DO UPDATE
                   SET tps_score = $5, tps_breakdown = $6, flagged = $7, analyzed_at = now()""",
                patent_num, title, filing.filing_date, abstract,
                tps, json.dumps(breakdown.to_dict()), flagged,
            )
            inserted += 1
            if flagged:
                flagged_count += 1
                all_abstracts.append(abstract)
                all_ids.append(patent_num)
        except Exception as e:
            logger.warning(f"Failed to insert {patent_num}: {e}")

    logger.info(f"Inserted/updated: {inserted}, Flagged: {flagged_count}")

    # Fit vectorizer on flagged patents
    if all_abstracts:
        fit_vectorizer(all_abstracts, all_ids)
        logger.info(f"Vectorizer fitted on {len(all_abstracts)} flagged patents")

    # Summary
    total = await pool.fetchval("SELECT COUNT(*) FROM patent_filings")
    total_flagged = await pool.fetchval("SELECT COUNT(*) FROM patent_filings WHERE flagged = TRUE")
    logger.info(f"Database totals: {total} patents, {total_flagged} flagged")

    await pool.close()
    logger.info("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
