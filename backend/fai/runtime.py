"""Shared runtime factories and process-wide singletons."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import httpx

from fai.analysis.llm_client import AnthropicClient, StubLlmClient
from fai.analysis.mitre_mapper import MitreLoader
from fai.analysis.threat_intel import ThreatIntelClient
from fai.config import Settings, get_settings
from fai.core.audit import AuditTrail
from fai.core.chain_of_custody import ChainOfCustody
from fai.core.events import EventBus, get_event_bus
from fai.ingestion.siem_consumer import SiemConsumer
from fai.reporting.generator import ReportGenerator

_internal_http_client: httpx.AsyncClient | None = None


@lru_cache(maxsize=1)
def get_runtime_dir() -> Path:
	"""Return the repository runtime directory."""
	return Path(__file__).resolve().parents[2] / "runtime"


@lru_cache(maxsize=1)
def get_settings_cached() -> Settings:
	"""Return the cached application settings instance."""
	return get_settings()


@lru_cache(maxsize=1)
def get_audit_trail() -> AuditTrail:
	"""Return the shared audit trail instance."""
	return AuditTrail(get_runtime_dir())


@lru_cache(maxsize=1)
def get_chain_of_custody() -> ChainOfCustody:
	"""Return the shared chain-of-custody instance."""
	return ChainOfCustody(get_runtime_dir(), get_audit_trail())


@lru_cache(maxsize=1)
def get_event_bus_singleton() -> EventBus:
	"""Return the shared SSE event bus instance."""
	return get_event_bus()


def set_internal_http_client(client: httpx.AsyncClient) -> None:
	"""Register the internal app-to-app HTTP client."""
	global _internal_http_client
	_internal_http_client = client


def clear_internal_http_client() -> None:
	"""Clear the registered internal HTTP client."""
	global _internal_http_client
	_internal_http_client = None


def get_internal_http_client() -> httpx.AsyncClient:
	"""Return the internal HTTP client used by mocked services."""
	if _internal_http_client is None:
		raise RuntimeError("Internal HTTP client has not been initialized")
	return _internal_http_client


@lru_cache(maxsize=1)
def get_llm_client() -> StubLlmClient | AnthropicClient:
	"""Return the configured LLM client."""
	settings = get_settings_cached()
	audit = get_audit_trail()
	if not settings.anthropic_api_key or settings.use_stub_llm:
		return StubLlmClient(audit)
	return AnthropicClient(settings.anthropic_api_key, settings.anthropic_model, audit)


@lru_cache(maxsize=1)
def get_mitre_loader() -> MitreLoader:
	"""Return the shared MITRE ATT&CK loader."""
	dataset_path = get_runtime_dir().parent / "data" / "mitre" / "enterprise-attack.json"
	return MitreLoader(dataset_path)


def get_siem_consumer() -> SiemConsumer:
	"""Return the SIEM consumer configured for internal mock routes."""
	return SiemConsumer(
		base_url="http://testserver",
		chain_of_custody=get_chain_of_custody(),
		audit=get_audit_trail(),
		client=get_internal_http_client(),
	)


@lru_cache(maxsize=1)
def get_threat_intel_client() -> ThreatIntelClient:
	"""Return the threat-intelligence client."""
	settings = get_settings_cached()
	audit = get_audit_trail()
	http_client = httpx.AsyncClient()
	misp_fallback_path = get_runtime_dir().parent / "data" / "misp_fallback.json"
	return ThreatIntelClient(http_client, settings, audit, misp_fallback_path)


@lru_cache(maxsize=1)
def get_report_generator() -> ReportGenerator:
	"""Return the shared report generator."""
	return ReportGenerator(
		llm_client=get_llm_client(),
		audit=get_audit_trail(),
		runtime_dir=get_runtime_dir(),
	)

