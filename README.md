# Forensics AI (FAI)

AI-assisted SOAR-adjacent orchestrator for security incident analysis.
Academic demo for the Project Management course at Akademia Górnośląska (2025/2026).

> ⚠️ This is an **academic prototype**, not a production system. It uses mocked SIEM, SOAR, and host-isolation integrations. The LLM analysis and Threat Intelligence lookups are real.

## What this demo shows

- End-to-end pipeline for two attack scenarios: ransomware and phishing
- LLM-based IoC extraction with prompt-injection isolation
- MITRE ATT&CK mapping with hallucination protection
- AlienVault OTX integration with MISP fallback
- Chain of custody with SHA-256 and append-only audit trail
- Two-stage human oversight: IoC review + host-isolation approval
- React-based SOC analyst console with live pipeline updates

## Quick start — local development

Requirements: Python 3.11+, Node 20+, and optionally Docker.

```bash
git clone <this repo>
cd fai
cp backend/.env.example backend/.env
# edit backend/.env and add ANTHROPIC_API_KEY if you want the real LLM
```

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
bash ../scripts/bootstrap.sh
uvicorn fai.app:app --host 0.0.0.0 --port 8080
```

Frontend (separate terminal):

```bash
cd frontend
npm ci
VITE_API_BASE=http://localhost:8080 npm run dev -- --host 0.0.0.0 --port 5173
```

Open http://localhost:5173.

If you prefer the simple containerized dev stack, the existing `docker-compose.yml` still serves the local demo on ports 8080 and 5173.

## Production deployment (GCP VM)

Deployment target:

- GCP Compute Engine `e2-medium`
- Ubuntu 22.04+ or similar
- Domain: `https://fai.mariuszderda.pl`
- TLS: Let's Encrypt via certbot + nginx

Prerequisites:

- VM reachable over SSH
- DNS A record pointing `fai.mariuszderda.pl` to the VM public IP
- Firewall rules allowing inbound TCP 80 and 443

Steps:

```bash
ssh your-vm
git clone <repo> fai
cd fai
cp .env.production.example .env.production
# edit .env.production with real API keys
bash scripts/deploy.sh
```

Open https://fai.mariuszderda.pl.

Cert renewal cron:

```cron
0 3 * * 0 cd /path/to/fai && bash scripts/renew-cert.sh
```

## Running the demo

See [`DEMO.md`](./DEMO.md) for the full click-through script.

## Real vs mocked

| Component | Status |
|---|---|
| LLM analysis (Anthropic Claude Sonnet) | Real, with deterministic stub fallback when no API key is present |
| MITRE ATT&CK validation | Real, against the local v14 Enterprise dataset |
| Threat Intelligence (AlienVault OTX) | Real, with MISP fallback if the key is missing or the lookup fails |
| Chain of custody (SHA-256, audit) | Real |
| Human-approval gate | Real |
| Client SIEM | Mocked, serves canned alerts and artifacts |
| SOAR (TheHive + Cortex) | Mocked, logs actions and returns case IDs |
| Host isolation executor | Mocked, validates the approval token before isolating |

## Architecture

```text
Browser
  │
  ▼
nginx :443
  ├── /                → React SPA from the named `frontend-build` volume
  ├── /api/            → FastAPI backend on backend:8080
  ├── /api/v1/incidents → SSE stream with special proxy settings
  └── /mock/           → Lecturer-visible mock SIEM/SOAR/host endpoints

backend:8080
  ├── reads runtime/ (artifacts, audit, reports)
  ├── reads data/ (scenarios, MITRE dataset, MISP fallback)
  └── coordinates analysis, approval, reporting, and audit
```

## Mapping to course requirements

- MH-01 → FR-1 (SIEM ingestion)
- MH-02 → FR-2 (Chain of custody)
- MH-03 → FR-3 (LLM analysis)
- MH-04 → FR-4 (MITRE mapping)
- MH-05 → FR-5 (Threat Intelligence)
- MH-06 → FR-6 (Approval gate)
- MH-07 → FR-8, FR-9 (Reporting + audit)

## Tests

```bash
cd backend && pytest -v
```

The backend tests pass without `ANTHROPIC_API_KEY` because the stub LLM is deterministic.

## Build-time decisions

- Kept the system database-free and stored all runtime state in memory plus the mounted `runtime/` directory, matching the project constraints and making the demo easy to reset.
- Used a deterministic stub LLM fallback that still emits the known demo IoCs and a fake `T9999` technique so the hallucination filter is visible during the defense.
- Chose FastAPI SSE for live pipeline updates instead of a separate SSE dependency, keeping the stack lightweight.
- Kept SIEM, SOAR, and host isolation as mocked routers under `/mock/...` so the lecturer can inspect the contracts without needing external infrastructure.
- Implemented the approval gate as a token-gated, single-use decision path with a TTL to make the human-in-the-loop control demonstrable and testable.
- Used local MITRE ATT&CK validation against the downloaded Enterprise v14 JSON instead of calling an external API, which keeps the demo reliable offline once bootstrapped.
- Stored chain-of-custody artifacts and audit trails on the mounted `runtime/` volume so the defense can inspect real filesystem outputs.
- Built the frontend for production as static files copied into a shared Docker volume and served by nginx, avoiding a separate Node runtime in production.
- Defaulted frontend production API calls to relative URLs so nginx can proxy `/api/...` to the backend on the same origin.
- Added a dedicated production compose file and nginx config so Let's Encrypt TLS termination is explicit and reproducible on the GCP VM.
- Preserved the existing dev compose workflow for local exploration, while documenting the explicit `VITE_API_BASE=http://localhost:8080` requirement for local frontend development.

## License

MIT.

## Acknowledgements

MITRE ATT&CK® is a registered trademark of The MITRE Corporation. The local dataset is the public Enterprise matrix from https://github.com/mitre/cti.

