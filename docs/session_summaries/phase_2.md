# Phase 2 · Backend core primitives · session summary

## What was built

- **Core data models** (`backend/fai/core/models.py`) — Pydantic v2 models for all domain entities: IocType, Confidence, IocStatus, Severity, Reputation enums; Artifact, IoC, MitreTechnique, ApprovalDecision, ApprovalRequest, Incident, AuditEvent models with field validators ensuring timezone-aware UTC timestamps.

- **Audit trail** (`backend/fai/core/audit.py`) — Append-only JSON-L audit trail with per-incident asyncio locks for serialized writes, filtering by action/actor/timestamp, and atomic log queries.

- **Chain of custody** (`backend/fai/core/chain_of_custody.py`) — Artifact ingestion with SHA-256 hashing, disk storage under `runtime/artifacts/<incident_id>/`, CoC JSON-L index, integrity verification detecting tampering, and audit event emission per artifact.

- **SSE event bus** (`backend/fai/core/events.py`) — In-memory pub/sub for incident-scoped event delivery, singleton pattern, weak reference cleanup via queue subscription/unsubscription.

- **Mock SIEM** (`backend/fai/mocks/mock_siem.py`) — FastAPI router at `/mock/siem` serving canned alerts and artifacts from `data/scenarios/` with fresh alert IDs and streaming file downloads.

- **Mock SOAR** (`backend/fai/mocks/mock_soar.py`) — FastAPI router at `/mock/soar` managing in-memory cases and observables; requires approval token for host isolation responder calls.

- **Mock host isolation** (`backend/fai/mocks/mock_host.py`) — FastAPI router at `/mock/host` enforcing `X-Approval-Token` header validation; tracks host states (isolated/online).

- **SIEM consumer** (`backend/fai/ingestion/siem_consumer.py`) — Triggers alerts, downloads artifacts via HTTP, records to chain of custody, emits audit trail events; awaits full integration with orchestrator in Phase 3.

- **App wiring** (updated `backend/fai/app.py`) — Mounted all three mock routers; added dependency injection via `lru_cache` factories for AuditTrail, ChainOfCustody, SiemConsumer, allowing endpoints to request shared instances.

## How to verify

```bash
# All tests pass
cd backend && pytest -v
# Expected: 35 passed in ~0.5s

# Linting clean
cd backend && ruff check fai/
# Expected: All checks passed!

# Type checking
cd backend && mypy fai/
# Expected: Success: no issues found in 14 source files

# Server starts
cd backend && timeout 5 uvicorn fai.app:app --port 8080 2>&1 || true
# Expected: Application startup complete + shutdown

# Manual endpoint testing (with server running)
curl -X POST http://localhost:8080/mock/siem/trigger/ransomware
# Returns alert with fresh alert_id

curl http://localhost:8080/mock/siem/artifacts/<alert_id>
# Returns list of artifacts

curl http://localhost:8080/mock/siem/artifacts/<alert_id>/<filename>
# Returns file bytes
```

## Decisions taken during the phase

1. **File storage layout** — Artifacts stored as `<artifact_id>__<filename>` to avoid collisions while preserving original names; CoC index stored as separate `coc.jsonl` in incident directory for efficient list operations.

2. **Lock strategy** — Per-incident locks in AuditTrail and ChainOfCustody instead of global locks to maximize concurrent throughput; dictionaries lazily init locks on first access.

3. **Mock registry pattern** — SIEM mock keeps `alert_id → scenario` in-memory dict; SOAR and host isolation similarly use dicts. This allows tests to create multiple alerts without persistence; registry will be swapped with real connectors in Phase 3/4.

4. **SSE event format** — Events serialized as `{event_type, payload}` JSON; payload is arbitrary dict for flexibility when LLM analysis results and approval gate state arrive.

5. **Error handling in mocks** — Mock endpoints return appropriate HTTP status codes (403 for missing token, 404 for not found, 400 for invalid input) matching production-like contracts.

6. **Dependency injection scope** — Used FastAPI `Depends()` pattern with `lru_cache` factories rather than globals, enabling future test mocking and app lifecycle management.

## Known gaps / follow-ups for later phases

- **SIEM consumer integration** — SiemConsumer works standalone but awaits orchestrator layer in Phase 3 to trigger ingestion and coordinate state machine.

- **Approval token validation** — Mock SOAR/host routers accept any non-empty token; Phase 4 approval gate will issue signed tokens and update registries.

- **LLM-extracted IoCs** — IoC model is defined; extraction, MITRE mapping, and TI lookup logic defer to Phase 3.

- **Report generation** — Artifact logs ready; report routes and templates deferred to Phase 4.

- **Frontend** — All backend endpoints return plain JSON; SSE streaming and UI binding deferred to Phases 5/6.

## Files created or modified

**Created:**
- `backend/fai/core/__init__.py`
- `backend/fai/core/models.py`
- `backend/fai/core/audit.py`
- `backend/fai/core/chain_of_custody.py`
- `backend/fai/core/events.py`
- `backend/fai/mocks/__init__.py`
- `backend/fai/mocks/mock_siem.py`
- `backend/fai/mocks/mock_soar.py`
- `backend/fai/mocks/mock_host.py`
- `backend/fai/ingestion/__init__.py`
- `backend/fai/ingestion/siem_consumer.py`
- `backend/tests/test_models.py`
- `backend/tests/test_audit.py`
- `backend/tests/test_chain_of_custody.py`
- `backend/tests/test_events.py`
- `backend/tests/test_mock_siem.py`
- `backend/tests/test_mock_soar.py`
- `backend/tests/test_mock_host.py`
- `backend/tests/test_siem_consumer.py`

**Modified:**
- `backend/fai/app.py` — Added router mounts and dependency injection helpers

