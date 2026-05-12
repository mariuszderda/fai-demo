"""IoC extraction from artifacts using LLM."""

from __future__ import annotations

import ipaddress
import logging
from uuid import uuid4

from fai.analysis.llm_client import LlmClient, LlmResponseError
from fai.analysis.prompts import (
    SYSTEM_PROMPT_IOC_EXTRACTION,
    build_ioc_extraction_user_content,
)
from fai.core.audit import AuditTrail, make_event
from fai.core.models import Artifact, Confidence, IoC, IocStatus, IocType

logger = logging.getLogger(__name__)


class IocExtractor:
    """Extract Indicators of Compromise from artifacts using LLM."""

    def __init__(self, llm_client: LlmClient, audit: AuditTrail) -> None:
        """Initialize IoC extractor.

        Args:
            llm_client: LLM client for extraction.
            audit: Audit trail for logging.
        """
        self.llm = llm_client
        self.audit = audit

    async def extract(
        self,
        incident_id: str,
        artifacts: list[Artifact],
        artifact_contents: dict[str, str],
    ) -> list[IoC]:
        """Extract IoCs from artifacts.

        Args:
            incident_id: Incident identifier.
            artifacts: List of artifacts.
            artifact_contents: Dict mapping artifact filename to content.

        Returns:
            List of extracted IoCs (excluding filtered ones).
        """
        # Build user content
        user_content = build_ioc_extraction_user_content(artifacts, artifact_contents)

        # Call LLM
        try:
            response = await self.llm.complete_json(
                SYSTEM_PROMPT_IOC_EXTRACTION,
                user_content,
                incident_id=incident_id,
            )
        except LlmResponseError as e:
            logger.error(f"IoC extraction failed: {e}")
            raise

        # Validate response schema
        if "iocs" not in response:
            raise ValueError("LLM response missing 'iocs' field")

        iocs: list[IoC] = []

        # Process each IoC
        for ioc_data in response.get("iocs", []):
            try:
                ioc_type = IocType(ioc_data["type"])
                ioc_value = ioc_data["value"]

                # Filter private IPs (RFC1918, loopback, link-local)
                # Note: This excludes private/internal addresses but allows reserved/documentation addresses
                if ioc_type == IocType.IPV4:
                    try:
                        ip = ipaddress.ip_address(ioc_value)
                        # Check for loopback or link-local
                        if ip.is_loopback or ip.is_link_local:
                            # Write audit event and skip
                            await self.audit.write(
                                make_event(
                                    incident_id=incident_id,
                                    actor="ioc_extractor",
                                    action="IOC_FILTERED_PRIVATE_IP",
                                    object=ioc_value,
                                )
                            )
                            continue
                        # Check for RFC1918 (private ranges)
                        if isinstance(ip, ipaddress.IPv4Address):
                            if (
                                (
                                    ipaddress.IPv4Address("10.0.0.0")
                                    <= ip
                                    <= ipaddress.IPv4Address("10.255.255.255")
                                )
                                or (
                                    ipaddress.IPv4Address("172.16.0.0")
                                    <= ip
                                    <= ipaddress.IPv4Address("172.31.255.255")
                                )
                                or (
                                    ipaddress.IPv4Address("192.168.0.0")
                                    <= ip
                                    <= ipaddress.IPv4Address("192.168.255.255")
                                )
                            ):
                                # Write audit event and skip
                                await self.audit.write(
                                    make_event(
                                        incident_id=incident_id,
                                        actor="ioc_extractor",
                                        action="IOC_FILTERED_PRIVATE_IP",
                                        object=ioc_value,
                                    )
                                )
                                continue
                    except ValueError:
                        # Invalid IP, skip
                        logger.warning(f"Invalid IPv4 address: {ioc_value}")
                        continue

                # Create IoC
                ioc = IoC(
                    incident_id=incident_id,
                    type=ioc_type,
                    value=ioc_value,
                    confidence=Confidence(ioc_data.get("confidence", "low")),
                    source_artifact_id=ioc_data.get("source_artifact", "unknown"),
                    rationale=ioc_data.get("rationale", ""),
                    status=IocStatus.PENDING_REVIEW,
                )
                iocs.append(ioc)
            except (KeyError, ValueError) as e:
                logger.warning(f"Invalid IoC data: {ioc_data}: {e}")
                continue

        # Check for prompt injection attempts in notes field
        if response.get("notes"):
            await self.audit.write(
                make_event(
                    incident_id=incident_id,
                    actor="ioc_extractor",
                    action="PROMPT_INJECTION_DETECTED",
                    object="ioc_extraction",
                    notes=response["notes"][:200],  # Truncate for safety
                )
            )

        return iocs

