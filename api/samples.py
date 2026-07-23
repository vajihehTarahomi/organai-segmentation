"""Pre-segmented demo cases, loaded from a JSON manifest.

Manifest location: $ORGANAI_SAMPLES_MANIFEST (default: api/samples.json).
Each entry: {"id","name","ct","seg"} where ct/seg are paths that exist on the
server. Entries whose files are missing are skipped, so the manifest can list
optional demos without breaking startup.
"""
import os
import json
from pathlib import Path

from . import jobs as jobstore

DEFAULT_MANIFEST = Path(__file__).parent / "samples.json"


def load_samples() -> list:
    path = Path(os.environ.get("ORGANAI_SAMPLES_MANIFEST", DEFAULT_MANIFEST))
    if not path.exists():
        return []
    try:
        items = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    base = path.parent  # relative ct/seg paths resolve against the manifest's dir
    available = []
    for it in items:
        ct = str((base / it.get("ct", "")).resolve()) if not os.path.isabs(it.get("ct", "")) else it["ct"]
        seg = str((base / it.get("seg", "")).resolve()) if not os.path.isabs(it.get("seg", "")) else it["seg"]
        if os.path.exists(ct) and os.path.isdir(seg):
            jobstore.register_sample(it["id"], it["name"], ct, seg)
            available.append({"id": it["id"], "name": it["name"]})
    return available
