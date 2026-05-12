"""Threat Intelligence client with OTX and MISP fallback."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx

from fai.config import Settings
from fai.core.audit import AuditTrail, make_event
from fai.core.models import IoC, IocType, Reputation

logger = logging.getLogger(__name__)


class ThreatIntelClient:
    """Lookup IoC reputation via OTX with MISP local fallback."""

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        settings: Settings,
        audit: AuditTrail,
        misp_fallback_path: Path,
    ) -> None:
        """Initialize Threat Intel client.

        Args:
            http_client: httpx async client for HTTP calls.
            settings: Application settings (for OTX key).
            audit: Audit trail for logging.
            misp_fallback_path: Path to MISP fallback JSON file.
        """
        self.client = http_client
        self.settings = settings
        self.audit = audit
        self.misp_fallback_path = Path(misp_fallback_path)

        # Load MISP fallback once
        self.misp_data: dict[str, dict[str, Any]] = {}
        self._load_misp_fallback()

    def _load_misp_fallback(self) -> None:
        """Load MISP fallback data from JSON."""
        if not self.misp_fallback_path.exists():
            logger.warning(f"MISP fallback file not found: {self.misp_fallback_path}")
            return

        try:
            with open(self.misp_fallback_path, "r", encoding="utf-8") as f:
                self.misp_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load MISP fallback: {e}")

    async def lookup(self, ioc: IoC) -> tuple[Reputation, str]:
        """Lookup IoC reputation.

        Args:
            ioc: IoC to lookup.

        Returns:
            Tuple of (Reputation, source) where source is "otx" or "misp".
        """
        # Only lookup certain types
        supported_types = {
            IocType.IPV4,
            IocType.IPV6,
            IocType.DOMAIN,
            IocType.URL,
            IocType.MD5,
            IocType.SHA1,
            IocType.SHA256,
        }

        if ioc.type not in supported_types:
            return Reputation.UNKNOWN, "unsupported_type"

        # Try OTX first if key is available
        if self.settings.otx_api_key:
            try:
                reputation, source = await self._lookup_otx(ioc)
                return reputation, source
            except Exception as e:
                logger.warning(f"OTX lookup failed for {ioc.value}: {e}")
                await self.audit.write(
                    make_event(
                        incident_id=ioc.incident_id,
                        actor="threat_intel",
                        action="OTX_TIMEOUT_FALLBACK_TO_MISP",
                        object=ioc.value,
                        error=str(e)[:100],
                    )
                )

        # Fallback to MISP
        return self._lookup_misp(ioc)

    async def _lookup_otx(self, ioc: IoC) -> tuple[Reputation, str]:
        """Lookup in AlienVault OTX.

        Args:
            ioc: IoC to lookup.

        Returns:
            Tuple of (Reputation, "otx").

        Raises:
            Exception: On network error, timeout, or invalid response.
        """
        # Build URL based on type
        base_url = "https://otx.alienvault.com/api/v1/indicators"

        if ioc.type == IocType.IPV4:
            url = f"{base_url}/IPv4/{ioc.value}/general"
        elif ioc.type == IocType.IPV6:
            url = f"{base_url}/IPv6/{ioc.value}/general"
        elif ioc.type == IocType.DOMAIN:
            url = f"{base_url}/domain/{ioc.value}/general"
        elif ioc.type == IocType.URL:
            url = f"{base_url}/url/{quote(ioc.value)}/general"
        elif ioc.type in {IocType.MD5, IocType.SHA1, IocType.SHA256}:
            url = f"{base_url}/file/{ioc.value}/general"
        else:
            # Shouldn't happen but handle gracefully
            return Reputation.UNKNOWN, "unsupported"

        # Make request with timeout
        response = await self.client.get(
            url,
            headers={"X-OTX-API-KEY": self.settings.otx_api_key},
            timeout=5.0,
        )

        # Handle errors
        if response.status_code >= 500:
            raise Exception(f"OTX returned {response.status_code}")

        if response.status_code != 200:
            # Not found or other error, treat as clean
            await self.audit.write(
                make_event(
                    incident_id=ioc.incident_id,
                    actor="threat_intel",
                    action="OTX_LOOKUP_RESULT",
                    object=ioc.value,
                    status_code=response.status_code,
                    reputation="clean",
                )
            )
            return Reputation.CLEAN, "otx"

        # Parse response
        data = response.json()
        pulse_count = data.get("pulse_info", {}).get("count", 0)

        reputation = Reputation.MALICIOUS if pulse_count > 0 else Reputation.CLEAN

        await self.audit.write(
            make_event(
                incident_id=ioc.incident_id,
                actor="threat_intel",
                action="OTX_LOOKUP_RESULT",
                object=ioc.value,
                pulse_count=pulse_count,
                reputation=reputation.value,
            )
        )

        return reputation, "otx"

    def _lookup_misp(self, ioc: IoC) -> tuple[Reputation, str]:
        """Lookup in MISP fallback data.

        Args:
            ioc: IoC to lookup.

        Returns:
            Tuple of (Reputation, "misp").
        """
        if ioc.value not in self.misp_data:
            # Default unknown
            return Reputation.UNKNOWN, "misp"

        entry = self.misp_data[ioc.value]
        reputation_str = entry.get("reputation", "unknown")

        if reputation_str == "malicious":
            reputation = Reputation.MALICIOUS
        elif reputation_str == "clean":
            reputation = Reputation.CLEAN
        else:
            reputation = Reputation.UNKNOWN

        return reputation, "misp"

    async def lookup_all(
        self, incident_id: str, iocs: list[IoC]
    ) -> list[IoC]:
        """Lookup all IoCs with a cap on requests.

        Args:
            incident_id: Incident identifier.
            iocs: List of IoCs to lookup.

        Returns:
            Updated list of IoCs with reputation populated.
        """
        max_lookups = 10
        lookups_done = 0

        for ioc in iocs:
            if lookups_done >= max_lookups:
                await self.audit.write(
                    make_event(
                        incident_id=incident_id,
                        actor="threat_intel",
                        action="TI_LOOKUP_CAP_REACHED",
                        object=f"cap={max_lookups}",
                    )
                )
                break

            reputation, source = await self.lookup(ioc)
            ioc.reputation = reputation
            ioc.reputation_source = source
            lookups_done += 1

        return iocs

