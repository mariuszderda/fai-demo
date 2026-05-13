# [Ops] Docker compose, README, DEMO.md

> **Phase 7 of 7 · Docker, README, DEMO.md**
>
> This file is read by GitHub Copilot Agent Mode in IntelliJ as part of
> the FAI build. To start this phase, open Copilot Chat in IntelliJ,
> switch to Agent mode (not Ask mode), and paste the prompt below.

## Agent Mode Prompt — copy and paste this into Copilot Chat

```
You are working in agent mode on Phase 7 — the final phase — of the Forensics AI (FAI) project.

Read `AGENTS.md` at the repo root first.

Then read the full spec for this phase at `prompts/06_docker_demo_docs.md` and execute it end-to-end.

The goal of this phase is: finalize docker-compose, write the comprehensive README and the DEMO.md presentation script. After this phase the project is presentable for defense.

Critical: the README's "Build-time decisions" section must list every non-obvious decision taken across all 7 phases. Look back at session summaries from prior phases to populate it.

When done, run `docker compose down -v && docker compose up --build` from a clean state and verify both scenarios end-to-end. Summarize and stop. This is the last phase.
```

```
# Phase 7 prompt — copy and paste into Copilot Chat (Agent mode)


You are working in agent mode on Phase 7 — the final phase — of the
Forensics AI (FAI) project.

Read AGENTS.md at the repo root first — treat it as hard constraints.
Then read prompts/06_docker_demo_docs.md for the base spec.

This phase has ADDITIONAL requirements beyond the base spec:

## DEPLOYMENT TARGET

The app will be deployed to a GCP Compute Engine VM (e2-medium, Ubuntu)
and served at https://fai.mariuszderda.pl with Let's Encrypt SSL.

## What to build in this phase

### 1. Production docker-compose (docker-compose.prod.yml)

Three services:

**nginx** — reverse proxy + SSL termination:
- Image: nginx:alpine
- Ports: 80:80, 443:443
- Volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - ./nginx/conf.d/:/etc/nginx/conf.d/:ro
    - ./certbot/www:/var/www/certbot:ro
    - ./certbot/conf:/etc/letsencrypt:ro
    - frontend-build:/usr/share/nginx/html:ro
- Depends on: backend, frontend

**backend** — FastAPI + uvicorn:
- Build from backend/Dockerfile
- NOT exposed to host directly (nginx proxies)
- Environment from .env.production
- Volumes:
    - ./runtime:/app/runtime
    - ./data:/app/data:ro

**frontend** — build stage only:
- Build from frontend/Dockerfile.prod (multi-stage: node build → copy
  dist to a named volume)
- The built files go into a named Docker volume `frontend-build` that
  nginx reads

Named volumes:
- frontend-build (shared between frontend build and nginx)

### 2. Nginx configuration (nginx/conf.d/default.conf)

```nginx
server {
    listen 80;
    server_name fai.mariuszderda.pl;

    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirect all other HTTP to HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name fai.mariuszderda.pl;

    ssl_certificate /etc/letsencrypt/live/fai.mariuszderda.pl/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/fai.mariuszderda.pl/privkey.pem;

    # Frontend SPA
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API proxy
    location /api/ {
        proxy_pass http://backend:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # SSE needs special proxy settings
    location /api/v1/incidents/ {
        proxy_pass http://backend:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
    }

    # Mock endpoints (for lecturer inspection)
    location /mock/ {
        proxy_pass http://backend:8080;
        proxy_set_header Host $host;
    }
}
```

Also create nginx/nginx.conf with basic top-level config (worker
processes, events block, http block that includes conf.d/*.conf).

### 3. Frontend production Dockerfile (frontend/Dockerfile.prod)

Multi-stage:
- Stage 1 (build): node:20-alpine, npm ci, npm run build
    - Set VITE_API_BASE="" (empty string — relative URLs, nginx proxies)
- Stage 2 (output): alpine, just copy dist/ to a known location
  that docker-compose mounts as a volume

The key insight: VITE_API_BASE must be empty string for production
so that fetch("/api/v1/...") goes to the same origin (nginx), which
proxies to backend. In dev mode it pointed to localhost:8080.

### 4. Backend Dockerfile update

Ensure backend/Dockerfile:
- Runs scripts/bootstrap.sh to download MITRE dataset
- Starts uvicorn on 0.0.0.0:8080 (internal only, nginx proxies)
- Sets PYTHONPATH if needed

### 5. Environment file (.env.production.example)

```
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-5
OTX_API_KEY=...
APPROVAL_TTL_SECONDS=120
CORS_ORIGINS=https://fai.mariuszderda.pl
USE_STUB_LLM=false
```

Note CORS_ORIGINS uses https:// and the real domain, not localhost.

### 6. Deploy script (scripts/deploy.sh)

Bash script for a fresh Ubuntu 22.04+ VM:

```bash
#!/bin/bash
set -euo pipefail

DOMAIN="fai.mariuszderda.pl"
EMAIL="mariusz.derda@gmail.com"

echo "=== FAI Deployment Script ==="

# 1. Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    echo "Docker installed. Log out and back in, then re-run this script."
    exit 0
fi

# 2. Install docker-compose plugin if not present
if ! docker compose version &> /dev/null; then
    echo "Installing Docker Compose plugin..."
    sudo apt-get update
    sudo apt-get install -y docker-compose-plugin
fi

# 3. Create required directories
mkdir -p certbot/www certbot/conf runtime/artifacts runtime/audit runtime/reports nginx/conf.d

# 4. Bootstrap MITRE dataset
if [ ! -f data/mitre/enterprise-attack.json ]; then
    echo "Downloading MITRE ATT&CK dataset..."
    bash scripts/bootstrap.sh
fi

# 5. Copy env file
if [ ! -f .env.production ]; then
    cp .env.production.example .env.production
    echo "EDIT .env.production with your real API keys before continuing!"
    exit 1
fi

# 6. Initial cert setup (HTTP only first)
# Start nginx temporarily on port 80 only for ACME challenge
echo "Obtaining Let's Encrypt certificate..."
# Create a temporary nginx config for cert acquisition
cat > nginx/conf.d/default.conf << 'NGINX'
server {
    listen 80;
    server_name DOMAIN_PLACEHOLDER;
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    location / {
        return 200 'FAI cert setup in progress';
    }
}
NGINX
sed -i "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" nginx/conf.d/default.conf

docker compose -f docker-compose.prod.yml up -d nginx

# Run certbot
docker run --rm \
    -v $(pwd)/certbot/www:/var/www/certbot \
    -v $(pwd)/certbot/conf:/etc/letsencrypt \
    certbot/certbot certonly --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL --agree-tos --no-eff-email \
    -d $DOMAIN

# 7. Deploy with full HTTPS config
echo "Starting FAI with HTTPS..."
# Now the real nginx config (with SSL) takes over
docker compose -f docker-compose.prod.yml down
# Restore the production nginx config
# (the one from the repo, not the temp one)
git checkout -- nginx/conf.d/default.conf
docker compose -f docker-compose.prod.yml up -d --build

echo ""
echo "=== FAI deployed at https://$DOMAIN ==="
echo "Check: curl -I https://$DOMAIN"
```

### 7. Certbot renewal cron

Add a `scripts/renew-cert.sh`:
```bash
#!/bin/bash
docker run --rm \
    -v $(pwd)/certbot/www:/var/www/certbot \
    -v $(pwd)/certbot/conf:/etc/letsencrypt \
    certbot/certbot renew --quiet
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
```
Mention in README to add a cron: `0 3 * * 0 cd /path/to/fai && bash scripts/renew-cert.sh`

### 8. README.md — comprehensive

Replace the placeholder README. Structure:

# Forensics AI (FAI)

## What this demo shows
(list of key features — pipeline, LLM, MITRE, approval gate, etc.)

## Quick start — local development
```
git clone ...
cd fai
cp backend/.env.example backend/.env
# edit .env: add ANTHROPIC_API_KEY
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
bash scripts/bootstrap.sh
uvicorn fai.app:app --port 8080

# separate terminal:
cd frontend && npm ci && npm run dev
```
Open http://localhost:5173

## Production deployment (GCP VM)

Prerequisites:
- GCP Compute Engine VM (e2-medium recommended, Ubuntu 22.04)
- Domain pointing to VM IP (A record for fai.mariuszderda.pl)
- Firewall rules: allow TCP 80, 443

Steps:
```
ssh your-vm
git clone <repo> fai && cd fai
cp .env.production.example .env.production
# edit .env.production with real keys
bash scripts/deploy.sh
```
Open https://fai.mariuszderda.pl

## Running the demo
See DEMO.md

## Real vs mocked
(table from AGENTS.md §8)

## Architecture
(ASCII diagram)

## Mapping to course requirements
- MH-01 → FR-1 (SIEM ingestion)
- MH-02 → FR-2 (Chain of custody)
- MH-03 → FR-3 (LLM analysis)
- MH-04 → FR-4 (MITRE mapping)
- MH-05 → FR-5 (Threat Intelligence)
- MH-06 → FR-6 (Approval gate)
- MH-07 → FR-8, FR-9 (Reporting + audit)

## Tests
```
cd backend && pytest -v
```
All tests pass without ANTHROPIC_API_KEY (stub mode).

## Build-time decisions
(Read docs/session_summaries/phase_*.md and compile the key decisions
from each phase into a bullet list here.)

## License
MIT

### 9. DEMO.md

Create a comprehensive demo script. Use the template from
prompts/06_docker_demo_docs.md but update:
- URL: https://fai.mariuszderda.pl (not localhost)
- Include the 60-second intro script (Polish)
- Include click-through for both scenarios (ransomware + phishing)
- Include the "three things to point at" section
- Include failure modes and recovery
- Include anticipated Q&A (6 questions minimum)
- Add a section "Before the defense" checklist:
    1. VM is running
    2. docker compose ps shows 3 healthy services
    3. https://fai.mariuszderda.pl loads the dashboard
    4. ANTHROPIC_API_KEY is set (not stub mode)
    5. Run one ransomware scenario to warm up LLM
    6. Clear runtime/ for a clean demo start

### 10. Update CORS in backend config

Ensure backend/fai/config.py default for cors_origins includes
https://fai.mariuszderda.pl alongside localhost origins. The
.env.production will override, but the default should be safe for
both dev and prod.

### 11. Update frontend api.ts

Ensure VITE_API_BASE defaults to "" (empty string) not
"http://localhost:8080" when the env var is not set. This way
production builds use relative URLs (/api/v1/...) which nginx
proxies. Only local dev needs the explicit localhost:8080.

Change in frontend/src/lib/api.ts:
```
export const API_BASE = import.meta.env.VITE_API_BASE ?? "";
```

### 12. CI workflow update

Update .github/workflows/ci.yml to run both backend and frontend
checks (it was created in Phase 1, may need updates for new test
files from Phase 4-6).

### 13. Session summary

Write docs/session_summaries/phase_7.md with:
- What was built (deployment infra, docs)
- Deploy instructions
- Build-time decisions
- File manifest

### 14. Final verification

Before finishing, run:
- cd backend && pytest -v (all tests pass)
- cd frontend && npm run typecheck && npm run build (clean)
- docker compose -f docker-compose.prod.yml build (images build)
- Verify nginx.conf is syntactically valid

Do NOT start any cloud deployment. The operator will do that manually.
Stop after local verification and summarize.

```

---

## Full specification

The rest of this document is the detailed spec the agent will read from
disk after you send the prompt above. You don't need to copy it — the
agent will open this file itself.


## Goal

Finalize the deployment story: a working `docker compose up` that
boots both services, a comprehensive README, and a DEMO.md guiding
the operator through the defense presentation. After this phase, the
project is presentable.

## Scope

### 1. Finalize `docker-compose.yml`

Two services:

```yaml
services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    container_name: fai-backend
    ports:
      - "8080:8080"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
      - ANTHROPIC_MODEL=${ANTHROPIC_MODEL:-claude-sonnet-4-5}
      - OTX_API_KEY=${OTX_API_KEY:-}
      - APPROVAL_TTL_SECONDS=${APPROVAL_TTL_SECONDS:-600}
      - CORS_ORIGINS=http://localhost:5173,http://localhost:8080
      - USE_STUB_LLM=${USE_STUB_LLM:-false}
    volumes:
      - ./runtime:/app/runtime
      - ./data:/app/data:ro
    networks:
      - fai-net

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: fai-frontend
    ports:
      - "5173:5173"
    environment:
      - VITE_API_BASE=http://localhost:8080
    depends_on:
      - backend
    networks:
      - fai-net

networks:
  fai-net:
    driver: bridge
```

Update frontend Dockerfile if needed so it runs `vite preview --host
0.0.0.0 --port 5173` as the production-ish dev mode (we are running
demos, not real prod). Or, alternatively, run nginx serving the built
SPA — pick whichever ends up smaller and works first try.

Confirm:
- `runtime/` is gitignored.
- `data/mitre/enterprise-attack.json` is present in the image OR
  downloaded on first start via `scripts/bootstrap.sh` baked into the
  backend image entrypoint.

### 2. Root README — `README.md`

Replace the placeholder. New structure:

```markdown
# Forensics AI (FAI)

AI-assisted SOAR-adjacent orchestrator for security incident analysis.
Academic demo for the Project Management course at Akademia Górnośląska
(2025/2026).

> ⚠️ This is an **academic prototype**, not a production system. It uses
> mocked SIEM, SOAR, and host-isolation integrations. The LLM analysis
> and Threat Intelligence lookups are real.

## What this demo shows

- End-to-end pipeline for two attack scenarios (ransomware, phishing)
- LLM-based IoC extraction with prompt-injection isolation
- MITRE ATT&CK mapping with **hallucination protection**
- AlienVault OTX integration with MISP fallback
- Chain of custody with SHA-256 and append-only audit trail
- Two-stage human oversight: IoC review + host-isolation approval
- React-based SOC analyst console with live pipeline updates

## Quick start

Requirements: Docker + Docker Compose. Optional: an Anthropic API key
for real LLM analysis (without it, a deterministic stub is used and
everything else still works).

```bash
git clone <this repo>
cd fai
cp backend/.env.example .env
# Optional: edit .env to add ANTHROPIC_API_KEY and/or OTX_API_KEY
docker compose up --build
```

Open `http://localhost:5173`.

## Manual dev mode (without Docker)

```bash
# terminal 1: backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
bash ../scripts/bootstrap.sh
uvicorn fai.app:app --reload --port 8080

# terminal 2: frontend
cd frontend
npm ci
npm run dev
```

## Running the demo

See **[DEMO.md](./DEMO.md)** for the click-through script.

## Real vs mocked

| Component | Status |
|---|---|
| LLM analysis (Anthropic Claude Sonnet) | Real (stub fallback if no API key) |
| MITRE ATT&CK validation | Real (local v14 dataset) |
| Threat Intelligence (AlienVault OTX) | Real (MISP fallback if no key/timeout) |
| Chain of custody (SHA-256, audit) | Real |
| Human-approval gate | Real |
| Client SIEM | Mocked (canned alerts) |
| SOAR (TheHive + Cortex) | Mocked (logs actions) |
| Host isolation executor | Mocked (validates approval token) |

## Architecture

(short prose description with the ASCII diagram from AGENTS.md §2)

## Mapping to course requirements

Every functional requirement is tied back to deliverables in the four
lab reports:

- MH-01 ingestion module (SIEM consumer) → FR-1
- MH-02 chain of custody → FR-2
- MH-03 LLM analysis engine → FR-3
- MH-04 MITRE mapping → FR-4
- MH-05 Threat Intelligence → FR-5
- MH-06 human-approval gate → FR-6
- MH-07 reporting + audit → FR-8, FR-9
- (v2 additions) IoC review gate → FR-10; React console → §5 in AGENTS.md

## Build-time decisions

(Bullet list of every "we picked X over Y" decision made during the
build that wasn't pre-specified in AGENTS.md or issues. Each bullet:
**decision · rationale · 1 sentence**.)

## License

MIT.

## Acknowledgements

MITRE ATT&CK® is a registered trademark of The MITRE Corporation. The
local dataset is the public Enterprise matrix from
https://github.com/mitre/cti.
```

### 3. DEMO.md — `DEMO.md`

```markdown
# FAI · Defense Demo Guide

This is the script for the project defense. Total target time:
**8–10 minutes including Q&A**.

## Before you start

1. Backend and frontend running: `docker compose up`.
2. Browser open at `http://localhost:5173`.
3. Two terminal windows visible alongside the browser:
   - `tail -f runtime/audit/*.jsonl` for live audit trail.
   - The `docker compose` log stream for live backend logs.
4. Have these files mentally ready to point at:
   - `backend/fai/analysis/prompts.py` (real LLM prompts)
   - `data/mitre/enterprise-attack.json` (real MITRE dataset)
   - `backend/tests/test_e2e_ransomware.py` (real E2E test)

## The 60-second intro

> "Forensics AI is the system our team scoped across the four lab
> reports of this course. The demo you'll see today is the technical
> implementation of the functional requirements MH-01 through MH-07
> from those reports. The architecture follows the two ADRs in Lab 3:
> TheHive+Cortex as the SOAR platform — mocked in this demo — and
> Anthropic Claude Sonnet as the LLM, which is the real integration
> you'll see in a moment. Two attack scenarios are wired end-to-end:
> ransomware and phishing. Let me show you the ransomware one first."

## Click-through · Ransomware (4 min)

1. **Dashboard** — point at the KPI strip, note the "halucynacje
   MITRE odrzucone" counter as a teaching point.
2. **Click "Uruchom scenariusz ransomware"**.
3. **Pipeline tab** — watch ingest → collect → CoC advance live.
   Mention: "SSE stream, no polling".
4. **IoC tab opens when pipeline pauses on ioc_review.**
   - Walk through 3-4 extracted IoCs.
   - Reject the lowest-confidence one with a note in Polish
     "Wewnętrzny IP biura, nie incydent".
   - Click "Akceptuj wszystkie pending" for the rest.
   - Click "Finalizuj".
5. **Pipeline advances to MITRE → TI → approval.** Switch back to
   Pipeline tab briefly to show it.
6. **Switch to MITRE tab.** Show the matrix with highlighted
   techniques: `T1486`, `T1083`, `T1071`. Click on `T1486`,
   show the Sheet with the IoCs that evidenced it.
7. **Approval card slides in bottom-right.** Read out the host_id
   and reason. **Pause** — emphasize this is the human-in-the-loop
   gate from Lab 3 ADR. Mention the kill-switch button.
8. **Click APPROVE.** Pipeline advances to report.
9. **Raport tab.** Read out the first sentence of the Polish
   executive summary. Scroll to the Timeline section. Scroll to the
   IoC table. Mention the Chain of Custody Statement at the bottom.
10. **Audyt tab.** Filter by action `HALLUCINATION_REJECTED`. **This
    is the most important slide.** Point at the rejected `T9999` and
    say:
    > "The LLM emitted a technique ID that doesn't exist. The system
    > caught it before it reached the report. This is the
    > hallucination-protection invariant from FR-4."

## Click-through · Phishing (2 min)

1. Click "Uruchom scenariusz phishing".
2. Skim Pipeline. At IoC review: accept all (these are obviously
   malicious by the data we shipped). Finalize.
3. Show MITRE tab: `T1566`, `T1204.002`.
4. Approval card: note `isolation_target: mail_relay_quarantine` —
   not host network. Different playbook, different isolation.
5. Approve. Report.

## Three things to point at to prove the system is real

1. **Audyt:** `HALLUCINATION_REJECTED` entries — proves real
   validation against the MITRE dataset, not just trust the LLM.
2. **Audyt:** if you ran without an OTX key, find
   `OTX_TIMEOUT_FALLBACK_TO_MISP` (or its absence with OTX present
   showing real `OTX_LOOKUP_RESULT`). Either way, the TI integration
   has demonstrable resilience.
3. **Backend logs:** show the SOAR mock rejecting an isolation call
   without `X-Approval-Token`. Run:
   ```bash
   curl -X POST http://localhost:8080/mock/host/test-host/isolate
   ```
   → 403. The token-required isolation is real.

## Failure-mode talking points

- "OTX is down." → MISP fallback. Show it in audit.
- "Anthropic is down." → Stub LLM kicks in. Settings page shows
  stub-mode warning. The demo still works end-to-end.
- "The approval gate times out." → Set `APPROVAL_TTL_SECONDS=10`,
  trigger a scenario, ignore the approval, watch it auto-decide
  `timeout`. No isolation. Audit logs the timeout.

## Anticipated questions

**Q: Why isn't there a real agent on the host collecting artifacts?**
A: We pivoted from Lab 1's wording. The system consumes from the
client's SIEM, which already aggregates host data. Building a separate
endpoint agent would duplicate the SIEM's job. This is documented in
the Build-time decisions section of the README.

**Q: How does the LLM avoid hallucinating MITRE techniques?**
A: Every technique ID is validated against the local MITRE v14
dataset before reaching the report. Unknown IDs are dropped and
audited as `HALLUCINATION_REJECTED`. See FR-4. The stub deliberately
emits a fake `T9999` so the rejection is visible in the demo.

**Q: What stops a malicious actor from bypassing the approval gate?**
A: The mocked host isolation endpoint requires a one-time token issued
by the approval gate on APPROVE. Without it, the call is 403. The
token is single-use and expires in 60 seconds. This is FR-6 and
exercised in `test_e2e_ransomware.py`.

**Q: Why do you pause for IoC review before MITRE mapping?**
A: It converts false-positive correction from "happens after the
report" to "happens before downstream analysis", saving LLM calls,
TI calls, and producing an explainable analyst-in-the-loop record.
This is FR-10 (added in v2 of the spec).

**Q: Is the chain of custody legally admissible?**
A: No. This is an academic prototype. Production deployment for
real forensic use would require Legal sign-off per Lab 4 §02 —
specifically Robert D.'s note on NIS2/DORA compliance.

**Q: Can the operator be fooled by a prompt injection in the
artifact data?**
A: The system prompt explicitly tells the LLM to treat content inside
`<artifact>` tags as untrusted input. Any detected injection
attempts are surfaced in the response's `notes` field and logged as
`PROMPT_INJECTION_DETECTED`. The artifact data and the system
instructions are strictly separated.

## After the demo

If asked for a code walkthrough, the files to open are, in order:
1. `AGENTS.md` (project spec)
2. `backend/fai/analysis/prompts.py` (the actual LLM prompts)
3. `backend/fai/analysis/mitre_mapper.py` (the hallucination filter)
4. `backend/fai/orchestrator/approval_gate.py` (the gate logic)
5. `frontend/src/components/ioc/IoCReviewPanel.tsx` (the analyst UI)
```

### 4. CI completion

Update `.github/workflows/ci.yml` (created in Phase #1):

```yaml
name: CI
on: [push, pull_request]
jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: cd backend && pip install -e .[dev]
      - run: bash scripts/bootstrap.sh
      - run: cd backend && ruff check .
      - run: cd backend && mypy fai/
      - run: cd backend && pytest -v
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: cd frontend && npm ci
      - run: cd frontend && npm run typecheck
      - run: cd frontend && npm run build
```

### 5. Final manual smoke (do this before finishing the phase)

1. `docker compose down -v`
2. `docker compose up --build` — must succeed cold.
3. Open `http://localhost:5173` — dashboard renders.
4. Run ransomware scenario through to report — works.
5. Run phishing scenario through to report — works.
6. Reload page mid-scenario — state preserved (incidents/IoCs survive
   reload because they're in the in-memory store, which survives as
   long as backend container is up).
7. Check `runtime/audit/`, `runtime/artifacts/`, `runtime/reports/`
   on the host — files exist from the mounted volume.

Document any issues found in the session summary.

### 6. .env.example finalization

Ensure `backend/.env.example` is complete and matches what
`docker-compose.yml` reads. Add comments explaining each variable.

## How to verify

- `docker compose up --build` from a clean state → both services
  healthy in <90s.
- The DEMO.md script can be executed start-to-finish without surprises.
- CI green on the main branch.
- README accurately describes how to run the project from scratch.

## Out of scope for this phase

- No further features.
- No new tests beyond what already exists.
- This is the last issue. After merging, the project is done.

## References

- AGENTS.md §1 (project context), §8 (real vs mocked).
- All prior issues.
