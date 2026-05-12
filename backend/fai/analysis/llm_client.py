"""LLM client implementation with Anthropic real and stub fallback."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Protocol

import anthropic

from fai.config import Settings
from fai.core.audit import AuditTrail, make_event

logger = logging.getLogger(__name__)


class LlmResponseError(Exception):
    """Raised when LLM response is invalid or unparseable."""

    pass


class LlmClient(Protocol):
    """Protocol for LLM clients."""

    async def complete_json(
        self,
        system_prompt: str,
        user_content: str,
        *,
        max_tokens: int = 4096,
        incident_id: str | None = None,
    ) -> dict[str, Any]:
        """Call LLM with system prompt and user content, return parsed JSON.

        Args:
            system_prompt: System prompt for the LLM.
            user_content: User content/question.
            max_tokens: Maximum tokens in response (default 4096).

        Returns:
            Parsed JSON response as dict.

        Raises:
            LlmResponseError: If response is not valid JSON or unparseable.
        """


class AnthropicClient:
    """Real Anthropic Claude client."""

    def __init__(self, api_key: str, model: str, audit: AuditTrail) -> None:
        """Initialize Anthropic client.

        Args:
            api_key: Anthropic API key.
            model: Model ID (e.g. claude-sonnet-4-5).
            audit: Audit trail for logging.
        """
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model
        self.audit = audit

    async def complete_json(
        self,
        system_prompt: str,
        user_content: str,
        *,
        max_tokens: int = 4096,
        incident_id: str | None = None,
    ) -> dict[str, Any]:
        """Call Anthropic API and return parsed JSON response."""
        prompt_hash = hashlib.sha256(system_prompt.encode()).hexdigest()
        audit_incident_id = incident_id or "unknown"

        # Audit: LLM_CALL_STARTED
        await self.audit.write(
            make_event(
                incident_id=audit_incident_id,
                actor="llm_client",
                action="LLM_CALL_STARTED",
                object=self.model,
                prompt_sha256=prompt_hash,
            )
        )

        try:
            # Try with primary model
            message = await self._call_api(
                system_prompt, user_content, max_tokens, self.model
            )
        except anthropic.NotFoundError:
            # Retry with fallback model
            logger.warning(
                f"Model {self.model} not found, retrying with fallback",
                extra={"model": self.model},
            )
            message = await self._call_api(
                system_prompt, user_content, max_tokens, "claude-3-5-sonnet-latest"
            )

        # Extract text and parse JSON
        response_text = message.content[0].text
        try:
            parsed = json.loads(response_text)
        except json.JSONDecodeError:
            # Retry once with stricter reminder
            logger.warning("Invalid JSON response, retrying with stricter prompt")
            retry_content = user_content + "\n\nReturn ONLY valid JSON. No markdown, no explanation."
            message = await self._call_api(
                system_prompt, retry_content, max_tokens, self.model
            )
            response_text = message.content[0].text
            try:
                parsed = json.loads(response_text)
            except json.JSONDecodeError as e:
                raise LlmResponseError(f"Response not valid JSON: {response_text}") from e

        # Audit: LLM_CALL_COMPLETED
        await self.audit.write(
            make_event(
                incident_id=audit_incident_id,
                actor="llm_client",
                action="LLM_CALL_COMPLETED",
                object=self.model,
                prompt_sha256=prompt_hash,
                input_tokens=message.usage.input_tokens,
                output_tokens=message.usage.output_tokens,
            )
        )

        return parsed

    async def _call_api(
        self,
        system_prompt: str,
        user_content: str,
        max_tokens: int,
        model: str,
    ) -> Any:
        """Internal: call Anthropic API with timeout."""
        try:
            # Use synchronous client invocation with 30s timeout
            message = await asyncio.wait_for(
                self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_content}],
                ),
                timeout=30.0,
            )
            return message
        except asyncio.TimeoutError as e:
            raise LlmResponseError("LLM call timeout after 30s") from e


class StubLlmClient:
    """Deterministic stub LLM client for testing/demo without API key."""

    def __init__(self, audit: AuditTrail | None = None) -> None:
        """Initialize stub client.

        Args:
            audit: Optional audit trail for logging.
        """
        self.audit = audit

    async def complete_json(
        self,
        system_prompt: str,
        user_content: str,
        *,
        max_tokens: int = 4096,
        incident_id: str | None = None,
    ) -> dict[str, Any]:
        """Return deterministic canned response based on prompt hash and scenario."""
        del max_tokens
        prompt_hash = hashlib.sha256(system_prompt.encode()).hexdigest()
        audit_incident_id = incident_id or "unknown"

        if self.audit is not None:
            await self.audit.write(
                make_event(
                    incident_id=audit_incident_id,
                    actor="llm_client",
                    action="LLM_CALL_STARTED",
                    object="stub",
                    prompt_sha256=prompt_hash,
                )
            )

        # Detect scenario from user_content
        scenario = self._detect_scenario(user_content)

        # Detect if this is a MITRE mapping request by looking for JSON format with "value" and "type"
        # MITRE mapping requests contain JSON like: [{"value": "...", "type": "...", "source_artifact": "...", "rationale": "..."}]
        # IoC extraction requests contain artifact content wrapped in XML-like tags
        is_mitre_mapping = (
            '"value"' in user_content
            and '"type"' in user_content
            and user_content.strip().startswith("[")
        )

        # Get canned response
        response = self._get_canned_response(prompt_hash, scenario, is_mitre_mapping)

        if self.audit is not None:
            await self.audit.write(
                make_event(
                    incident_id=audit_incident_id,
                    actor="llm_client",
                    action="LLM_CALL_COMPLETED",
                    object="stub",
                    prompt_sha256=prompt_hash,
                    input_tokens=0,
                    output_tokens=0,
                )
            )

        return response

    def _detect_scenario(self, content: str) -> str:
        """Detect scenario marker from user content.

        Returns:
            "ransomware", "phishing", or "unknown".
        """
        content_lower = content.lower()

        # Check for ransomware markers
        if any(
            marker in content_lower
            for marker in ["cryptdaemon", "ransomware", ".locked", "c2-relay"]
        ):
            return "ransomware"

        # Check for phishing markers
        if any(
            marker in content_lower
            for marker in [
                "faktury",
                "invoice",
                "phishing",
                "email",
                "mailto",
                "faktura",
            ]
        ):
            return "phishing"

        return "unknown"

    def _get_canned_response(
        self, prompt_hash: str, scenario: str, is_mitre_mapping: bool = False
    ) -> dict[str, Any]:
        """Get deterministic canned response.

        Args:
            prompt_hash: First 8 chars of system prompt SHA256.
            scenario: "ransomware", "phishing", or "unknown".
            is_mitre_mapping: True if this is a MITRE mapping request.

        Returns:
            Canned response dict appropriate to the prompt and scenario.
        """
        if is_mitre_mapping:
            # For MITRE mapping, regardless of scenario, return comprehensive mapping
            return {
                "mappings": [
                    {
                        "ioc_value": "203.0.113.47",
                        "techniques": [
                            {
                                "technique_id": "T1071",
                                "tactic": "Command and Control",
                                "rationale": "IP used for command and control",
                            }
                        ],
                    },
                    {
                        "ioc_value": "c2-relay.evil-corp-demo.test",
                        "techniques": [
                            {
                                "technique_id": "T1486",
                                "tactic": "Impact",
                                "rationale": "Data encryption for impact using C2 domain",
                            },
                            {
                                "technique_id": "T1083",
                                "tactic": "Discovery",
                                "rationale": "File discovery before encryption",
                            },
                            {
                                "technique_id": "T9999",
                                "tactic": "Hallucinated",
                                "rationale": "This is a deliberately hallucinated technique",
                            },
                        ],
                    },
                    {
                        "ioc_value": "4a5cd2947eb20214c7d5df3f688a4c18f6b7f5d1e9c2a3b4d5e6f7a8b9c0d1e2",
                        "techniques": [
                            {
                                "technique_id": "T1566",
                                "tactic": "Initial Access",
                                "rationale": "Malicious file hash",
                            }
                        ],
                    },
                    {
                        "ioc_value": "evil-corp-demo.test",
                        "techniques": [
                            {
                                "technique_id": "T1566",
                                "tactic": "Initial Access",
                                "rationale": "Phishing email contains malicious domain",
                            }
                        ],
                    },
                    {
                        "ioc_value": "faktury-online.evil-corp-demo.test",
                        "techniques": [
                            {
                                "technique_id": "T1204.002",
                                "tactic": "Execution",
                                "rationale": "User executed malicious attachment",
                            },
                            {
                                "technique_id": "T9999",
                                "tactic": "Hallucinated",
                                "rationale": "This is a deliberately hallucinated technique",
                            },
                        ],
                    },
                    {
                        "ioc_value": "https://faktury-online.evil-corp-demo.test/download/faktura.exe",
                        "techniques": [
                            {
                                "technique_id": "T1566",
                                "tactic": "Initial Access",
                                "rationale": "Phishing URL",
                            }
                        ],
                    },
                    {
                        "ioc_value": "23b8c1e9392456de3eb13b9046685257bdd640fb06671ad11c80317fa3b1799d",
                        "techniques": [
                            {
                                "technique_id": "T1204.002",
                                "tactic": "Execution",
                                "rationale": "Malicious executable",
                            }
                        ],
                    },
                ]
            }

        if "ransomware" in scenario:
            # IoC extraction response for ransomware
            return {
                "iocs": [
                    {
                        "type": "ipv4",
                        "value": "203.0.113.47",
                        "confidence": "high",
                        "source_artifact": "syslog.log",
                        "rationale": "C2 server IP observed downloading payload",
                    },
                    {
                        "type": "domain",
                        "value": "c2-relay.evil-corp-demo.test",
                        "confidence": "high",
                        "source_artifact": "syslog.log",
                        "rationale": "Ransomware C2 domain with beaconing pattern",
                    },
                    {
                        "type": "sha256",
                        "value": "4a5cd2947eb20214c7d5df3f688a4c18f6b7f5d1e9c2a3b4d5e6f7a8b9c0d1e2",
                        "confidence": "high",
                        "source_artifact": "processes.json",
                        "rationale": "Ransomware executable hash",
                    },
                ],
                "notes": "",
            }
        elif "phishing" in scenario:
            # IoC extraction response for phishing
            return {
                "iocs": [
                    {
                        "type": "domain",
                        "value": "evil-corp-demo.test",
                        "confidence": "high",
                        "source_artifact": "email_headers.eml",
                        "rationale": "Sender domain in phishing email",
                    },
                    {
                        "type": "domain",
                        "value": "faktury-online.evil-corp-demo.test",
                        "confidence": "high",
                        "source_artifact": "browser_history.json",
                        "rationale": "Malicious domain hosting fake invoice download",
                    },
                    {
                        "type": "url",
                        "value": "https://faktury-online.evil-corp-demo.test/download/faktura.exe",
                        "confidence": "high",
                        "source_artifact": "browser_history.json",
                        "rationale": "Direct URL to malicious executable",
                    },
                    {
                        "type": "sha256",
                        "value": "23b8c1e9392456de3eb13b9046685257bdd640fb06671ad11c80317fa3b1799d",
                        "confidence": "high",
                        "source_artifact": "payload_sample.txt",
                        "rationale": "Hash of downloaded payload",
                    },
                ],
                "notes": "",
            }

        # Unknown scenario - return empty response
        return {"iocs": [], "notes": "", "mappings": []}


async def get_llm_client(
    settings: Settings,
    audit: AuditTrail | None = None,
    incident_id: str | None = None,
) -> LlmClient:
    """Factory function to get the appropriate LLM client.

    Args:
        settings: Application settings.
        audit: Optional audit trail for logging.

    Returns:
        AnthropicClient if API key is available and use_stub_llm is False,
        otherwise StubLlmClient.
    """
    # Check if we should use stub
    use_stub = not settings.anthropic_api_key or getattr(settings, "use_stub_llm", False)

    if use_stub:
        if audit:
            await audit.write(
                make_event(
                    incident_id=incident_id or "unknown",
                    actor="llm_client",
                    action="LLM_STUB_MODE_ACTIVE",
                    object="stub_llm",
                )
            )
        logger.warning("LLM operating in stub mode (no API key or stub explicitly enabled)")
        return StubLlmClient(audit)

    # Use real Anthropic client
    return AnthropicClient(
        api_key=settings.anthropic_api_key,
        model=settings.anthropic_model,
        audit=audit or AuditTrail(Path("runtime")),
    )





