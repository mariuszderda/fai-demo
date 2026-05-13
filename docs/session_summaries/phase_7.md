# Phase 7 · Deployment and defense docs · session summary

## What was built

- Added a production deployment stack for the GCP VM target: `docker-compose.prod.yml`, nginx reverse proxy config, and Let’s Encrypt TLS wiring.
- Added `frontend/Dockerfile.prod` to build the React app with `VITE_API_BASE=""` and copy the static bundle into a shared Docker volume for nginx to serve.
- Updated the backend runtime image so it bootstraps the MITRE dataset at startup, binds Uvicorn to `0.0.0.0:8080`, and exposes the internal API only through nginx.
- Added `.env.production.example` with the real production variables and the HTTPS CORS origin for `fai.mariuszderda.pl`.
- Added deployment and certificate renewal scripts under `scripts/` for a fresh Ubuntu VM.
- Replaced the README with a full operator guide covering local development, production deployment, architecture, course mapping, tests, and build-time decisions.
- Added a comprehensive `DEMO.md` with the Polish intro script, click-through steps for ransomware and phishing, recovery notes, and Q&A.
- Updated the backend CORS default and the frontend API base fallback so production builds use same-origin relative API URLs behind nginx.
- Expanded CI to validate backend bootstrap/lint/type/tests and frontend typecheck/build on push and pull requests.

## How to verify

```bash
cd backend && pytest -v
```

```bash
cd frontend && npm run typecheck && npm run build
```

```bash
docker compose -f docker-compose.prod.yml build
```

```bash
docker compose -f docker-compose.prod.yml up -d
```

```bash
nginx -t -c /path/to/fai/nginx/nginx.conf
```

## Decisions taken during the phase

- Used nginx as the TLS terminator and reverse proxy so the public VM exposes only ports 80 and 443, while the backend remains private on the Docker network.
- Built the frontend as a static asset bundle copied into a named Docker volume instead of running a long-lived Node container in production.
- Kept the production API base empty so the browser talks to the same origin and nginx proxies `/api/...` to the backend.
- Added healthchecks for backend, frontend asset copy, and nginx so `docker compose ps` can show healthy services before the defense.
- Kept the deployment script simple and reproducible for a fresh Ubuntu VM, with an explicit first-run certificate acquisition flow.
- Preserved the existing dev compose path instead of replacing it, because the defense-specific deployment story is now handled by `docker-compose.prod.yml`.
- Documented the local frontend dev requirement to set `VITE_API_BASE=http://localhost:8080` explicitly, since the production default is now relative URLs.

## Known gaps / follow-ups for later phases

- No automated cloud provisioning was added; the operator still performs the actual GCP VM setup manually.
- The deployment script assumes a cloned git repository and a writable working tree for the temporary certbot nginx config swap.
- Cert renewal is documented via cron, but the cron job itself must still be installed by the operator on the VM.

## Files created or modified

- `backend/Dockerfile`
- `backend/fai/config.py`
- `frontend/src/lib/api.ts`
- `frontend/Dockerfile.prod`
- `docker-compose.prod.yml`
- `nginx/nginx.conf`
- `nginx/conf.d/default.conf`
- `.env.production.example`
- `scripts/deploy.sh`
- `scripts/renew-cert.sh`
- `.github/workflows/ci.yml`
- `README.md`
- `DEMO.md`
- `docs/session_summaries/phase_7.md`

