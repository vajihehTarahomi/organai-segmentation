"""OrganAI FastAPI service — on-demand CT organ segmentation & volumetry.

Endpoints:
  GET  /health                     liveness
  POST /api/jobs                   upload a CT (.nii/.nii.gz) -> starts segmentation
  GET  /api/jobs                   list jobs
  GET  /api/jobs/{id}              job status + volumes when done
  GET  /api/jobs/{id}/slice/{z}    rendered slice PNG (base64) with overlays
  GET  /                           minimal upload UI
"""
import os
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends
from fastapi.responses import JSONResponse, HTMLResponse

from .config import MAX_UPLOAD_MB, API_TOKEN, DEVICE, FAST
from .inference import render_slice, volumes_payload
from . import jobs as jobstore
from .samples import load_samples

app = FastAPI(title="OrganAI", version="1.0.0")

STATIC = Path(__file__).parent / "static"

# Register any pre-segmented demo cases listed in the samples manifest.
SAMPLES = load_samples()


def require_token(authorization: str = Header(default="")):
    """Enforce a bearer token on mutating routes when ORGANAI_API_TOKEN is set."""
    if not API_TOKEN:
        return
    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="invalid or missing token")


@app.get("/health")
def health():
    return {"status": "ok", "device": DEVICE, "fast": FAST}


@app.get("/", response_class=HTMLResponse)
def index():
    f = STATIC / "index.html"
    if f.exists():
        return f.read_text(encoding="utf-8")
    return "<h1>OrganAI</h1><p>POST a CT to /api/jobs</p>"


@app.post("/api/jobs")
async def create_job(file: UploadFile = File(...), _=Depends(require_token)):
    name = file.filename or "upload"
    if not (name.endswith(".nii") or name.endswith(".nii.gz")):
        raise HTTPException(status_code=400, detail="file must be .nii or .nii.gz")
    raw = await file.read()
    if len(raw) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"file exceeds {MAX_UPLOAD_MB} MB")
    if not raw:
        raise HTTPException(status_code=400, detail="empty file")

    # Reject macOS AppleDouble sidecars (._file) that datasets often ship alongside
    # the real data — they share the .nii.gz name but are tiny metadata blobs.
    if raw[:4] == b"\x00\x05\x16\x07":
        raise HTTPException(
            status_code=400,
            detail="this is a macOS metadata sidecar (a '._' file), not a CT. "
                   "Upload the real file — e.g. 'spleen_13.nii.gz', not '._spleen_13.nii.gz'.",
        )
    # A .nii.gz must start with the gzip magic bytes.
    if name.endswith(".nii.gz") and raw[:2] != b"\x1f\x8b":
        raise HTTPException(
            status_code=400,
            detail="file is named .nii.gz but is not gzip-compressed — it may be "
                   "corrupt, truncated, or the wrong file.",
        )

    job = jobstore.create_job(name, raw)
    return {"id": job["id"], "status": job["status"]}


@app.get("/api/samples")
def list_samples():
    """Pre-segmented demo cases the user can view instantly (no upload/wait)."""
    return SAMPLES


@app.get("/api/jobs")
def list_jobs():
    return [
        {"id": j["id"], "filename": j["filename"], "status": j["status"]}
        for j in jobstore.list_jobs()
    ]


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str):
    job = jobstore.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    payload = {
        "id": job["id"], "filename": job["filename"], "status": job["status"],
        "error": job.get("error"),
    }
    if job["status"] == "done" and job.get("result"):
        r = job["result"]
        payload.update({
            "voxel_mm": r["voxel_mm"], "shape": r["shape"],
            "n_slices": r["n_slices"], "n_masks": r["n_masks"],
            "organs": volumes_payload(r["volumes"]),
            "model": "TotalSegmentator v2 (fast/3mm)" if FAST else "TotalSegmentator v2",
        })
    return payload


@app.get("/api/jobs/{job_id}/slice/{z}")
def job_slice(job_id: str, z: int, wc: int = 40, ww: int = 400):
    job = jobstore.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    if job["status"] != "done":
        raise HTTPException(status_code=409, detail=f"job not ready ({job['status']})")
    img = render_slice(job["ct_path"], job["seg_dir"], z, wc, ww)
    return JSONResponse({"image": img, "slice": int(z)})
