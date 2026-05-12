# Phase 1 · Bootstrap · session summary

## What was built
- Created the repository skeleton for backend, frontend, data, scripts, runtime, and CI workflow support.
- Added the backend scaffold: `pyproject.toml`, `.env.example`, Dockerfile, FastAPI health endpoint, typed config, and an async test.
- Added the frontend scaffold: Vite React + TypeScript shell, Tailwind/PostCSS setup, Google Fonts, Dockerfile, and placeholder app UI.
- Added `scripts/bootstrap.sh` to create runtime directories and download + validate MITRE ATT&CK Enterprise v14 locally.
- Added `data/_generate.py` and generated deterministic ransomware/phishing fixtures plus `data/misp_fallback.json`.
- Added `.github/workflows/ci.yml` for backend and frontend smoke CI.
- Added `docs/session_summaries/phase_1.md` as required by `AGENTS.md`.

## How to verify
```bash
bash scripts/bootstrap.sh
```

```bash
cd backend && python3 -m venv /tmp/fai-backend-venv && /tmp/fai-backend-venv/bin/pip install -e ".[dev]" --ignore-requires-python && /tmp/fai-backend-venv/bin/pytest -v && /tmp/fai-backend-venv/bin/ruff check .
```

```bash
cd frontend && npm ci && npm run build
```

```bash
docker compose build
```

```bash
cd .. && ls data/scenarios/ransomware data/scenarios/phishing
```

```bash
cd .. && python3 -c "import json; print(len(json.load(open('data/misp_fallback.json'))))"
```

## Decisions taken during the phase
- Kept `data/mitre/enterprise-attack.json` out of git history via `.gitignore`; the downloaded file is 45 MB locally and is meant to be bootstrapped on demand.
- Generated the frontend lockfile with `npm install --prefix frontend` so the CI `npm ci` step is reproducible.
- Added extra MISP fallback entries beyond the minimum so the obvious IoCs in both demo scenarios are covered.

## Known gaps / follow-ups for later phases
- No application logic beyond `/healthz` exists yet.
- The frontend remains a placeholder shell until the later UI phases.
- Docker images are scaffolded only; runtime behavior will be implemented in later phases.

## Files created or modified
- `.gitignore`
- `README.md`
- `docker-compose.yml`
- `scripts/bootstrap.sh`
- `.github/workflows/ci.yml`
- `backend/pyproject.toml`
- `backend/.env.example`
- `backend/Dockerfile`
- `backend/setup.py`
- `backend/fai/__init__.py`
- `backend/fai/app.py`
- `backend/fai/config.py`
- `backend/tests/__init__.py`
- `backend/tests/test_healthz.py`
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/vite.config.ts`
- `frontend/tsconfig.json`
- `frontend/tailwind.config.ts`
- `frontend/postcss.config.js`
- `frontend/index.html`
- `frontend/src/styles/globals.css`
- `frontend/src/main.tsx`
- `frontend/src/App.tsx`
- `frontend/Dockerfile`
- `data/_generate.py`
- `data/misp_fallback.json`
- `data/scenarios/ransomware/*`
- `data/scenarios/phishing/*`

