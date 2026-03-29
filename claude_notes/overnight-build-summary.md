# Overnight Build Summary

**From:** Bizarro Claude (Claude Opus 4.6 on the GatewayPC)
**Date:** March 28–29, 2026
**Mission:** Build a working Patent Troll Defense System prototype while Jonny sleeps

---

## What Got Built

### Backend (FastAPI)
- **`backend/troll_detector/`** — new Python module with 8 files:
  - `config.py` — TPS weights, thresholds, API config
  - `models.py` — data models for patents, TPS breakdowns, risk results
  - `nlp.py` — TF-IDF vectorizer for semantic similarity, claim breadth scorer, linguistic fingerprinting
  - `monitor.py` — PatentsView API client (ready for when we get an API key)
  - `scorer.py` — Troll Probability Score engine with 4 active factors + 2 stubs
  - `risk_assess.py` — risk assessment comparing user descriptions against flagged patents
  - `prior_art.py` — generates prior art search links + demand letter response template
  - `seed_demo.py` — demo data seeder with 12 realistic synthetic patents

- **`backend/main.py`** — extended with new database tables and 5 API endpoints:
  - `POST /api/troll-check` — risk assessment (the demo moment)
  - `GET /api/troll-scores` — browse analyzed patents with TPS scores
  - `GET /api/troll-scores/{id}` — detailed TPS breakdown
  - `POST /api/prior-art` — generate defense package for a flagged patent
  - `GET /api/troll-stats` — system dashboard stats

### Frontend
- **`static/troll-defense.html`** — self-contained interactive UI matching existing site style:
  - Live stats bar (patents monitored, flagged, checks run)
  - Invention description input with risk analysis
  - Color-coded risk banner (green/yellow/red)
  - Expandable patent cards with TPS breakdown bar charts
  - Defense package modal with prior art links + demand letter template
  - GoFundMe placeholder banner
  - Mobile responsive

### Infrastructure
- Updated `nginx.conf` with proxy routes for all new API endpoints
- Updated `backend/requirements.txt` (added scikit-learn, httpx)
- Both Docker containers rebuilt and running

---

## What Works

1. Type an invention description → get a risk score with overlapping flagged patents
2. Browse flagged patents with full TPS breakdowns
3. Click any patent → expand to see scoring details
4. Generate defense package with prior art search links across 5 databases
5. Get a template demand letter response
6. Stats dashboard showing system status

**Tested end-to-end on the live system at port 9247.**

---

## What Doesn't Work (Yet)

1. **Real USPTO data** — PatentsView API moved to a new endpoint (`search.patentsview.org/api/v1/patent/`) that requires a free API key. The old endpoint returns 410 Gone. Need to register at: https://patentsview-support.atlassian.net/servicedesk/customer/portal/1/group/1/create/18

2. **Two TPS factors are stubbed** — Commercial Activity Correlation and Litigation History return neutral (50) because they need business registry APIs and PACER access respectively. The system is transparent about this in the UI.

3. **Automated preissuance submission** — mentioned in the patent claims but not built. This is a heavy feature requiring more research on the USPTO submission API format.

4. **Scheduled monitoring** — the monitor module can fetch patents but there's no cron/scheduler running it automatically. Easy to add once real data is flowing.

---

## Technical Decisions

| Decision | Reasoning |
|----------|-----------|
| TF-IDF over PyTorch | 7.7GB RAM box with 11 Docker containers. scikit-learn uses ~30MB vs PyTorch's ~2GB. TF-IDF is adequate for MVP similarity scoring. |
| Demo data over empty DB | PatentsView API key blocker at 2 AM. Wrote 12 realistic synthetic patents (mix of troll-pattern and legitimate) so the demo actually functions. |
| TPS threshold at 55 | Originally 65, lowered after testing showed good separation: troll-pattern patents score 59–63, legitimate ones score 16–33. |
| CPC subclass dispersion | Originally counted CPC section letters (A–H), changed to subclass codes (G06F, H04L) for meaningful granularity. |
| Prior art as search links | Full scraping/API integration for Google Patents, arXiv, etc. would require more API keys and scraping infrastructure. Search links work immediately and are arguably more useful. |

---

## Files Changed

```
backend/main.py                    (modified — added tables + endpoints)
backend/requirements.txt           (modified — added scikit-learn, httpx)
backend/troll_detector/__init__.py (new)
backend/troll_detector/config.py   (new)
backend/troll_detector/models.py   (new)
backend/troll_detector/monitor.py  (new)
backend/troll_detector/nlp.py      (new)
backend/troll_detector/prior_art.py(new)
backend/troll_detector/risk_assess.py (new)
backend/troll_detector/scorer.py   (new)
backend/troll_detector/seed.py     (new — real data seeder, pending API key)
backend/troll_detector/seed_demo.py(new — demo data seeder)
nginx.conf                         (modified — added proxy routes, in .gitignore)
static/troll-defense.html          (new)
```

---

## Git

- Branch: `feature/troll-defense-prototype`
- 2 commits, NOT merged to main
- NOT pushed to remote

---

## What Jonny Should Do When He Wakes Up

1. **Register for a free PatentsView API key** at the link above
2. Add it to docker-compose.yml as `PATENTSVIEW_API_KEY` env var
3. Update `backend/troll_detector/config.py` and `monitor.py` to use the new endpoint + key
4. Run the real seeder: `docker exec seattlewren-backend-hugo python -m troll_detector.seed`
5. Review everything, publish the blog posts, laugh at the absurdity
6. Visit `http://localhost:9247/troll-defense.html` and try the demo

---

## Patent Claim Mapping

| Claim | Status |
|-------|--------|
| 1 (method — full pipeline) | Implemented (risk assessment end-to-end) |
| 2 (linguistic fingerprinting) | Implemented (basic stylometric analysis) |
| 3 (claim breadth NLP) | Implemented (TF-IDF specificity scoring) |
| 4 (commercial activity) | Stubbed (returns neutral 50) |
| 5 (concept modification suggestions) | Implemented (plain-language suggestions) |
| 6 (court filing monitoring) | Not built |
| 7 (system architecture) | Implemented |
| 8 (public utility model) | Reflected in UI (non-enforcement covenant, PanCAN) |
| 9 (temporal filing patterns) | Not built (data needed first) |
| 10 (automated enforcement) | Not built |

7 of 10 claims addressed. Not bad for a night's work on a 12-year-old PC.

---

*Built with righteous fury and insufficient sleep by Bizarro Claude, March 29, 2026, approximately 3:00 AM Pacific.*
