"""MITRE ATT&CK dataset loader and validator."""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from fai.core.models import MitreTechnique

logger = logging.getLogger(__name__)


# MITRE phase_name in kill_chain_phases sometimes uses non-canonical names.
# This map normalizes them to canonical tactic keys.
_PHASE_NAME_ALIASES = {
    "stealth": "defense-evasion",
}


class MitreLoader:
    """Load and validate MITRE ATT&CK techniques."""

    def __init__(self, dataset_path: Path) -> None:
        self.dataset_path = Path(dataset_path)
        self.techniques: dict[str, MitreTechnique] = {}
        self.tactic_map: dict[str, list[str]] = {}
        self._load_dataset()

    def _load_dataset(self) -> None:
        if not self.dataset_path.exists():
            logger.warning(f"MITRE dataset not found at {self.dataset_path}")
            return

        try:
            with open(self.dataset_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load MITRE dataset: {e}")
            return

        if "objects" not in data:
            logger.warning("MITRE dataset missing 'objects' field")
            return

        for obj in data.get("objects", []):
            if obj.get("type") != "attack-pattern":
                continue
            if obj.get("revoked") or obj.get("x_mitre_deprecated"):
                continue

            technique_id = None
            for ref in obj.get("external_references", []):
                if ref.get("source_name") == "mitre-attack":
                    technique_id = ref.get("external_id")
                    break
            if not technique_id:
                continue

            kill_chain = obj.get("kill_chain_phases", [])
            tactic_keys: list[str] = []
            for phase in kill_chain:
                if phase.get("kill_chain_name") != "mitre-attack":
                    continue
                raw = phase.get("phase_name", "")
                if not raw:
                    continue
                canonical = _PHASE_NAME_ALIASES.get(raw, raw)
                tactic_keys.append(canonical)

            primary_tactic = tactic_keys[0] if tactic_keys else "unknown"

            tech = MitreTechnique(
                technique_id=technique_id,
                name=obj.get("name", ""),
                tactic=primary_tactic,
            )
            self.techniques[technique_id] = tech

            for tactic_key in tactic_keys:
                self.tactic_map.setdefault(tactic_key, []).append(technique_id)

        logger.info(
            f"Loaded {len(self.techniques)} techniques from MITRE dataset "
            f"({len(self.tactic_map)} tactic buckets)"
        )

    def is_valid_technique(self, technique_id: str) -> bool:
        return technique_id in self.techniques

    def get_technique(self, technique_id: str) -> MitreTechnique | None:
        return self.techniques.get(technique_id)

    @lru_cache(maxsize=1)
    def get_matrix(self) -> dict[str, Any]:
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

            parents: dict[str, dict[str, Any]] = {}
            subs_by_parent: dict[str, list[dict[str, Any]]] = {}

            for tech_id in sorted(technique_ids):
                tech = self.techniques.get(tech_id)
                if not tech:
                    continue

                if "." in tech_id:
                    parent_id = tech_id.split(".")[0]
                    subs_by_parent.setdefault(parent_id, []).append({
                        "id": tech_id,
                        "name": tech.name,
                    })
                else:
                    parents[tech_id] = {
                        "id": tech_id,
                        "name": tech.name,
                        "sub_techniques": [],
                    }

            for parent_id, subs in subs_by_parent.items():
                if parent_id in parents:
                    parents[parent_id]["sub_techniques"] = subs

            techniques_list = sorted(parents.values(), key=lambda t: t["id"])

            tactics_list.append({
                "id": tactic_meta["id"],
                "name": tactic_meta["name"],
                "key": tactic_key,
                "techniques": techniques_list,
            })

        return {"tactics": tactics_list}