# [Backend] LLM analysis, MITRE mapper, Threat Intel

> **Phase 3 of 7 · Backend analysis**
>
> This file is read by GitHub Copilot Agent Mode in IntelliJ as part of
> the FAI build. To start this phase, open Copilot Chat in IntelliJ,
> switch to Agent mode (not Ask mode), and paste the prompt below.

## Agent Mode Prompt — copy and paste this into Copilot Chat

```
You are working in agent mode on Phase 3 of the Forensics AI (FAI) project.

Read `AGENTS.md` at the repo root first — treat it as hard constraints. Phases 1 and 2 are complete.

Then read the full spec for this phase at `prompts/02_backend_analysis.md` and execute it end-to-end.

The goal of this phase is: implement the analysis layer — LLM client (with Anthropic real + deterministic stub fallback), MITRE loader and validator with hallucination protection, MITRE mapper, Threat Intel client (OTX → MISP fallback), and report generator. The LLM prompts in §10 of AGENTS.md must be used verbatim — do not paraphrase them.

Critical: the stub LLM must emit IoC values that have entries in `data/misp_fallback.json`, and must emit at least one deliberately hallucinated MITRE technique ID (like T9999) per scenario so the hallucination filter has something visible to catch in the demo.

When done, run the verification checklist including the `scripts/smoke_analysis.py` end-to-end smoke. Summarize and stop.
```

---

## Full specification

The rest of this document is the detailed spec the agent will read from
disk after you send the prompt above. You don't need to copy it — the
agent will open this file itself.


## Goal

Implement the analysis layer: LLM-based IoC extraction, MITRE ATT&CK
mapping with hallucination protection, and Threat Intelligence lookup
with OTX→MISP fallback. After this phase, all the AI/external-API logic
exists; the next issue wires it into playbooks and exposes the API.

## Scope

### 1. LLM client — `backend/fai/analysis/llm_client.py`

Two implementations behind a common interface.

#### Interface

```python
class LlmClient(Protocol):
    async def complete_json(
        self,
        system_prompt: str,
        user_content: str,
        *,
        max_tokens: int = 4096,
    ) -> dict: ...
```

The method calls the LLM, expects a JSON response, parses it, returns
the dict. Raises `LlmResponseError` on non-JSON or unparseable output
(retry once with a stricter "Return ONLY JSON" reminder appended).

#### `AnthropicClient`

Real implementation using `anthropic.AsyncAnthropic`.
- Model from `settings.anthropic_model` (default `claude-sonnet-4-5`).
- On model-not-found error, retry once with `claude-3-5-sonnet-latest`.
- 30-second timeout per call.
- Audits `LLM_CALL_STARTED` and `LLM_CALL_COMPLETED` (or `_FAILED`)
  with the model id, prompt SHA-256 (not full prompt for privacy/size),
  and token counts.

#### `StubLlmClient`

Deterministic stub used when `ANTHROPIC_API_KEY` is missing OR
`settings.use_stub_llm=True`. Returns canned responses keyed by the
SHA-256 of the system prompt.

Build a small dispatch dict mapping `(system_prompt_sha256, scenario_marker)
→ canned_response`. The `scenario_marker` is derived by looking at the
`user_content` for known sentinels (e.g. occurrence of `cryptdaemon` →
ransomware, occurrence of `faktury-online` → phishing).

**Canned responses must:**
- For IoC extraction → emit IoCs whose values are keys in
  `data/misp_fallback.json` (so TI fallback succeeds end-to-end).
- For MITRE mapping → emit valid technique IDs that exist in the v14
  dataset (so they survive the hallucination filter).
- For executive summary → return a plausible short Polish Markdown
  summary referencing the data structure passed in.

For ransomware, IoC extraction should emit at least:
- `203.0.113.47` (ipv4)
- `c2-relay.evil-corp-demo.test` (domain)
- One sha256 of the `cryptdaemon` binary (use the seed=42 generated hash)

For phishing, at least:
- `evil-corp-demo.test` (domain)
- `faktury-online.evil-corp-demo.test` (domain)
- `https://faktury-online.evil-corp-demo.test/download/faktura.exe` (url)
- The sha256 of the fake `faktura.exe`

For MITRE mapping, the stub must produce techniques from this safe
list per scenario:
- Ransomware: `T1486` (Data Encrypted for Impact), `T1071`
  (Application Layer Protocol), `T1083` (File and Directory Discovery).
- Phishing: `T1566` (Phishing), `T1204.002` (User Execution: Malicious
  File).

Plus include **one deliberately hallucinated technique ID** per
scenario (e.g. `T9999`) so the hallucination filter has something to
catch — this is a teaching moment for the lecturer.

#### Factory

`def get_llm_client(settings: Settings) -> LlmClient`:
- If `settings.anthropic_api_key` is set and non-empty AND
  `not settings.use_stub_llm` → return `AnthropicClient`.
- Otherwise → return `StubLlmClient` and log a structured warning
  `LLM_STUB_MODE_ACTIVE`.

### 2. Prompts — `backend/fai/analysis/prompts.py`

Three constants holding the system prompts EXACTLY as in AGENTS.md §10.
Do not modify a single character of these strings (the lecturer may
diff them).

Helper functions:

- `def build_ioc_extraction_user_content(artifacts: list[Artifact],
  artifact_contents: dict[str, str]) -> str` — wraps each artifact's
  textual content in `<artifact name="..." sha256="...">...</artifact>`
  tags. For binary files, include only metadata (filename, size, hash),
  not bytes.
- `def build_mitre_mapping_user_content(iocs: list[IoC]) -> str` —
  emits a JSON list with `value`, `type`, `source_artifact`, `rationale`.
- `def build_executive_summary_user_content(report_data: dict) -> str` —
  emits a structured JSON of the incident facts.

### 3. IoC extractor — `backend/fai/analysis/ioc_extractor.py`

Class `IocExtractor`:

- Constructor: `LlmClient`, `AuditTrail`.
- `async def extract(self, incident_id: str, artifacts: list[Artifact],
  artifact_contents: dict[str, str]) -> list[IoC]`:
  - Builds user content.
  - Calls `llm.complete_json(system_prompt, user_content)`.
  - Validates response against expected schema (manual dict check).
  - For each emitted IoC:
    - If `type == ipv4`: filter out RFC1918 / loopback / link-local
      (use `ipaddress` stdlib). Skip with audit `IOC_FILTERED_PRIVATE_IP`.
    - Generate UUID4 `id`, set `incident_id`, `source_artifact_id`,
      `status=pending_review`.
  - If response has non-empty `notes` field → write audit event
    `PROMPT_INJECTION_DETECTED` with the notes content.
  - Return list of `IoC` (excludes filtered ones).

Tests:
- With `StubLlmClient`, extract IoCs for ransomware scenario → expect
  ≥3 IoCs, no RFC1918 addresses.
- Inject an artifact with a private IP value → ensure it's filtered
  and audited.
- Inject a `notes` value via a stub override → ensure the audit event
  is written.

### 4. MITRE loader and validator — `backend/fai/mitre/loader.py`

Class `MitreLoader`:

- Constructor: `dataset_path: Path`. Loads the JSON at instantiation.
- `is_valid_technique(technique_id: str) -> bool` — checks against
  the loaded set of `T####`/`T####.###` IDs.
- `get_technique(technique_id: str) -> MitreTechnique | None` — returns
  metadata.
- `get_matrix() -> dict` — returns a frontend-friendly structure:
  ```python
  {
    "tactics": [
      {
        "id": "TA0001",
        "name": "Initial Access",
        "techniques": [
          {"id": "T1566", "name": "Phishing", "sub_techniques": [
            {"id": "T1566.002", "name": "Spearphishing Link"}
          ]}
        ]
      },
      ...
    ]
  }
  ```
- Use `lru_cache` on `get_matrix()` so it's computed once.

Tests:
- Load the real `enterprise-attack.json`, verify `T1486` is valid
  and `T9999` is not.
- Verify `get_matrix()` returns 14 tactics.

### 5. MITRE mapper — `backend/fai/analysis/mitre_mapper.py`

Class `MitreMapper`:

- Constructor: `LlmClient`, `MitreLoader`, `AuditTrail`.
- `async def map_iocs(self, incident_id: str, iocs: list[IoC]) -> list[IoC]`:
  - Calls LLM with the MITRE mapping prompt.
  - For each emitted mapping:
    - For each technique_id: if `mitre_loader.is_valid_technique(id)`
      → keep. Else → drop, write audit `HALLUCINATION_REJECTED` with
      the rejected ID.
  - Updates the matching `IoC` objects in place by setting
    `mitre_technique_ids` to the surviving technique IDs.
  - Returns the updated `IoC` list.

Tests:
- With stub, run mapping on ransomware IoCs → confirm survivors
  include `T1486` and exclude `T9999`. Confirm audit event for the
  rejection.

### 6. Threat Intel — `backend/fai/analysis/threat_intel.py`

Class `ThreatIntelClient`:

- Constructor: `httpx.AsyncClient`, `settings: Settings`, `AuditTrail`,
  and a `misp_fallback_path: Path`.
- `async def lookup(self, ioc: IoC) -> tuple[Reputation, str]`:
  - Returns `(reputation, source)` where source is `"otx"` or `"misp"`.
  - Only looks up types `{ipv4, domain, url, md5, sha1, sha256}`.
  - If OTX key absent → straight to MISP fallback.
  - If OTX call:
    - URL pattern:
      - ipv4: `https://otx.alienvault.com/api/v1/indicators/IPv4/<value>/general`
      - domain: `.../indicators/domain/<value>/general`
      - url: `.../indicators/url/<value>/general` (URL-encoded)
      - md5/sha1/sha256: `.../indicators/file/<value>/general`
    - Timeout 5s.
    - Header `X-OTX-API-KEY: <key>`.
    - On 5xx, timeout, or network error: fallback. Write audit
      `OTX_TIMEOUT_FALLBACK_TO_MISP`.
    - On 200: parse `pulse_info.count` — if > 0 → `malicious`,
      else → `clean`. Write audit `OTX_LOOKUP_RESULT`.
- `async def lookup_all(self, incident_id: str, iocs: list[IoC]) -> list[IoC]`:
  - Caps at 10 lookups per incident (audit `TI_LOOKUP_CAP_REACHED` if hit).
  - Updates IoC objects in place with `reputation` and
    `reputation_source`.

The MISP fallback loads `data/misp_fallback.json` once and looks up
by IoC `value`. Missing values default to `unknown`.

Tests:
- With OTX key absent, every ransomware IoC gets a reputation from
  MISP. Confirm audit shows fallback events.
- Mock httpx to simulate OTX 503 → fallback kicks in.
- Mock httpx to simulate OTX 200 with `pulse_info.count=5` → returns
  malicious.

### 7. Report generator — `backend/fai/reporting/generator.py`

Class `ReportGenerator`:

- Constructor: `LlmClient`, `AuditTrail`, `runtime_dir: Path`,
  templates directory (`backend/fai/reporting/templates/`).
- `async def generate(self, incident: Incident, iocs: list[IoC],
  artifacts: list[Artifact]) -> tuple[str, str]`:
  - Builds structured `report_data` dict from the inputs.
  - Reads audit trail for the incident → builds chronological timeline.
  - Calls LLM for the executive summary (Polish Markdown).
  - Renders the full report using a Jinja2 template with these
    sections (order matters):
    1. Executive Summary (LLM-generated)
    2. Timeline (deterministic, from audit)
    3. IoC Table (only `status=accepted`, with type, value, reputation,
       MITRE technique IDs)
    4. Chain of Custody Statement (count of artifacts, listing of
       SHA-256 values, verification status)
  - Writes Markdown to `runtime/reports/<incident_id>.md`.
  - Converts to HTML using `markdown-it-py` (with tables enabled).
  - Returns `(markdown, html)`.

Template: `backend/fai/reporting/templates/report.md.j2`. Polish
headers, English IoC type codes.

Tests:
- Generate a report end-to-end with hand-built input → confirm all
  four sections present, IoC table includes only accepted IoCs,
  timeline pulls from audit.

## How to verify

- `cd backend && pytest -v` → all new tests pass.
- `cd backend && pytest -v -k stub` → stub-only tests pass (no
  ANTHROPIC_API_KEY needed).
- `cd backend && ruff check . && mypy fai/` → clean.
- Manual sanity: write a small `scripts/smoke_analysis.py` that
  - Wires up the stub LLM, mitre loader, TI client (no OTX).
  - Runs IoC extraction on the ransomware artifacts.
  - Runs MITRE mapping.
  - Runs TI lookup.
  - Generates a report.
  - Prints the report.

  Commit this smoke script — it will be useful in the next issue too.

## Out of scope for this phase

- HTTP API endpoints (`/api/v1/...`) — Phase #4.
- Playbooks and orchestration — Phase #4.
- Approval gate logic — Phase #4.
- Frontend.

## References

- AGENTS.md §10 (prompts), §11 (demo data conventions), §9 (FR-3, FR-4,
  FR-5, FR-8).
