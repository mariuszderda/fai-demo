"""MITRE ATT&CK mapping with hallucination protection."""

from __future__ import annotations

import logging

from fai.analysis.llm_client import LlmClient, LlmResponseError
from fai.analysis.prompts import (
    SYSTEM_PROMPT_MITRE_MAPPING,
    build_mitre_mapping_user_content,
)
from fai.core.audit import AuditTrail, make_event
from fai.core.models import IoC
from fai.mitre.loader import MitreLoader

logger = logging.getLogger(__name__)


class MitreMapper:
    """Map IoCs to MITRE ATT&CK techniques with hallucination protection."""

    def __init__(
        self,
        llm_client: LlmClient,
        mitre_loader: MitreLoader,
        audit: AuditTrail,
    ) -> None:
        """Initialize MITRE mapper.

        Args:
            llm_client: LLM client for mapping.
            mitre_loader: MITRE dataset loader.
            audit: Audit trail for logging.
        """
        self.llm = llm_client
        self.mitre_loader = mitre_loader
        self.audit = audit

    async def map_iocs(self, incident_id: str, iocs: list[IoC]) -> list[IoC]:
        """Map IoCs to MITRE techniques.

        Args:
            incident_id: Incident identifier.
            iocs: List of IoCs to map.

        Returns:
            Updated list of IoCs with mitre_technique_ids populated.
        """
        if not iocs:
            return iocs

        # Build user content
        user_content = build_mitre_mapping_user_content(iocs)

        # Call LLM
        try:
            response = await self.llm.complete_json(
                SYSTEM_PROMPT_MITRE_MAPPING,
                user_content,
                incident_id=incident_id,
            )
        except LlmResponseError as e:
            logger.error(f"MITRE mapping failed: {e}")
            raise

        # Validate response schema
        if "mappings" not in response:
            raise ValueError("LLM response missing 'mappings' field")

        # Build a map of IoC value -> techniques for quick lookup
        ioc_map = {ioc.value: ioc for ioc in iocs}

        # Process each mapping
        for mapping in response.get("mappings", []):
            ioc_value = mapping.get("ioc_value")
            if not ioc_value or ioc_value not in ioc_map:
                continue

            ioc = ioc_map[ioc_value]
            valid_techniques: list[str] = []

            # Validate each technique
            for technique_data in mapping.get("techniques", []):
                technique_id = technique_data.get("technique_id")

                if not technique_id:
                    continue

                # Check if technique is valid
                if self.mitre_loader.is_valid_technique(technique_id):
                    valid_techniques.append(technique_id)
                else:
                    # Log hallucination
                    await self.audit.write(
                        make_event(
                            incident_id=incident_id,
                            actor="mitre_mapper",
                            action="HALLUCINATION_REJECTED",
                            object=ioc_value,
                            technique_id=technique_id,
                        )
                    )
                    logger.warning(
                        f"Hallucinated technique rejected: {technique_id} for IoC {ioc_value}"
                    )

            # Update IoC with valid techniques
            ioc.mitre_technique_ids = valid_techniques

        return iocs

