import json
import logging
import os
import re
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from troll_detector.config import TPS_FLAG_THRESHOLD
from troll_detector.models import PatentFiling
from troll_detector.nlp import fit_vectorizer
from troll_detector.scorer import compute_tps, compute_weighted_tps, is_flagged
from troll_detector.risk_assess import assess_risk
from troll_detector.prior_art import generate_prior_art_links, generate_defense_package

DATABASE_URL = os.environ["DATABASE_URL"]
EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pool: asyncpg.Pool = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)

    # Existing tables
    await pool.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id          SERIAL PRIMARY KEY,
            post_slug   TEXT NOT NULL,
            author_name TEXT NOT NULL,
            comment_text TEXT NOT NULL,
            parent_id   INTEGER REFERENCES comments(id),
            ip_address  TEXT,
            user_agent  TEXT,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    await pool.execute("""
        CREATE INDEX IF NOT EXISTS idx_comments_post_slug ON comments(post_slug)
    """)

    # Patent Troll Defense System tables
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
    await pool.execute("""
        CREATE TABLE IF NOT EXISTS troll_checks (
            id              SERIAL PRIMARY KEY,
            description     TEXT NOT NULL,
            risk_score      REAL,
            overlapping     JSONB DEFAULT '[]',
            prior_art       JSONB DEFAULT '[]',
            created_at      TIMESTAMPTZ DEFAULT now()
        )
    """)
    await pool.execute("""
        CREATE INDEX IF NOT EXISTS idx_patent_filings_flagged ON patent_filings(flagged)
            WHERE flagged = TRUE
    """)
    await pool.execute("""
        CREATE INDEX IF NOT EXISTS idx_patent_filings_tps ON patent_filings(tps_score DESC)
    """)

    # Fit the NLP vectorizer on existing flagged patents
    await _rebuild_vectorizer()

    logger.info("Patent Troll Defense System initialized")
    yield
    await pool.close()


async def _rebuild_vectorizer():
    """Rebuild the TF-IDF vectorizer from flagged patent texts."""
    rows = await pool.fetch(
        "SELECT application_num, claims_text, abstract_text FROM patent_filings WHERE flagged = TRUE"
    )
    if rows:
        texts = [r["claims_text"] or r["abstract_text"] or "" for r in rows]
        ids = [r["application_num"] for r in rows]
        fit_vectorizer(texts, ids)
        logger.info(f"Vectorizer fitted on {len(rows)} flagged patents")
    else:
        logger.info("No flagged patents yet — vectorizer empty")


def _get_ip(request: Request) -> str:
    return (
        request.headers.get("cf-connecting-ip")
        or (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
        or request.headers.get("x-real-ip")
        or request.client.host
    )


limiter = Limiter(key_func=_get_ip)
app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"error": "Too many requests"})


# ─── Existing endpoints ──────────────────────────────────────────────

@app.post("/api/newsletter", status_code=201)
@limiter.limit("10/hour")
async def subscribe(request: Request):
    body = await request.json()
    email = (body.get("email") or "").strip()
    name = (body.get("name") or "").strip() or None

    if not email:
        return JSONResponse(status_code=400, content={"error": "Email is required"})
    if not EMAIL_REGEX.match(email):
        return JSONResponse(status_code=400, content={"error": "Invalid email format"})
    if len(email) > 255:
        return JSONResponse(status_code=400, content={"error": "Email is too long"})
    if name and len(name) > 255:
        return JSONResponse(status_code=400, content={"error": "Name is too long"})

    existing = await pool.fetchrow(
        "SELECT id FROM newsletter_subscriptions WHERE email = $1", email
    )
    if existing:
        return JSONResponse(status_code=400, content={"error": "Email already subscribed"})

    row = await pool.fetchrow(
        "INSERT INTO newsletter_subscriptions (email, name) VALUES ($1, $2) RETURNING *",
        email, name,
    )
    return {
        "id": row["id"],
        "email": row["email"],
        "name": row["name"],
        "subscribed_at": row["subscribed_at"].isoformat(),
    }


@app.post("/api/page-views", status_code=201)
async def record_page_view(request: Request):
    body = await request.json()
    path = body.get("path")

    if not path:
        return JSONResponse(status_code=400, content={"error": "Path is required"})

    ip_address = _get_ip(request)
    user_agent = request.headers.get("user-agent")
    referer = request.headers.get("referer")
    country = request.headers.get("cf-ipcountry")
    city = request.headers.get("cf-ipcity")

    await pool.execute(
        """INSERT INTO page_views (path, ip_address, user_agent, referer, country, city)
           VALUES ($1, $2, $3, $4, $5, $6)""",
        path, ip_address, user_agent, referer, country, city,
    )
    return {"success": True}


@app.get("/api/comments/{slug:path}")
async def get_comments(slug: str):
    rows = await pool.fetch(
        """SELECT id, post_slug, author_name, comment_text, parent_id,
                  created_at
           FROM comments
           WHERE post_slug = $1
           ORDER BY created_at ASC""",
        slug,
    )
    return [
        {
            "id": r["id"],
            "post_slug": r["post_slug"],
            "author_name": r["author_name"],
            "comment_text": r["comment_text"],
            "parent_id": r["parent_id"],
            "created_at": r["created_at"].isoformat(),
        }
        for r in rows
    ]


@app.post("/api/comments", status_code=201)
@limiter.limit("10/hour")
async def post_comment(request: Request):
    body = await request.json()
    post_slug = (body.get("post_slug") or "").strip()
    author_name = (body.get("author_name") or "").strip()
    comment_text = (body.get("comment_text") or "").strip()
    parent_id = body.get("parent_id")

    if not post_slug:
        return JSONResponse(status_code=400, content={"error": "post_slug is required"})
    if not author_name:
        return JSONResponse(status_code=400, content={"error": "Name is required"})
    if len(author_name) > 100:
        return JSONResponse(status_code=400, content={"error": "Name is too long"})
    if not comment_text:
        return JSONResponse(status_code=400, content={"error": "Comment is required"})
    if len(comment_text) > 5000:
        return JSONResponse(status_code=400, content={"error": "Comment is too long (max 5000 chars)"})

    if parent_id is not None:
        parent = await pool.fetchrow("SELECT id FROM comments WHERE id = $1", int(parent_id))
        if not parent:
            return JSONResponse(status_code=400, content={"error": "Parent comment not found"})

    ip_address = _get_ip(request)
    user_agent = request.headers.get("user-agent")

    row = await pool.fetchrow(
        """INSERT INTO comments (post_slug, author_name, comment_text, parent_id, ip_address, user_agent)
           VALUES ($1, $2, $3, $4, $5, $6)
           RETURNING id, post_slug, author_name, comment_text, parent_id, created_at""",
        post_slug, author_name, comment_text,
        int(parent_id) if parent_id is not None else None,
        ip_address, user_agent,
    )
    return {
        "id": row["id"],
        "post_slug": row["post_slug"],
        "author_name": row["author_name"],
        "comment_text": row["comment_text"],
        "parent_id": row["parent_id"],
        "created_at": row["created_at"].isoformat(),
    }


# ─── Patent Troll Defense System endpoints ───────────────────────────

@app.post("/api/troll-check")
@limiter.limit("30/hour")
async def troll_check(request: Request):
    """Risk assessment: accepts invention description, returns risk score + overlapping patents."""
    body = await request.json()
    description = (body.get("description") or "").strip()

    if not description:
        return JSONResponse(status_code=400, content={"error": "Description is required"})
    if len(description) > 10000:
        return JSONResponse(status_code=400, content={"error": "Description too long (max 10,000 chars)"})

    # Get flagged patents from DB
    rows = await pool.fetch(
        """SELECT application_num, title, abstract_text, claims_text, tps_score, tps_breakdown
           FROM patent_filings WHERE flagged = TRUE
           ORDER BY tps_score DESC"""
    )
    flagged_patents = [
        {
            "application_num": r["application_num"],
            "title": r["title"],
            "abstract_text": r["abstract_text"],
            "claims_text": r["claims_text"],
            "tps_score": r["tps_score"],
            "tps_breakdown": json.loads(r["tps_breakdown"]) if r["tps_breakdown"] else {},
        }
        for r in rows
    ]

    result = assess_risk(description, flagged_patents)

    # Log the check
    await pool.execute(
        """INSERT INTO troll_checks (description, risk_score, overlapping)
           VALUES ($1, $2, $3)""",
        description, result.risk_score,
        json.dumps(result.overlapping_patents),
    )

    return {
        "risk_score": result.risk_score,
        "risk_level": (
            "HIGH" if result.risk_score >= 75 else
            "MODERATE" if result.risk_score >= 40 else
            "LOW"
        ),
        "overlapping_patents": result.overlapping_patents,
        "suggestions": result.suggestions,
        "patent_count_analyzed": len(flagged_patents),
    }


@app.get("/api/troll-scores")
async def get_troll_scores(limit: int = 50, flagged_only: bool = False):
    """Return recently analyzed patents with their TPS scores."""
    if flagged_only:
        rows = await pool.fetch(
            """SELECT id, application_num, title, filing_date, assignee,
                      tps_score, tps_breakdown, flagged, analyzed_at
               FROM patent_filings
               WHERE flagged = TRUE
               ORDER BY tps_score DESC
               LIMIT $1""",
            min(limit, 200),
        )
    else:
        rows = await pool.fetch(
            """SELECT id, application_num, title, filing_date, assignee,
                      tps_score, tps_breakdown, flagged, analyzed_at
               FROM patent_filings
               ORDER BY tps_score DESC
               LIMIT $1""",
            min(limit, 200),
        )
    return [
        {
            "id": r["id"],
            "application_num": r["application_num"],
            "title": r["title"],
            "filing_date": r["filing_date"].isoformat() if r["filing_date"] else None,
            "assignee": r["assignee"],
            "tps_score": r["tps_score"],
            "tps_breakdown": json.loads(r["tps_breakdown"]) if r["tps_breakdown"] else {},
            "flagged": r["flagged"],
            "analyzed_at": r["analyzed_at"].isoformat() if r["analyzed_at"] else None,
        }
        for r in rows
    ]


@app.get("/api/troll-scores/{patent_id}")
async def get_troll_score_detail(patent_id: int):
    """Detailed TPS breakdown for a specific patent."""
    row = await pool.fetchrow(
        """SELECT id, application_num, title, filing_date, inventor_name, assignee,
                  cpc_codes, claims_text, abstract_text,
                  tps_score, tps_breakdown, flagged, analyzed_at
           FROM patent_filings WHERE id = $1""",
        patent_id,
    )
    if not row:
        return JSONResponse(status_code=404, content={"error": "Patent not found"})

    return {
        "id": row["id"],
        "application_num": row["application_num"],
        "title": row["title"],
        "filing_date": row["filing_date"].isoformat() if row["filing_date"] else None,
        "inventor_name": row["inventor_name"],
        "assignee": row["assignee"],
        "cpc_codes": row["cpc_codes"],
        "claims_text": (row["claims_text"] or "")[:2000],
        "abstract_text": row["abstract_text"],
        "tps_score": row["tps_score"],
        "tps_breakdown": json.loads(row["tps_breakdown"]) if row["tps_breakdown"] else {},
        "flagged": row["flagged"],
        "analyzed_at": row["analyzed_at"].isoformat() if row["analyzed_at"] else None,
    }


@app.post("/api/prior-art")
@limiter.limit("20/hour")
async def get_prior_art(request: Request):
    """Generate prior art search links for a flagged patent."""
    body = await request.json()
    patent_id = body.get("patent_id")

    if patent_id is None:
        return JSONResponse(status_code=400, content={"error": "patent_id is required"})

    row = await pool.fetchrow(
        """SELECT application_num, title, claims_text, abstract_text
           FROM patent_filings WHERE id = $1""",
        int(patent_id),
    )
    if not row:
        return JSONResponse(status_code=404, content={"error": "Patent not found"})

    refs = generate_prior_art_links(
        patent_title=row["title"] or "",
        claims_text=row["claims_text"] or "",
        abstract_text=row["abstract_text"] or "",
    )

    package = generate_defense_package(
        patent_title=row["title"] or "",
        patent_number=row["application_num"],
        claims_text=row["claims_text"] or "",
        abstract_text=row["abstract_text"] or "",
        prior_art_refs=refs,
    )

    return package


@app.get("/api/troll-stats")
async def get_stats():
    """System statistics for the dashboard."""
    total = await pool.fetchval("SELECT COUNT(*) FROM patent_filings")
    flagged = await pool.fetchval("SELECT COUNT(*) FROM patent_filings WHERE flagged = TRUE")
    checks = await pool.fetchval("SELECT COUNT(*) FROM troll_checks")
    avg_tps = await pool.fetchval("SELECT COALESCE(AVG(tps_score), 0) FROM patent_filings")
    highest_tps = await pool.fetchval("SELECT COALESCE(MAX(tps_score), 0) FROM patent_filings")

    return {
        "patents_monitored": total,
        "patents_flagged": flagged,
        "checks_performed": checks,
        "avg_tps_score": round(float(avg_tps), 1),
        "highest_tps_score": round(float(highest_tps), 1),
        "system_status": "operational",
        "patent_app_number": "64/020,008",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
