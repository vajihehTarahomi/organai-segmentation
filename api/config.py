"""Runtime configuration — all via environment variables, no hardcoded paths."""
import os
from pathlib import Path

# Where per-job data (uploads + segmentation masks) is stored.
DATA_DIR = Path(os.environ.get("ORGANAI_DATA_DIR", "/data")).resolve()

# Inference device: "cpu" or "gpu".
DEVICE = os.environ.get("ORGANAI_DEVICE", "cpu")

# TotalSegmentator fast mode (3mm) — faster, good enough for volumetry.
FAST = os.environ.get("ORGANAI_FAST", "true").lower() in ("1", "true", "yes")

# Max upload size in megabytes.
MAX_UPLOAD_MB = int(os.environ.get("ORGANAI_MAX_UPLOAD_MB", "500"))

# How many segmentation jobs may run concurrently.
MAX_WORKERS = int(os.environ.get("ORGANAI_MAX_WORKERS", "1"))

# Optional bearer token; if set, mutating endpoints require it.
API_TOKEN = os.environ.get("ORGANAI_API_TOKEN", "")

DATA_DIR.mkdir(parents=True, exist_ok=True)
