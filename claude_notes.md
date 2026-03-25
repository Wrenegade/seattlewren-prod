# Seattle Wren Hugo Dev Site — Claude Notes

## Machine: GatewayPC
- **OS**: Ubuntu 24.04.3 LTS (WSL2)
- **User**: u49382
- **Docker**: Running multiple containers

## What Lives Here
`/home/u49382/seattlewren-prod/` is a **Hugo** static site. This is the dev version of the new seattlewren.com, served via Docker + Cloudflare Tunnel at **jonnywren.com**.

The existing React/Vite app at `/home/u49382/seattlewren/` is the current **production** seattlewren.com — do NOT touch it.

## Architecture

### Production (seattlewren.com)
- **Source**: `/home/u49382/seattlewren/`
- **Stack**: React/Vite frontend + Node.js backend
- **Containers**: `seattle-wren-frontend` (port 8083), `seattle-wren-backend` (internal 5000)
- **Compose**: `docker-compose.prod.yml`
- **Database**: Shared postgres at `mypostgres` container (port 5432, db: `seattle_wren`)
- **Domain**: seattlewren.com → Cloudflare Tunnel → localhost:8083

### Dev / Hugo Site (jonnywren.com)
- **Source**: `/home/u49382/seattlewren-prod/`
- **Stack**: Hugo static site → nginx + FastAPI backend (Docker Compose)
- **Containers**: `seattlewren-hugo-dev` (port 9247), `seattlewren-backend-hugo` (internal 8000)
- **Compose**: `docker-compose.yml` (gitignored, local only)
- **Hugo version**: 0.147.2 (via `hugomods/hugo` Docker image)
- **Backend**: FastAPI — `POST /api/newsletter` and `POST /api/page-views`
- **Database**: Shared postgres at `mypostgres` via `host.docker.internal:5432` (db: `seattle_wren`)
- **Domain**: jonnywren.com → Cloudflare Tunnel → localhost:9247
- **baseURL**: Set to `"/"` (relative paths) in `hugo.toml`
- **Note**: Fully self-contained — no dependency on old React app containers

## Docker Setup
- **docker-compose.yml** (gitignored): Orchestrates `hugo` + `backend` services on a shared compose network
- **Dockerfile** (gitignored): Multi-stage Hugo build → nginx:alpine
- **backend/Dockerfile** (tracked): Python 3.12-slim + uvicorn
- **backend/main.py** (tracked): FastAPI app with newsletter + page view endpoints
- Gitignored deploy files: `Dockerfile`, `docker-compose.yml`, `nginx.conf`, `autodeploy.sh`

### Manual rebuild command:
```bash
cd /home/u49382/seattlewren-prod && docker compose up -d --build
```

## Auto-Deploy
- **Script**: `/home/u49382/seattlewren-prod/autodeploy.sh`
- **Systemd service**: `seattlewren-autodeploy` (user-level)
- **How it works**: Polls GitHub (`Wrenegade/seattlewren-prod`, branch `main`) every 30 seconds. On new commits, pulls and rebuilds the Docker container.
- **Linger enabled**: Service survives logout/reboot.

### Useful commands:
```bash
systemctl --user status seattlewren-autodeploy   # check status
journalctl --user -u seattlewren-autodeploy -f   # watch deploy logs
systemctl --user restart seattlewren-autodeploy   # restart
```

## Cloudflare Tunnel
- **Tunnel ID**: `43a4b5eb-3454-4ee5-8747-989de8f9ed6b`
- **Config**: `/home/u49382/.cloudflared/config.yml`
- **Cert**: `/home/u49382/.cloudflared/cert.pem` (authorized for seattlewren.com zone only)
- **Service**: `cloudflared` (user-level systemd)
- **Note**: The cert is scoped to seattlewren.com. DNS records for jonnywren.com were added manually in the Cloudflare dashboard (CNAME `@` and `www` → `43a4b5eb-3454-4ee5-8747-989de8f9ed6b.cfargotunnel.com`, proxied).

### Ingress routes:
| Hostname | Service |
|---|---|
| seattlewren.com | localhost:8083 (React prod) |
| www.seattlewren.com | localhost:8083 (React prod) |
| jonnywren.com | localhost:9247 (Hugo dev) |
| www.jonnywren.com | localhost:9247 (Hugo dev) |

### Restart tunnel:
```bash
systemctl --user restart cloudflared
```

## Theme Colors
- **Header / badges / tags**: British Racing Green `#2E4230` (light theme), `#3F5540` (dark theme badges)
- Original was `#2d3529` — shifted greener per user preference
- **Logo icon**: Placeholder wren SVG in header — user has their own image to replace it with later

## Homepage Categories
- **Fixed display order** in `layouts/index.html`: Musings, AI, Social, Data
- Order is defined via `$orderedCats` slice and `$catDisplay` dict (for proper casing like "AI")
- Categories not in the ordered list (e.g., General, Hobbies from templates) won't appear on the homepage
- **Latest sidebar** now skips the featured hero post (`after 1 | first 4`) to avoid duplication — the Trending fallback already did this

## Background Texture
- **Canvas/linen texture** applied to `body` in `layouts/_default/baseof.html`
- Image file: `static/bd7e52566_bg.jpg` (referenced as `/bd7e52566_bg.jpg`)
- CSS: `background-image`, `background-attachment: fixed`, `background-size: cover`, `background-position: center`
- Originally from the old seattlewren.com coming-soon page (Supabase-hosted), now self-hosted in static/

## About Page
- About image is set via front matter in `content/about/_index.md`
- Image source: `https://seattlewren.s3.us-west-2.amazonaws.com/about/hero.jpeg`

## Nav
- 🔥 emoji added before "Roast Me" link in header nav (`baseof.html` line ~1126)

## Archive
- `archive/` folder contains the old seattlewren React/Vite repo — gitignored, do not track

## Data Reports
- Each data report gets its own custom layout in `layouts/data/`
- Content files live in `content/data/` with `type: "data"` and a custom `layout` field
- **Existing reports**:
  - `economic-health` — County-level choropleth map (layout: `economic-health-map.html`)
  - `presidential-pardons` — Pardons by offense severity, 6 presidents, interactive bar chart (layout: `presidential-pardons.html`)
- Hero images hosted on S3: `https://seattlewren.s3.us-west-2.amazonaws.com/`
- Hero image generator utility: `hero-pardons-generator.html` (not tracked in git, local only)

## Git
- **Repo**: https://github.com/Wrenegade/seattlewren-prod.git
- **Branch**: main
- **Hosting/deploy**: Cloudflare (NOT Netlify — `netlify.toml` was removed)
- `.gitignore` includes: `Dockerfile`, `docker-compose.yml`, `autodeploy.sh`, `nginx.conf`, `public/`, `.hugo_build.lock`, `data/`, `archive/`

## Other Containers on This Box
| Container | Port | Purpose |
|---|---|---|
| diary-frontend | 8081 | Diary app |
| diary-backend | 5000 | Diary API |
| home-inventory-frontend | 8082 | Home inventory app |
| home-inventory-backend | 5001 | Home inventory API |
| seattle-wren-frontend | 8083 | SeattleWren prod (React) |
| seattle-wren-backend | internal | SeattleWren prod API |
| seattlewren-hugo-dev | 9247 | SeattleWren Hugo dev (nginx) |
| seattlewren-backend-hugo | internal | SeattleWren Hugo backend (FastAPI) |
| mypostgres | 5432 | Shared PostgreSQL |
| homeassistant | 8123 | Home Assistant |
