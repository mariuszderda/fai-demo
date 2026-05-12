# Phase 3 · Backend analysis · session summary

## What was built
- LLM client layer with two implementations:
  - `AnthropicClient` (real, uses `anthropic.AsyncAnthropic`, auditing of calls) — implemented per spec (retry fallback model logic present).
  - `StubLlmClient` (deterministic fallback) producing canned responses keyed by prompt content and scenario marker. Stub responses emit IoCs present in `data/misp_fallback.json` and include one deliberately hallucinated MITRE technique (`T9999`) per scenario for demo/hallucination filtering.
- Prompts module: `backend/fai/analysis/prompts.py` containing the three system prompts EXACTLY as specified in `AGENTS.md §10` and helper builders:
  - `build_ioc_extraction_user_content`
  - `build_mitre_mapping_user_content`
  - `build_executive_summary_user_content`
- IoC extractor: `backend/fai/analysis/ioc_extractor.py` — builds user content, calls LLM, validates schema, filters RFC1918/loopback/link-local IPv4 addresses (audits filtered IPs), writes `PROMPT_INJECTION_DETECTED` if `notes` present.
- MITRE loader: `backend/fai/mitre/loader.py` — loads `data/mitre/enterprise-attack.json`, validates technique IDs, exposes `is_valid_technique`, `get_technique`, `get_matrix` (cached with `lru_cache`).
- MITRE mapper: `backend/fai/analysis/mitre_mapper.py` — calls LLM to propose mappings, filters hallucinated technique IDs (writes `HALLUCINATION_REJECTED` audit events), updates IoCs in-place.
- Threat Intel client: `backend/fai/analysis/threat_intel.py` — OTX lookup implementation with timeout and header usage, full MISP local JSON fallback (`data/misp_fallback.json`) when OTX key missing or on OTX failures, `lookup_all` with cap and `TI_LOOKUP_CAP_REACHED` audit.
- Report generator: `backend/fai/reporting/generator.py` — collects audit timeline, builds structured report data, requests LLM executive summary (Polish Markdown), renders Markdown report and converts to HTML.
- Tests: comprehensive tests added at `backend/tests/test_analysis.py` (plus existing tests exercised). All backend tests now pass.
- Smoke script: `scripts/smoke_analysis.py` — end-to-end demo wiring stub LLM, MITRE loader, TI client (MISP fallback), report generator. Prints summary and report locations.

## How to verify
Run the test suite and smoke script from the repository root.

1. Run backend tests:

```bash
cd backend
python -m pytest -v
```

2. Run smoke analysis end-to-end (uses stub LLM and MISP fallback):

```bash
cd /home/mario/dev/fai
PYTHONPATH=/home/mario/dev/fai/backend python scripts/smoke_analysis.py
```

3. Lint/type checks (optional):

```bash
cd backend
ruff check fai/  # linter
python -m mypy fai/  # type checking (requires mypy installed)
```

4. Inspect generated report for a sample incident in runtime/reports/*.md and *.html.

## Decisions taken during the phase
- Added `use_stub_llm: bool` to `Settings` to allow forcing stub mode for demos and tests. (Keeps `ANTHROPIC_API_KEY` semantics intact.)
- `StubLlmClient` detection: implemented a conservative content-based detector to choose ransomware vs phishing stub responses (searching for artifacts text markers such as `cryptdaemon`, `.locked`, `faktury`, `faktura`, email-related tokens). This approach keeps the stub deterministic for tests and demos.
- Stub responses produce both IoC-extraction outputs and MITRE mapping outputs; MITRE responses deliberately include an invalid `T9999` per scenario to exercise hallucination protection.
- For MITRE matrix generation, a pragmatic tactic mapping was implemented to produce a frontend-friendly `tactics` list (14 tactics as expected). The loader reads `data/mitre/enterprise-attack.json` on instantiation.
- Report generation uses `markdown-it-py` for Markdown→HTML. To avoid optional plugin dependency issues in constrained environments, tables rendering uses base `markdown-it-py` (tables supported) without extra plugin dependency.

These choices were documented in this session summary.

## Known gaps / follow-ups for later phases
- `AnthropicClient` integration: the client scaffolding is present and audited, but real deployments require proper `ANTHROPIC_API_KEY` and network connectivity (out of scope for unit tests). Ensure env var is set in production runs.
- More robust LLM response parsing & retry strategies could be implemented (e.g., partial JSON extraction) — current implementation retries once with a "Return ONLY JSON" hint.
- `mypy` strictness: some minor type annotations were adjusted to satisfy checks, but further typing coverage is always helpful.
- Frontend wiring of report endpoints and playbook orchestration is deferred to Phase 4.

## Files created or modified
- Created:
  - `backend/fai/analysis/prompts.py`
  - `backend/fai/analysis/llm_client.py`
  - `backend/fai/analysis/ioc_extractor.py`
  - `backend/fai/analysis/mitre_mapper.py`
  - `backend/fai/analysis/threat_intel.py`
  - `backend/fai/reporting/generator.py`
  - `backend/fai/mitre/loader.py`
  - `backend/tests/test_analysis.py`
  - `scripts/smoke_analysis.py`
  - `backend/fai/analysis/__init__.py`, `backend/fai/mitre/__init__.py`, `backend/fai/reporting/__init__.py`
- Modified:
  - `backend/fai/config.py` (added `use_stub_llm` setting)
  - Minor fixes in a few modules to satisfy lint/type checks and tests.

## Quick notes for the lecturer/demo
- The `StubLlmClient` guarantees that IoC values emitted by the stub are present in `data/misp_fallback.json`, ensuring the TI fallback flow is exercised end-to-end without network access.
- Each scenario’s MITRE mapping includes an intentionally hallucinated `T9999` ID so the `MitreMapper` will reject it and emit `HALLUCINATION_REJECTED` audit events — visible in the smoke script output and audit logs.

---

If you'd like, I can now:
- Commit the changes with conventional commit messages (I can prepare suggested commits),
- Run `mypy` and `ruff --fix` and address any remaining type issues, or
- Start the next phase (Phase 4) wiring the analysis layer into the API.

Tell me which of these you want me to do next, or I will stop here and await instructions.
