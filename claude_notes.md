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
- **Stack**: Hugo static site → nginx (Docker)
- **Container**: `seattlewren-hugo-dev` (port 9247)
- **Hugo version**: 0.147.2 (via `hugomods/hugo` Docker image)
- **Domain**: jonnywren.com → Cloudflare Tunnel → localhost:9247
- **baseURL**: Set to `"/"` (relative paths) in `hugo.toml`

## Docker Setup
- **Dockerfile**: Multi-stage build in `/home/u49382/seattlewren-prod/Dockerfile`
  - Stage 1: `hugomods/hugo:0.147.2` builds the site with `hugo --minify`
  - Stage 2: `nginx:alpine` serves the built `/public` directory
- Both `Dockerfile` and `autodeploy.sh` are in `.gitignore` (local to this machine only)

### Manual rebuild command:
```bash
docker build -t seattlewren-hugo-dev . && docker rm -f seattlewren-hugo-dev && docker run -d --name seattlewren-hugo-dev --restart unless-stopped -p 9247:80 seattlewren-hugo-dev
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

## Git
- **Repo**: https://github.com/Wrenegade/seattlewren-prod.git
- **Branch**: main
- `.gitignore` includes: `Dockerfile`, `autodeploy.sh`, `public/`, `.hugo_build.lock`

## Other Containers on This Box
| Container | Port | Purpose |
|---|---|---|
| diary-frontend | 8081 | Diary app |
| diary-backend | 5000 | Diary API |
| home-inventory-frontend | 8082 | Home inventory app |
| home-inventory-backend | 5001 | Home inventory API |
| seattle-wren-frontend | 8083 | SeattleWren prod (React) |
| seattle-wren-backend | internal | SeattleWren prod API |
| seattlewren-hugo-dev | 9247 | SeattleWren Hugo dev |
| mypostgres | 5432 | Shared PostgreSQL |
| homeassistant | 8123 | Home Assistant |
