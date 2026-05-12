# [Backend] Core primitives, mocks, audit trail

> **Phase 2 of 7 · Backend core**
>
> This file is read by GitHub Copilot Agent Mode in IntelliJ as part of
> the FAI build. To start this phase, open Copilot Chat in IntelliJ,
> switch to Agent mode (not Ask mode), and paste the prompt below.

## Agent Mode Prompt — copy and paste this into Copilot Chat

```
You are working in agent mode on Phase 2 of the Forensics AI (FAI) project.

Read `AGENTS.md` at the repo root first — treat it as hard constraints. The repository was scaffolded in Phase 1.

Then read the full spec for this phase at `prompts/01_backend_core.md` and execute it end-to-end.

The goal of this phase is: implement core backend primitives (Pydantic models, audit trail, chain of custody, SSE event bus), mock external systems (SIEM, SOAR, host isolation), and the SIEM consumer that pulls artifacts. No analysis logic and no HTTP API endpoints yet — those come in Phase 3 and Phase 4.

When done, run the verification checklist, then summarize. Do not start Phase 3.
```

---

## Full specification

The rest of this document is the detailed spec the agent will read from
disk after you send the prompt above. You don't need to copy it — the
agent will open this file itself.


## Goal

Implement the foundational backend modules: data models, audit trail,
chain of custody, mock external systems (SIEM, SOAR, host isolation),
and SIEM ingestion. After this phase is complete, the next issue can build
the analysis layer on top.

## Scope

### 1. Core data models — `backend/fai/core/models.py`

Pydantic v2 models for the entire system. Define:

- `IocType` — `Enum[str]` with values: `ipv4`, `ipv6`, `domain`, `url`,
  `md5`, `sha1`, `sha256`, `file_path`, `email`.
- `Confidence` — `Enum[str]` with values: `low`, `medium`, `high`.
- `IocStatus` — `Enum[str]` with values: `pending_review`, `accepted`,
  `rejected`.
- `Severity` — `Enum[str]` with values: `critical`, `high`, `medium`,
  `low`, `info`.
- `Reputation` — `Enum[str]` with values: `malicious`, `clean`,
  `unknown`.
- `Artifact` — `id` (UUID4 str), `incident_id` (str), `filename` (str),
  `source` (str — e.g. `siem`), `size_bytes` (int), `sha256` (str),
  `collected_at_utc` (datetime, tz-aware), `collector_version` (str).
- `IoC` — `id` (UUID4 str), `incident_id` (str), `type` (IocType),
  `value` (str), `confidence` (Confidence),
  `source_artifact_id` (str), `rationale` (str),
  `status` (IocStatus, default `pending_review`),
  `analyst_note` (str | None, default None),
  `reputation` (Reputation | None, default None),
  `reputation_source` (str | None, default None — `otx` or `misp`),
  `mitre_technique_ids` (list[str], default empty).
- `MitreTechnique` — `technique_id` (str, validator: matches
  `^T\d{4}(\.\d{3})?$`), `name` (str), `tactic` (str).
- `ApprovalDecision` — `Enum[str]` with values: `pending`, `approved`,
  `denied`, `killswitch`, `timeout`.
- `ApprovalRequest` — `id` (UUID4 str), `incident_id` (str),
  `host_id` (str), `reason` (str), `created_at_utc` (datetime),
  `ttl_seconds` (int), `decision` (ApprovalDecision, default
  `pending`), `decided_at_utc` (datetime | None),
  `decided_by` (str | None), `isolation_target`
  (Literal[`host_network`, `mail_relay_quarantine`], default
  `host_network`).
- `Incident` — `id` (UUID4 str), `scenario`
  (Literal[`ransomware`, `phishing`]), `siem_alert_id` (str),
  `started_at_utc` (datetime), `severity` (Severity, default `info`),
  `current_step` (str — e.g. `ingest`, `collect`, `coc`,
  `ioc_extraction`, `ioc_review`, `mitre_mapping`, `ti_lookup`,
  `approval`, `report`, `done`, `failed`), `completed_at_utc`
  (datetime | None).
- `AuditEvent` — `id` (UUID4 str), `incident_id` (str),
  `ts_utc` (datetime), `actor` (str — `system` or operator id),
  `action` (str, SCREAMING_SNAKE_CASE), `object` (str),
  `sha256` (str | None), `details` (dict, default empty).

All datetimes are timezone-aware UTC. Use Pydantic field validators
to enforce.

### 2. Audit trail — `backend/fai/core/audit.py`

Class `AuditTrail`:

- Constructor takes `runtime_dir: Path`. Creates the directory if missing.
- `async def write(self, event: AuditEvent) -> None` — appends one JSON
  line to `<runtime_dir>/audit/<incident_id>.jsonl`. Uses an asyncio
  lock keyed by `incident_id` to serialize writes per incident.
- `async def read(self, incident_id: str, *, action: str | None = None,
  actor: str | None = None, since: datetime | None = None) -> list[AuditEvent]`
  — reads and filters. Returns newest first.
- Helper: `make_event(incident_id, actor, action, object, **details) -> AuditEvent`
  generates ID and timestamp.

Tests:
- Write three events, read them back in reverse chronological order.
- Read with `action` filter returns only matching.
- Concurrent writes from 20 asyncio tasks for the same incident
  produce 20 lines (lock works).

### 3. Chain of Custody — `backend/fai/core/chain_of_custody.py`

Class `ChainOfCustody`:

- Constructor takes `runtime_dir: Path` and an `AuditTrail` instance.
- `async def record_artifact(self, incident_id: str, filename: str,
  content: bytes, source: str = "siem") -> Artifact` —
  - Generates UUID4 for the artifact.
  - Computes SHA-256 of `content`.
  - Writes content to
    `<runtime_dir>/artifacts/<incident_id>/<artifact_id>__<filename>`.
  - Builds an `Artifact` model.
  - Appends a JSON line for it to
    `<runtime_dir>/artifacts/<incident_id>/coc.jsonl`.
  - Writes an audit event `ARTIFACT_COLLECTED` with the SHA-256.
  - Returns the `Artifact`.
- `async def verify_integrity(self, incident_id: str) -> list[dict]` —
  re-hashes every artifact in the CoC log, returns a list of
  `{artifact_id, filename, expected_sha256, actual_sha256}` for any
  mismatch. Writes an audit event `COC_VERIFIED` with the result.

Tests:
- Record an artifact, read back the coc.jsonl, verify all five fields
  present and SHA-256 matches.
- Tamper one byte on disk, run `verify_integrity`, expect one
  mismatch entry.
- Record 10 artifacts concurrently, all 10 appear in coc.jsonl.

### 4. Mock SIEM — `backend/fai/mocks/mock_siem.py`

FastAPI router mounted at `/mock/siem`.

Endpoints:

- `POST /mock/siem/trigger/{scenario}` — body empty. `scenario` is
  `ransomware` or `phishing`. Returns the `alert.json` content of the
  corresponding scenario, with a freshly generated `alert_id`. The
  mock keeps an in-memory dict mapping fresh `alert_id` → scenario
  name so subsequent fetches work.
- `GET /mock/siem/alert/{alert_id}` — returns the stored alert.
- `GET /mock/siem/artifacts/{alert_id}` — returns a JSON list of
  artifacts to fetch, each with `filename` and `download_url` pointing
  at the next endpoint. Read from `data/scenarios/<scenario>/` directory
  listing.
- `GET /mock/siem/artifacts/{alert_id}/{filename}` — streams the file
  bytes with appropriate `Content-Type`. Reads from `data/scenarios/`.

Tests:
- Trigger ransomware, get alert back, list artifacts, fetch one,
  verify bytes match the file on disk.

### 5. Mock SOAR — `backend/fai/mocks/mock_soar.py`

FastAPI router at `/mock/soar`. In-memory state (dict).

Endpoints:

- `POST /mock/soar/case` — body `{title, severity, description}` →
  returns `{case_id}`.
- `POST /mock/soar/observable` — body `{case_id, type, value,
  reputation?, mitre_technique_ids?}` → returns `{observable_id}`.
- `POST /mock/soar/responder/isolate-host` — body `{case_id, host_id,
  approval_token}`. Validates the approval token (the gate-issued one).
  Returns `{job_id, status: "queued"}`. If token missing/invalid:
  returns 403 with descriptive error.
- `GET /mock/soar/case/{case_id}` — returns the case with all
  observables and responder jobs (for the lecturer to inspect).

Tests:
- Create case, attach observable, call isolate without token → 403.
- Call isolate with valid token (passed in from test) → 200.

### 6. Mock host isolation — `backend/fai/mocks/mock_host.py`

FastAPI router at `/mock/host`. In-memory state.

Endpoints:

- `POST /mock/host/{host_id}/isolate` — requires header
  `X-Approval-Token: <token>`. Token is validated against a global
  registry (which will be populated by the approval gate in Phase #4).
  For this phase, accept any non-empty token but store the token in
  the audit log. Returns `{host_id, status: "isolated", isolated_at}`.
  Reject empty/missing token with 403.
- `POST /mock/host/{host_id}/restore` — returns
  `{host_id, status: "online"}`.
- `GET /mock/host/{host_id}` — returns the current state.

Tests:
- Isolate without token → 403.
- Isolate with token → 200, status reflects.

### 7. SIEM consumer — `backend/fai/ingestion/siem_consumer.py`

Class `SiemConsumer`:

- Constructor takes `base_url: str`, `chain_of_custody: ChainOfCustody`,
  `audit: AuditTrail`, and an `httpx.AsyncClient`.
- `async def ingest_alert(self, incident_id: str, scenario: str) -> list[Artifact]`:
  - Calls `POST /mock/siem/trigger/<scenario>` to get a fresh alert.
  - Writes audit event `SIEM_ALERT_RECEIVED` with the alert id.
  - Lists artifacts via `GET /mock/siem/artifacts/<alert_id>`.
  - For each artifact: downloads bytes, calls
    `chain_of_custody.record_artifact(...)`. Note that
    `record_artifact` already emits `ARTIFACT_COLLECTED`.
  - Returns the list of `Artifact` records.

Tests:
- End-to-end: start app with mocks mounted, run `ingest_alert("test",
  "ransomware")`, verify all expected files are recorded in CoC and
  audit trail has expected event sequence.

### 8. SSE event bus — `backend/fai/core/events.py`

Simple in-memory pub/sub for SSE delivery to the frontend.

- Class `EventBus` with:
  - `subscribe(incident_id: str) -> asyncio.Queue` — returns a fresh
    queue. The bus keeps weak references to active queues per incident.
  - `async def publish(self, incident_id: str, event_type: str,
    payload: dict) -> None` — fan-out to all subscribed queues for that
    incident.
  - `unsubscribe(incident_id, queue)` — clean up.
- The bus is a singleton accessible via `get_event_bus()` (lru_cache).

Tests:
- Subscribe, publish, receive. Two subscribers both receive. Unsubscribe
  drops messages.

### 9. App wiring — update `backend/fai/app.py`

Mount the three mock routers under `/mock`. Wire up dependency-injection
helpers (`Depends(...)`) for `AuditTrail`, `ChainOfCustody`,
`SiemConsumer`, and `EventBus`. Use `lru_cache` factories.

## How to verify

- `cd backend && pytest -v` — all tests pass.
- `cd backend && ruff check . && mypy fai/` — no errors.
- `cd backend && uvicorn fai.app:app --port 8080` — server starts.
- In another terminal:
  ```bash
  curl -X POST http://localhost:8080/mock/siem/trigger/ransomware
  # → returns alert JSON with alert_id
  curl http://localhost:8080/mock/siem/artifacts/<alert_id>
  # → returns list of artifacts
  ```
- `runtime/audit/<incident_id>.jsonl` has events after manual ingest.
- `runtime/artifacts/<incident_id>/coc.jsonl` has chain of custody records.

## Out of scope for this phase

- LLM analysis (Phase #3).
- Threat Intel lookups (Phase #3).
- Playbooks and gates (Phase #4).
- All HTTP API endpoints under `/api/v1/` (Phase #4).
- Frontend (Issues #5 and #6).

## References

- AGENTS.md §3 (layout), §4 (coding standards), §8 (real vs mocked),
  §9 (FR-1, FR-2, FR-9 are the relevant ones here).
