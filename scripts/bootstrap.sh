#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MITRE_DIR="${ROOT_DIR}/data/mitre"
MITRE_FILE="${MITRE_DIR}/enterprise-attack.json"

mkdir -p "${ROOT_DIR}/runtime/artifacts" "${ROOT_DIR}/runtime/audit" "${ROOT_DIR}/runtime/reports" "${MITRE_DIR}"

if [[ ! -f "${MITRE_FILE}" ]]; then
  echo "Downloading MITRE ATT&CK Enterprise v14 dataset..." >&2
  python3 - "${MITRE_FILE}" <<'PY'
from __future__ import annotations

import sys
import urllib.error
import urllib.request
from pathlib import Path

url = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"
destination = Path(sys.argv[1])
try:
    with urllib.request.urlopen(url, timeout=60) as response:
        data = response.read()
except urllib.error.URLError as exc:
    raise SystemExit(f"ERROR: failed to download MITRE ATT&CK dataset: {exc}") from exc

destination.write_bytes(data)
PY
fi

python3 - "${MITRE_FILE}" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    payload = json.loads(path.read_text(encoding='utf-8'))
except FileNotFoundError as exc:
    raise SystemExit(f"ERROR: MITRE dataset is missing: {path}") from exc
except json.JSONDecodeError as exc:
    raise SystemExit(f"ERROR: MITRE dataset is not valid JSON: {path}") from exc

if not isinstance(payload, dict):
    raise SystemExit(f"ERROR: MITRE dataset root must be a JSON object: {path}")

objects = payload.get('objects')
if not isinstance(objects, list):
    raise SystemExit(f"ERROR: MITRE dataset is missing an objects array: {path}")

if not any(isinstance(obj, dict) and obj.get('type') == 'attack-pattern' for obj in objects):
    raise SystemExit(f"ERROR: MITRE dataset does not contain any attack-pattern objects: {path}")
PY

echo "MITRE dataset ready at ${MITRE_FILE}" >&2

