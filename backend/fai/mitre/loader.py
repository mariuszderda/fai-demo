"""MITRE ATT&CK dataset loader and validator."""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from fai.core.models import MitreTechnique

logger = logging.getLogger(__name__)


class MitreLoader:
    """Load and validate MITRE ATT&CK techniques."""

    def __init__(self, dataset_path: Path) -> None:
        """Initialize MITRE loader.

        Args:
            dataset_path: Path to enterprise-attack.json file.
        """
        self.dataset_path = Path(dataset_path)
        self.techniques: dict[str, MitreTechnique] = {}
        self.tactic_map: dict[str, list[str]] = {}  # tactic -> [technique_ids]
        self._load_dataset()

    def _load_dataset(self) -> None:
        """Load and parse the MITRE dataset."""
        if not self.dataset_path.exists():
            logger.warning(f"MITRE dataset not found at {self.dataset_path}")
            return

        try:
            with open(self.dataset_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load MITRE dataset: {e}")
            return

        # Extract technique objects
        if "objects" not in data:
            logger.warning("MITRE dataset missing 'objects' field")
            return

        for obj in data.get("objects", []):
            if obj.get("type") == "attack-pattern":
                # Extract technique ID
                ext_refs = obj.get("external_references", [])
                technique_id = None
                for ref in ext_refs:
                    if ref.get("source_name") == "mitre-attack":
                        technique_id = ref.get("external_id")
                        break

                if not technique_id:
                    continue

                # Extract tactic
                tactics = obj.get("x_mitre_tactics", [])
                tactic = tactics[0] if tactics else "Unknown"

                # Create technique object
                tech = MitreTechnique(
                    technique_id=technique_id,
                    name=obj.get("name", ""),
                    tactic=tactic,
                )
                self.techniques[technique_id] = tech

                # Map tactic -> techniques
                if tactic not in self.tactic_map:
                    self.tactic_map[tactic] = []
                self.tactic_map[tactic].append(technique_id)

        logger.info(f"Loaded {len(self.techniques)} techniques from MITRE dataset")

    def is_valid_technique(self, technique_id: str) -> bool:
        """Check if a technique ID is valid.

        Args:
            technique_id: Technique ID to validate (e.g. T1234 or T1234.567).

        Returns:
            True if valid, False otherwise.
        """
        return technique_id in self.techniques

    def get_technique(self, technique_id: str) -> MitreTechnique | None:
        """Get technique metadata.

        Args:
            technique_id: Technique ID to retrieve.

        Returns:
            MitreTechnique object if found, None otherwise.
        """
        return self.techniques.get(technique_id)

    @lru_cache(maxsize=1)
    def get_matrix(self) -> dict[str, Any]:
        """Get frontend-friendly MITRE matrix structure.

        Returns:
            Dict with tactics and techniques organized hierarchically.
        """
        # Map tactic names to canonical form with IDs
        tactic_info = {
            "reconnaissance": {"id": "TA0043", "name": "Reconnaissance"},
            "resource-development": {"id": "TA0042", "name": "Resource Development"},
            "initial-access": {"id": "TA0001", "name": "Initial Access"},
            "execution": {"id": "TA0002", "name": "Execution"},
            "persistence": {"id": "TA0003", "name": "Persistence"},
            "privilege-escalation": {"id": "TA0004", "name": "Privilege Escalation"},
            "defense-evasion": {"id": "TA0005", "name": "Defense Evasion"},
            "credential-access": {"id": "TA0006", "name": "Credential Access"},
            "discovery": {"id": "TA0007", "name": "Discovery"},
            "lateral-movement": {"id": "TA0008", "name": "Lateral Movement"},
            "collection": {"id": "TA0009", "name": "Collection"},
            "command-and-control": {"id": "TA0011", "name": "Command and Control"},
            "exfiltration": {"id": "TA0010", "name": "Exfiltration"},
            "impact": {"id": "TA0040", "name": "Impact"},
        }

        tactics_list = []

        for tactic_key, tactic_meta in tactic_info.items():
            technique_ids = self.tactic_map.get(tactic_key, [])

            techniques = []
            for tech_id in sorted(technique_ids):
                tech = self.techniques.get(tech_id)
                if tech:
                    tech_dict = {
                        "id": tech_id,
                        "name": tech.name,
                        "sub_techniques": [],  # Could be expanded if sub-techniques exist
                    }
                    techniques.append(tech_dict)

            tactic_dict = {
                "id": tactic_meta["id"],
                "name": tactic_meta["name"],
                "key": tactic_key,
                "techniques": techniques,
            }
            tactics_list.append(tactic_dict)

        return {
            "tactics": tactics_list,
        }

