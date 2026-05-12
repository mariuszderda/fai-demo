"""Chain of custody implementation."""

from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .audit import AuditTrail, make_event
from .models import Artifact


class ChainOfCustody:
    """Chain of custody tracker with integrity verification."""

    def __init__(self, runtime_dir: Path, audit: AuditTrail) -> None:
        """Initialize chain of custody with runtime directory and audit trail."""
        self.runtime_dir = Path(runtime_dir)
        self.artifacts_dir = self.runtime_dir / "artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.audit = audit
        self._locks: dict[str, asyncio.Lock] = {}

    def _get_lock(self, incident_id: str) -> asyncio.Lock:
        """Get or create a lock for an incident."""
        if incident_id not in self._locks:
            self._locks[incident_id] = asyncio.Lock()
        return self._locks[incident_id]

    def _compute_sha256(self, content: bytes) -> str:
        """Compute SHA-256 hash of content."""
        return hashlib.sha256(content).hexdigest()

    async def record_artifact(
        self,
        incident_id: str,
        filename: str,
        content: bytes,
        source: str = "siem",
    ) -> Artifact:
        """Record an artifact with integrity verification."""
        lock = self._get_lock(incident_id)
        async with lock:
            artifact_id = str(uuid4())
            sha256_hash = self._compute_sha256(content)

            # Create incident directory
            incident_artifacts_dir = self.artifacts_dir / incident_id
            incident_artifacts_dir.mkdir(parents=True, exist_ok=True)

            # Write content to disk
            artifact_filename = f"{artifact_id}__{filename}"
            artifact_path = incident_artifacts_dir / artifact_filename
            with open(artifact_path, "wb") as f:
                f.write(content)

            # Create artifact model
            now = datetime.now(timezone.utc)
            artifact = Artifact(
                id=artifact_id,
                incident_id=incident_id,
                filename=filename,
                source=source,
                size_bytes=len(content),
                sha256=sha256_hash,
                collected_at_utc=now,
                collector_version="0.1.0",
            )

            # Append to CoC log
            coc_path = incident_artifacts_dir / "coc.jsonl"
            with open(coc_path, "a", encoding="utf-8") as f:
                f.write(artifact.model_dump_json() + "\n")

            # Write audit event
            event = make_event(
                incident_id=incident_id,
                actor="system",
                action="ARTIFACT_COLLECTED",
                object=filename,
                sha256=sha256_hash,
            )
            await self.audit.write(event)

            return artifact

    async def verify_integrity(self, incident_id: str) -> list[dict]:
        """Verify integrity of all artifacts in chain of custody."""
        incident_artifacts_dir = self.artifacts_dir / incident_id
        coc_path = incident_artifacts_dir / "coc.jsonl"

        mismatches: list[dict] = []

        if coc_path.exists():
            with open(coc_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        artifact_dict = json.loads(line)
                        artifact_id = artifact_dict["id"]
                        expected_sha256 = artifact_dict["sha256"]
                        filename = artifact_dict["filename"]

                        # Find artifact file
                        artifact_filename = f"{artifact_id}__{filename}"
                        artifact_path = incident_artifacts_dir / artifact_filename

                        if artifact_path.exists():
                            artifact_content = artifact_path.read_bytes()
                            actual_sha256 = self._compute_sha256(artifact_content)
                            if actual_sha256 != expected_sha256:
                                mismatches.append(
                                    {
                                        "artifact_id": artifact_id,
                                        "filename": filename,
                                        "expected_sha256": expected_sha256,
                                        "actual_sha256": actual_sha256,
                                    }
                                )

        # Write audit event
        event = make_event(
            incident_id=incident_id,
            actor="system",
            action="COC_VERIFIED",
            object="chain_of_custody",
            mismatches_count=len(mismatches),
        )
        await self.audit.write(event)

        return mismatches

