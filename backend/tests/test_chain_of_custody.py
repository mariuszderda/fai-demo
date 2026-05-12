"""Tests for chain of custody."""

from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path

import pytest

from fai.core.audit import AuditTrail
from fai.core.chain_of_custody import ChainOfCustody


@pytest.mark.asyncio
async def test_record_artifact() -> None:
    """Test recording an artifact."""
    with tempfile.TemporaryDirectory() as tmpdir:
        audit = AuditTrail(Path(tmpdir))
        coc = ChainOfCustody(Path(tmpdir), audit)

        content = b"test artifact content"
        artifact = await coc.record_artifact(
            incident_id="incident1",
            filename="test.txt",
            content=content,
            source="siem",
        )

        assert artifact.incident_id == "incident1"
        assert artifact.filename == "test.txt"
        assert artifact.source == "siem"
        assert artifact.size_bytes == len(content)
        assert len(artifact.sha256) == 64  # SHA-256 is 64 hex chars

        # Verify artifact file exists
        artifact_path = (
            Path(tmpdir) / "artifacts" / "incident1"
            / f"{artifact.id}__test.txt"
        )
        assert artifact_path.exists()
        assert artifact_path.read_bytes() == content

        # Verify CoC log has the entry
        coc_path = Path(tmpdir) / "artifacts" / "incident1" / "coc.jsonl"
        assert coc_path.exists()
        with open(coc_path, "r", encoding="utf-8") as f:
            log_line = f.readline()
            log_entry = json.loads(log_line)
            assert log_entry["filename"] == "test.txt"
            assert log_entry["sha256"] == artifact.sha256


@pytest.mark.asyncio
async def test_verify_integrity_no_tampering() -> None:
    """Test integrity verification with no tampering."""
    with tempfile.TemporaryDirectory() as tmpdir:
        audit = AuditTrail(Path(tmpdir))
        coc = ChainOfCustody(Path(tmpdir), audit)

        content = b"clean artifact"
        artifact = await coc.record_artifact(
            incident_id="incident1",
            filename="clean.txt",
            content=content,
        )

        mismatches = await coc.verify_integrity("incident1")
        assert len(mismatches) == 0


@pytest.mark.asyncio
async def test_verify_integrity_with_tampering() -> None:
    """Test integrity verification detects tampering."""
    with tempfile.TemporaryDirectory() as tmpdir:
        audit = AuditTrail(Path(tmpdir))
        coc = ChainOfCustody(Path(tmpdir), audit)

        content = b"original artifact"
        artifact = await coc.record_artifact(
            incident_id="incident1",
            filename="artifact.txt",
            content=content,
        )

        # Tamper with the artifact on disk
        artifact_path = (
            Path(tmpdir) / "artifacts" / "incident1"
            / f"{artifact.id}__artifact.txt"
        )
        with open(artifact_path, "wb") as f:
            f.write(b"tampered content")

        # Verify should find the mismatch
        mismatches = await coc.verify_integrity("incident1")
        assert len(mismatches) == 1
        assert mismatches[0]["filename"] == "artifact.txt"
        assert mismatches[0]["expected_sha256"] == artifact.sha256
        assert mismatches[0]["expected_sha256"] != mismatches[0]["actual_sha256"]


@pytest.mark.asyncio
async def test_concurrent_artifact_recording() -> None:
    """Test concurrent artifact recording."""
    with tempfile.TemporaryDirectory() as tmpdir:
        audit = AuditTrail(Path(tmpdir))
        coc = ChainOfCustody(Path(tmpdir), audit)

        async def record_artifact(i: int) -> None:
            content = f"artifact {i}".encode()
            await coc.record_artifact(
                incident_id="incident1",
                filename=f"file{i}.txt",
                content=content,
            )

        # Record 10 artifacts concurrently
        await asyncio.gather(*[record_artifact(i) for i in range(10)])

        # Verify all 10 appear in CoC log
        coc_path = Path(tmpdir) / "artifacts" / "incident1" / "coc.jsonl"
        with open(coc_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 10

        # Verify integrity
        mismatches = await coc.verify_integrity("incident1")
        assert len(mismatches) == 0

