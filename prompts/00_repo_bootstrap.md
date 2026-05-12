# [Bootstrap] Repo skeleton, MITRE dataset, demo scenarios

> **Phase 1 of 7 · Bootstrap**
>
> This file is read by GitHub Copilot Agent Mode in IntelliJ as part of
> the FAI build. To start this phase, open Copilot Chat in IntelliJ,
> switch to Agent mode (not Ask mode), and paste the prompt below.

## Agent Mode Prompt — copy and paste this into Copilot Chat

```
You are working in agent mode on Phase 1 of the Forensics AI (FAI) project.

Read `AGENTS.md` at the repo root first — treat it as hard constraints.

Then read the full spec for this phase at `prompts/00_repo_bootstrap.md` and execute it end-to-end.

The goal of this phase is: set up the repository skeleton (backend + frontend directory trees, configuration files, Docker stubs), download MITRE ATT&CK v14 dataset, and generate deterministic demo data files for the ransomware and phishing scenarios. NO application logic in this phase — just scaffolding.

When you are done, run the verification checklist in the spec's "How to verify" section, then summarize what you built and any decisions you took. Do not start Phase 2 — stop and wait for me to review.
```

---

## Full specification

The rest of this document is the detailed spec the agent will read from
disk after you send the prompt above. You don't need to copy it — the
agent will open this file itself.


## Goal

Set up the repository skeleton, fetch the MITRE ATT&CK Enterprise v14
dataset, and generate the two demo scenario data bundles (ransomware
and phishing). After this phase is complete, subsequent issues can build
on a stable file layout.

**Do not write any application logic in this phase.** Only scaffolding,
configuration, data files, and the bootstrap script.

## Scope

### 1. Top-level files

Create these files at the repo root:

- `.gitignore` — Python, Node, IDE, plus:
  ```
  runtime/
  backend/.env
  data/mitre/enterprise-attack.json
  *.pyc
  __pycache__/
  node_modules/
  dist/
  .vite/
  ```
- `scripts/bootstrap.sh` — bash script that:
  - Creates `runtime/artifacts`, `runtime/audit`, `runtime/reports`.
  - Downloads MITRE ATT&CK Enterprise v14 JSON from
    `https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json`
    into `data/mitre/enterprise-attack.json` if not already present.
  - Verifies the file is valid JSON and contains at least one
    technique object (`type == "attack-pattern"`).
  - Exits non-zero on any failure with a clear error message.
- `README.md` — minimal placeholder. One sentence project description,
  a "build status" note saying "in active development", and a line
  pointing readers at `DEMO.md` (will be created in Phase #7).
- `docker-compose.yml` — placeholder with two services (`backend`,
  `frontend`) defined but each pointing at a Dockerfile that does not
  exist yet. Use `build:` directives, not `image:`. Networks default.
  Backend on 8080, frontend on 5173.

### 2. Backend skeleton

- `backend/pyproject.toml` with:
  - `[project]` block, name `fai`, version `0.1.0`, Python `>=3.11`.
  - Dependencies pinned to recent stable: `fastapi`, `uvicorn[standard]`,
    `pydantic>=2`, `pydantic-settings`, `httpx`, `structlog`,
    `anthropic>=0.40`, `jinja2`, `markdown-it-py`, `python-multipart`.
  - Dev dependencies: `pytest`, `pytest-asyncio`, `ruff`, `mypy`.
  - `[tool.ruff]` config: line-length 100, target Python 3.11.
  - `[tool.pytest.ini_options]` config: `asyncio_mode = "auto"`,
    `testpaths = ["tests"]`.
- `backend/.env.example` with all env vars from AGENTS.md §7, each
  with a comment.
- `backend/Dockerfile` — multi-stage build with Python 3.11-slim,
  installs dependencies, copies source, runs `uvicorn fai.app:app
  --host 0.0.0.0 --port 8080`. Bootstrap script copied in and run
  before the app starts (so MITRE dataset is present in container).
- `backend/fai/__init__.py` — empty.
- `backend/fai/app.py` — minimal FastAPI app with a `GET /healthz`
  endpoint returning `{"status": "ok"}` and CORS middleware configured
  from `CORS_ORIGINS` env var.
- `backend/fai/config.py` — `pydantic-settings` `Settings` class with
  all env vars from AGENTS.md §7. Read once via `lru_cache`.
- `backend/tests/__init__.py` — empty.
- `backend/tests/test_healthz.py` — single test verifying `GET /healthz`
  returns 200 and the expected body. Use `httpx.AsyncClient` with
  `ASGITransport`.

### 3. Frontend skeleton

Use Vite's `react-ts` template as a starting point, then customize.

- `frontend/package.json` with these dependencies (latest stable):
  - `react`, `react-dom`, `react-router-dom`,
  - `@tanstack/react-query`,
  - `tailwindcss`, `postcss`, `autoprefixer`,
  - `clsx`, `tailwind-merge`,
  - `lucide-react`,
  - `react-markdown`, `remark-gfm`,
  - and the shadcn/ui Radix primitives that will be installed in Issue
    #5 (do not install them yet — they will come via `npx shadcn` then).
- `frontend/vite.config.ts` — React plugin, `@` alias to `./src`.
- `frontend/tsconfig.json` — strict mode, path alias for `@`.
- `frontend/tailwind.config.ts` — content paths, dark mode `'class'`,
  theme extends `colors` with CSS variable references for every token
  in AGENTS.md §5 (e.g. `'bg-base': 'var(--bg-base)'`).
- `frontend/postcss.config.js` — standard Tailwind setup.
- `frontend/index.html` — minimal, `<html lang="pl">`, `<title>FAI ·
  Konsola Analityka</title>`, loads Google Fonts: JetBrains Mono
  (weights 400, 600, 700) and Inter Tight (weights 400, 500, 600)
  via `<link rel="preconnect">` + stylesheet.
- `frontend/src/styles/globals.css` — Tailwind directives, CSS variables
  on `:root` exactly as in AGENTS.md §5, base typography rules.
- `frontend/src/main.tsx` — mounts a placeholder `App` component.
- `frontend/src/App.tsx` — for now, just renders `<div className="bg-base
  text-text-primary min-h-screen font-mono p-8">FAI · skeleton ready</div>`.
- `frontend/Dockerfile` — multi-stage: Node 20 build stage runs
  `npm ci` and `npm run build`, then nginx-alpine serves the `dist/`
  with a SPA-friendly config (fallback to `index.html`). For dev,
  `docker-compose.yml` will override with the Vite dev server command;
  prod-style build is fine here.

### 4. Demo data — ransomware scenario

Create `data/scenarios/ransomware/`:

- `alert.json` — a SIEM-style alert object. Suggested shape:
  ```json
  {
    "alert_id": "SIEM-RW-2026-0511-001",
    "severity": "high",
    "host": "victim-vm-01",
    "host_os": "Ubuntu 22.04",
    "detected_at_utc": "2026-05-11T08:14:22Z",
    "rule": "MASS_FILE_RENAME + UNUSUAL_OUTBOUND_443",
    "summary": "Mass file renaming with .locked extension and outbound traffic to non-categorized domain on port 443"
  }
  ```
- `syslog.log` — ~1500 lines. Mostly benign Linux syslog content
  (cron, sshd, systemd messages). Sprinkle in these signals at
  plausible timestamps:
  - One `wget` call fetching a payload from `203.0.113.47`.
  - Many file rename operations to `.locked` extension.
  - A process `cryptdaemon` spawning.
  - Outbound connections to `c2-relay.evil-corp-demo.test` on 443.
- `processes.json` — `ps`-style listing as a JSON array of objects.
  Include `cryptdaemon`, `python3 /tmp/x.py`, and normal background
  processes (init, sshd, systemd-resolve, dbus-daemon, etc.).
- `netstat.json` — list of outbound connections. Two to
  `c2-relay.evil-corp-demo.test:443`, rest benign.
- `tmp_files/README.txt` — a Polish ransom note ("Twoje pliki zostały
  zaszyfrowane. Aby je odzyskać, skontaktuj się: support@evil-corp-demo.test.
  Identyfikator ofiary: VC-9912.").
- `tmp_files/file1.locked`, `file2.locked`, `file3.locked`,
  `file4.locked` — small files of pseudo-random bytes (use Python's
  `random.seed(42)` in the generator so bytes are stable).

### 5. Demo data — phishing scenario

Create `data/scenarios/phishing/`:

- `alert.json` — medium severity, analyst workstation, summary mentions
  suspicious email click.
- `email_headers.eml` — RFC822 headers (no body needed) showing:
  - `Subject: Faktura zaległa #4471 — pilna płatność`
  - `From: ksiegowosc@evil-corp-demo.test`
  - `Return-Path: <noreply@bounce.evil-corp-demo.test>`
  - `Authentication-Results: spf=fail smtp.mailfrom=evil-corp-demo.test; dkim=none`
  - Plausible Received headers chain.
- `dns_queries.log` — text log of DNS queries from the host. Include
  one query to `faktury-online.evil-corp-demo.test` (typosquat).
- `browser_history.json` — JSON array of browser history entries.
  Include a click on `https://faktury-online.evil-corp-demo.test/download/faktura.exe`.
- `payload_sample.txt` — text describing the payload found on disk:
  filename `faktura.exe`, fake SHA-256 hash (generated with the same
  fixed seed), file size, MIME-type. **Not** an actual executable.

### 6. MISP fallback fixtures

Create `data/misp_fallback.json`. Keyed by IoC value. Cover **every**
IoC the stub LLM (which will be implemented in Phase #3) is expected
to extract from both scenarios. Each entry shape:

```json
{
  "203.0.113.47": {
    "reputation": "malicious",
    "first_seen": "2025-12-03T11:02:18Z",
    "last_seen": "2026-05-10T22:47:09Z",
    "related_campaigns": ["LockedFiles2025"]
  },
  ...
}
```

For now, include entries for at least these IoC values:
- `203.0.113.47` (ransomware payload host) — malicious
- `c2-relay.evil-corp-demo.test` (ransomware C2) — malicious
- `evil-corp-demo.test` (phishing sender domain) — malicious
- `faktury-online.evil-corp-demo.test` (typosquat) — malicious
- the SHA-256 of the fake `faktura.exe` — malicious
- one clean-reputation domain for contrast (e.g. `legitimate-bank.example`) — clean

### 7. Generator script

Write `data/_generate.py` — a one-shot Python script that produces the
scenario files deterministically (`random.seed(42)`). Run it once
in this phase, commit the output. The script stays in the repo so
the data can be regenerated by `python data/_generate.py` if needed.

### 8. CI smoke

Add `.github/workflows/ci.yml` running on push:
- `cd backend && pip install -e .[dev] && pytest && ruff check .`
- `cd frontend && npm ci && npm run build`

It is OK if frontend build only produces the placeholder page at this
stage — we just want CI green from the start.

## How to verify

After merging:
- `bash scripts/bootstrap.sh` exits 0, MITRE JSON appears at
  `data/mitre/enterprise-attack.json`.
- `cd backend && pip install -e .[dev] && pytest -v` → 1 test passes
  (`test_healthz`).
- `cd backend && ruff check .` → 0 errors.
- `cd frontend && npm ci && npm run build` → succeeds.
- `docker compose build` → both images build.
- `ls data/scenarios/ransomware data/scenarios/phishing` → all expected
  files present.
- `python -c "import json; print(len(json.load(open('data/misp_fallback.json'))))"` ≥ 5.

## Out of scope for this phase

- All application logic (FR-1 through FR-12) — comes in later issues.
- shadcn/ui component installation — comes in Phase #5.
- Any UI beyond the placeholder div — comes in Issues #5 and #6.

## References

- AGENTS.md §3 (repo layout), §4 (coding standards), §7 (config),
  §11 (demo data conventions).
