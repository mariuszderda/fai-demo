# [Backend] Playbooks, gates, REST API, SSE stream

> **Phase 4 of 7 · Orchestrator + REST API**
>
> This file is read by GitHub Copilot Agent Mode in IntelliJ as part of
> the FAI build. To start this phase, open Copilot Chat in IntelliJ,
> switch to Agent mode (not Ask mode), and paste the prompt below.

## Agent Mode Prompt — copy and paste this into Copilot Chat

```
You are working in agent mode on Phase 4 of the Forensics AI (FAI) project.

Read `AGENTS.md` at the repo root first — treat it as hard constraints. Phases 1, 2, and 3 are complete.

Then read the full spec for this phase at `prompts/03_backend_orchestrator_api.md` and execute it end-to-end.

The goal of this phase is: wire everything into two playbooks (ransomware, phishing), implement the two gates (IoC review, human approval), and expose the full REST API plus SSE event stream. After this phase the backend is feature-complete and ready for the frontend.

When you implement the approval gate, remember it must issue a one-time isolation token to the SOAR mock — Phase 2 left placeholder logic; replace it here with real token validation against the gate's registry.

When done, run both E2E tests (`test_e2e_ransomware`, `test_e2e_phishing`) — they must pass without an Anthropic API key (stub mode). Summarize and stop.
```

---

## Full specification

The rest of this document is the detailed spec the agent will read from
disk after you send the prompt above. You don't need to copy it — the
agent will open this file itself.


## Goal

Wire all backend modules into two playbooks (ransomware, phishing),
implement the two gates (IoC review, human approval), and expose
everything through a documented REST API plus an SSE event stream.
After this phase, the backend is feature-complete and ready for the
frontend.

## Scope

### 1. IoC review gate — `backend/fai/orchestrator/ioc_review_gate.py`

A pause point in the pipeline that exposes extracted IoCs to the
analyst for accept/reject before MITRE mapping runs.

- Class `IocReviewGate`:
  - In-memory registry: `dict[incident_id, asyncio.Event]` and
    `dict[incident_id, list[IoC]]`.
  - `async def submit(self, incident_id: str, iocs: list[IoC]) -> None`
    — stores IoCs (status `pending_review`), creates an unset Event,
    publishes `IOC_REVIEW_REQUESTED` to the audit trail and to the
    event bus.
  - `async def update_ioc(self, incident_id: str, ioc_id: str,
    status: IocStatus, analyst_note: str | None) -> IoC` — mutates the
    stored IoC, audits `IOC_REVIEWED` with the decision and note.
  - `async def finalize(self, incident_id: str, operator: str) -> list[IoC]`
    — checks that no `pending_review` IoCs remain. Sets the Event.
    Returns the list of `accepted` IoCs. Audits `IOC_REVIEW_FINALIZED`
    with the operator id.
  - `async def wait_for_finalize(self, incident_id: str) -> list[IoC]`
    — `await event.wait()`, then returns accepted IoCs.
  - `list_pending(self, incident_id: str) -> list[IoC]` — for the API.

Tests:
- Submit 5 IoCs, mark 3 accepted and 2 rejected, finalize → returns 3.
- Trying to finalize while 1 is still pending → raises a 400-style
  exception.
- `wait_for_finalize` returns when finalize is called.

### 2. Approval gate — `backend/fai/orchestrator/approval_gate.py`

Class `ApprovalGate`:

- In-memory: `dict[approval_id, ApprovalRequest]`. Also a token
  registry: `dict[token, approval_id]` for valid isolation tokens.
- `async def request(self, incident_id: str, host_id: str,
  reason: str, isolation_target: str = "host_network") -> ApprovalRequest`
  — creates with TTL from `settings.approval_ttl_seconds`. Audits
  `APPROVAL_REQUESTED`. Publishes `approval_pending` to event bus.
  Starts a TTL task that auto-decides `timeout` after TTL.
- `async def decide(self, approval_id: str, decision: ApprovalDecision,
  decided_by: str) -> ApprovalRequest`:
  - Validates current state is `pending`.
  - Sets decision, decided_at_utc, decided_by.
  - Cancels the TTL task.
  - Audits `APPROVAL_DECIDED` with the decision.
  - Publishes `approval_decided` event.
  - If `approved`: generates a one-time isolation token (UUID4
    string), stores in token registry with 60s TTL of its own. Stores
    the token on the request object as `isolation_token` (Pydantic
    field — add it).
  - Returns the updated request.
- `validate_token(token: str) -> str | None` — returns the
  `approval_id` if valid and not used. Marks token used on return.
- `list_pending(self) -> list[ApprovalRequest]`.

Tests:
- Request approval, approve it → token issued, validatable once.
- Validate token twice → second time returns None (single-use).
- Request approval, wait past TTL → decision becomes `timeout`,
  no token issued.
- Killswitch decision → no token issued, audited.

Wire the validate_token check into `mocks/mock_soar.py`
`responder/isolate-host` and `mocks/mock_host.py`
`isolate` so they now reject requests whose token is not in the
gate's registry. Update the audit trail entries from Phase #2 to
reference the validated `approval_id`.

### 3. Playbook abstract — `backend/fai/orchestrator/playbook.py`

```python
class Playbook(ABC):
    name: str
    @abstractmethod
    async def run(self, incident: Incident) -> None: ...
```

The class holds references (via constructor injection) to:
`SiemConsumer`, `IocExtractor`, `MitreMapper`, `ThreatIntelClient`,
`IocReviewGate`, `ApprovalGate`, `ReportGenerator`, `AuditTrail`,
`EventBus`, and the in-memory incident store.

Helper method `_advance(incident, step_name)` that updates
`incident.current_step` and emits a `pipeline_step` SSE event plus an
audit entry.

### 4. Ransomware playbook — `backend/fai/orchestrator/ransomware.py`

`class RansomwarePlaybook(Playbook)`:

```
ingest (SIEM)
→ collect (artifacts written via CoC)
→ ioc_extraction (LLM)
→ ioc_review (PAUSES; awaits gate.finalize)
→ mitre_mapping (LLM, hallucination filter)
→ ti_lookup (OTX → MISP)
→ severity classification
→ if Critical: approval request → wait for decision
   if approved: call mock_soar isolate-host (token attached)
→ report generation
→ done
```

Severity rule (ransomware):
- Critical if (≥1 accepted IoC has `reputation==malicious`) AND
  (≥1 mapped technique in `{T1486, T1490}`).
- High if ≥1 accepted IoC has `reputation==malicious`.
- Otherwise: Medium.

Isolation target: `host_network`. Reason string format:
`"Ransomware confirmed on {host_id}: {top_technique_id} + {malicious_ioc_count} malicious IoCs"`.

### 5. Phishing playbook — `backend/fai/orchestrator/phishing.py`

Same skeleton; classification rule:
- High if (≥1 url/domain IoC has `reputation==malicious`) AND
  (mapped technique `T1566` present).
- Medium otherwise.

Isolation target: `mail_relay_quarantine`. Reason string:
`"Phishing confirmed: quarantine mail relay for {sender_domain}"`.

### 6. Incident store — `backend/fai/orchestrator/incident_store.py`

Simple in-memory dict wrapper.

- `create(scenario) -> Incident`
- `get(incident_id) -> Incident | None`
- `update(incident_id, **fields) -> Incident`
- `list() -> list[Incident]` (newest first)
- `list_iocs(incident_id) -> list[IoC]`
- `set_iocs(incident_id, iocs: list[IoC])` (used after extraction and
  again after MITRE mapping and TI lookup)

The store is the source of truth for the API responses. Keep it
simple, do not pretend it's a database.

### 7. Playbook dispatcher — `backend/fai/orchestrator/dispatcher.py`

`async def dispatch(scenario: str, incident_store: IncidentStore, ...)`:
- Creates an incident.
- Selects the playbook by name.
- Runs `playbook.run(incident)` as a background asyncio task.
- Returns the `incident_id` immediately.
- On exception in the playbook task: catches, logs, audits
  `PLAYBOOK_FAILED`, sets `incident.current_step = "failed"`, emits
  SSE event.

### 8. API routers — `backend/fai/api/`

Each in its own module. Wire all into `backend/fai/app.py` under
`/api/v1`.

#### `api/incidents.py`

- `POST /api/v1/incidents` — body `{"scenario": "ransomware"|"phishing"}`.
  Calls dispatcher. Returns `{incident_id, status: "ingesting"}`. 202.
- `GET /api/v1/incidents` — returns list of all incidents (id, scenario,
  severity, current_step, started_at_utc, completed_at_utc, IoC count,
  technique count, isolation decision).
- `GET /api/v1/incidents/{id}` — full incident state.
- `POST /api/v1/incidents/{id}/verify-coc` — runs
  `chain_of_custody.verify_integrity`, returns list of mismatches.

#### `api/ioc.py`

- `GET /api/v1/incidents/{id}/ioc` — returns IoCs with their current
  status (all of them, including rejected and pending).
- `PATCH /api/v1/incidents/{id}/ioc/{ioc_id}` — body `{"status":
  "accepted"|"rejected", "analyst_note": "..."}`. Calls
  `ioc_review_gate.update_ioc`. Returns the updated IoC.
- `POST /api/v1/incidents/{id}/ioc/finalize` — body `{"operator":
  "..."}`. Calls `ioc_review_gate.finalize`. Returns
  `{accepted_count, rejected_count}`.

#### `api/approvals.py`

- `GET /api/v1/approvals/pending` — list pending requests.
- `GET /api/v1/approvals/{id}` — single request.
- `POST /api/v1/approvals/{id}/decide` — body `{"decision":
  "APPROVE"|"DENY"|"KILLSWITCH", "decided_by": "..."}`. Maps to
  ApprovalDecision values.

#### `api/mitre.py`

- `GET /api/v1/mitre/techniques` — returns the matrix structure from
  `MitreLoader.get_matrix()`.
- `GET /api/v1/incidents/{id}/mitre-coverage` — returns
  `{detected: [{technique_id, ioc_ids: [...], confidence: "high"|"medium"|"low"}]}`.
- `GET /api/v1/mitre-coverage/global` — aggregated across all
  incidents.

#### `api/audit.py`

- `GET /api/v1/audit/{incident_id}` — query params `action`, `actor`,
  `since` (ISO datetime). Returns events newest-first. Cap at 1000
  per call.

#### `api/stream.py`

- `GET /api/v1/incidents/{id}/stream` — SSE endpoint using
  `sse-starlette` (or roll your own with `StreamingResponse` and
  `text/event-stream`). Subscribes to event bus for the incident,
  yields events as `event: <type>\ndata: <json>\n\n`. Heartbeat every
  15s with `event: heartbeat`.
- Event types emitted by playbooks:
  - `pipeline_step` — `{step, status, duration_ms?, extra?}`
  - `ioc_extracted` — `{count}`
  - `ioc_review_requested` — `{count}`
  - `ioc_review_finalized` — `{accepted, rejected}`
  - `mitre_mapped` — `{technique_ids}`
  - `ti_lookup_completed` — `{malicious_count}`
  - `approval_pending` — `{approval_id, host_id, reason, ttl_seconds}`
  - `approval_decided` — `{approval_id, decision}`
  - `report_ready` — `{report_path}`
  - `failed` — `{step, error_message}`

#### `api/settings.py`

- `GET /api/v1/settings` — read-only summary:
  ```json
  {
    "llm": {"provider": "anthropic"|"stub", "model": "...", "stub_active": true|false},
    "otx": {"key_present": true|false},
    "mitre": {"version": "v14", "path": "...", "techniques_count": 0},
    "approval_ttl_seconds": 600,
    "directories": {"audit": "...", "artifacts": "...", "reports": "..."}
  }
  ```
  Never expose secret values themselves.

### 9. CORS and OpenAPI

- Ensure CORS allows the frontend dev origin (`http://localhost:5173`).
- Set FastAPI title `Forensics AI API`, version `0.1.0`.
- Use Pydantic models in route signatures so OpenAPI is rich.

### 10. End-to-end tests

In `backend/tests/test_e2e_ransomware.py` and
`test_e2e_phishing.py`:

- Use the stub LLM (no API key needed).
- Override `settings.approval_ttl_seconds = 5` for the test.
- Trigger the scenario via `POST /api/v1/incidents`.
- Poll `GET /api/v1/incidents/{id}/ioc` until IoCs appear.
- Accept all, call finalize.
- Poll `GET /api/v1/approvals/pending` until the approval shows up.
- Decide `APPROVE`, then poll incident until `current_step == "done"`.
- Assert: report file exists, audit trail contains the expected event
  sequence (including `HALLUCINATION_REJECTED` for the stub's
  intentional `T9999`).

Each E2E test must complete in under 15 seconds.

## How to verify

- `cd backend && pytest -v` — all tests pass, including the two E2E.
- `cd backend && pytest -v --no-header -q` — completes in <30s total.
- `uvicorn fai.app:app --port 8080 --reload`, then:
  ```bash
  curl -X POST http://localhost:8080/api/v1/incidents \
    -H 'Content-Type: application/json' \
    -d '{"scenario":"ransomware"}'
  # → {"incident_id":"...","status":"ingesting"}

  # follow SSE stream
  curl -N http://localhost:8080/api/v1/incidents/<id>/stream
  ```
- `curl http://localhost:8080/openapi.json | jq '.paths | keys'` →
  shows all the /api/v1/... routes.

## Out of scope for this phase

- Frontend (Issues #5 and #6).
- Docker compose finalization (Phase #7).
- DEMO.md (Phase #7).

## References

- AGENTS.md §9 (all FRs), §10 (prompts).
