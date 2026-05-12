"""SIEM consumer for ingesting alerts and artifacts."""

from __future__ import annotations

import httpx

from fai.core.audit import AuditTrail, make_event
from fai.core.chain_of_custody import ChainOfCustody
from fai.core.models import Artifact


class SiemConsumer:
    """Consumes alerts and artifacts from mock SIEM."""

    def __init__(
        self,
        base_url: str,
        chain_of_custody: ChainOfCustody,
        audit: AuditTrail,
        client: httpx.AsyncClient,
    ) -> None:
        """Initialize the SIEM consumer."""
        self.base_url = base_url.rstrip("/")
        self.chain_of_custody = chain_of_custody
        self.audit = audit
        self.client = client

    async def ingest_alert(self, incident_id: str, scenario: str) -> list[Artifact]:
        """Ingest a mock SIEM alert and all related artifacts."""
        # Trigger a new alert
        alert_response = await self.client.post(
            f"{self.base_url}/mock/siem/trigger/{scenario}"
        )
        alert_response.raise_for_status()
        alert = alert_response.json()
        alert_id = alert["alert_id"]

        # Write audit event for alert received
        event = make_event(
            incident_id=incident_id,
            actor="system",
            action="SIEM_ALERT_RECEIVED",
            object="alert",
            alert_id=alert_id,
        )
        await self.audit.write(event)

        # List artifacts
        artifacts_response = await self.client.get(
            f"{self.base_url}/mock/siem/artifacts/{alert_id}"
        )
        artifacts_response.raise_for_status()
        artifact_list = artifacts_response.json()

        # Download and record each artifact
        recorded_artifacts: list[Artifact] = []
        for artifact_info in artifact_list:
            filename = artifact_info["filename"]
            download_url = artifact_info["download_url"]

            # Download the artifact
            artifact_response = await self.client.get(
                f"{self.base_url}{download_url}"
            )
            artifact_response.raise_for_status()
            content = artifact_response.content

            # Record to chain of custody
            artifact = await self.chain_of_custody.record_artifact(
                incident_id=incident_id,
                filename=filename,
                content=content,
                source="siem",
            )
            recorded_artifacts.append(artifact)

        return recorded_artifacts

