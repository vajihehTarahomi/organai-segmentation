"""In-process job store with a bounded background worker pool.

Jobs persist their input + masks on disk under DATA_DIR/<job_id>/, so slice
rendering and volumes survive across requests. Job *metadata* lives in memory;
on restart, completed jobs are rediscovered from disk.
"""
import json
import time
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .config import DATA_DIR, MAX_WORKERS
from .inference import run_segmentation, compute_volumes

_executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
_jobs = {}
_lock = threading.Lock()


def _job_dir(job_id: str) -> Path:
    return DATA_DIR / job_id


def _meta_path(job_id: str) -> Path:
    return _job_dir(job_id) / "job.json"


def _save_meta(job: dict) -> None:
    with open(_meta_path(job["id"]), "w") as f:
        json.dump(job, f, indent=2)


def create_job(filename: str, raw: bytes) -> dict:
    job_id = uuid.uuid4().hex[:12]
    d = _job_dir(job_id)
    d.mkdir(parents=True, exist_ok=True)
    ct_path = d / "input.nii.gz"
    ct_path.write_bytes(raw)

    job = {
        "id": job_id,
        "filename": filename,
        "status": "queued",
        "created": time.time(),
        "ct_path": str(ct_path),
        "seg_dir": str(d / "seg"),
        "error": None,
        "result": None,
    }
    with _lock:
        _jobs[job_id] = job
    _save_meta(job)
    _executor.submit(_run, job_id)
    return job


def _run(job_id: str) -> None:
    with _lock:
        job = _jobs[job_id]
        job["status"] = "running"
        _save_meta(job)
    try:
        run_segmentation(job["ct_path"], job["seg_dir"])
        result = compute_volumes(job["ct_path"], job["seg_dir"])
        with _lock:
            job["status"] = "done"
            job["result"] = result
            _save_meta(job)
    except Exception as e:  # noqa: BLE001 — surface any failure to the client
        with _lock:
            job["status"] = "error"
            job["error"] = str(e)
            _save_meta(job)


def register_sample(sample_id: str, name: str, ct_path: str, seg_dir: str) -> None:
    """Register a pre-segmented demo case as an already-'done' job.

    Volumes are computed lazily on first access so startup stays fast.
    """
    with _lock:
        if sample_id in _jobs:
            return
        _jobs[sample_id] = {
            "id": sample_id, "filename": name, "status": "done", "kind": "sample",
            "created": time.time(), "ct_path": ct_path, "seg_dir": seg_dir,
            "error": None, "result": None,
        }


def get_job(job_id: str):
    with _lock:
        job = _jobs.get(job_id)
    if job is None:
        # fall back to disk (e.g. after a restart)
        mp = _meta_path(job_id)
        if mp.exists():
            job = json.loads(mp.read_text())
            with _lock:
                _jobs[job_id] = job
        else:
            return None
    # lazily compute volumes for sample cases on first access
    if job.get("kind") == "sample" and job.get("result") is None:
        from .inference import compute_volumes
        result = compute_volumes(job["ct_path"], job["seg_dir"])
        with _lock:
            job["result"] = result
    return dict(job)


def list_jobs():
    with _lock:
        return [dict(j) for j in _jobs.values()]
