# OrganAI — Abdominal Organ Segmentation & Volumetry

AI-powered organ segmentation and volumetry for abdominal CT, built on
[TotalSegmentator](https://github.com/wasserth/TotalSegmentator).
Upload a CT scan → get organ volumes (liver, spleen, kidneys, pancreas, …) flagged
against clinical normal ranges, with an interactive slice viewer.

- Segments **117 anatomical structures** automatically
- Computes **organ volumes in mL** and flags high / low / normal
- Runs on **CPU in ~4 minutes** per scan (faster on GPU)
- Ships as a **deployable web service** (FastAPI + Docker)

---

## Quick Start (Docker — recommended)

```bash
git clone https://github.com/vajihehTarahomi/organai-segmentation.git
cd organai-segmentation
docker compose up --build
```

Then open **http://localhost:8000** and either:
- **Live CT** — upload your own `.nii` / `.nii.gz` scan (segments on demand), or
- **Sample CT** — view a pre-segmented demo instantly (if a sample is configured).

> On first use, TotalSegmentator downloads ~150 MB of model weights (cached afterwards).

---

## Quick Start (without Docker)

Requires Python 3.10+.

```bash
git clone https://github.com/vajihehTarahomi/organai-segmentation.git
cd organai-segmentation

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

pip install -r requirements-api.txt

# start the service (set where uploads + masks are stored)
ORGANAI_DATA_DIR=./data uvicorn api.main:app --port 8000
```

Open **http://localhost:8000**.

---

## Using the API

```bash
# 1. Upload a CT to start a segmentation job
curl -F "file=@abdomen_ct.nii.gz" http://localhost:8000/api/jobs
#    -> {"id":"ab12cd34ef56","status":"queued"}

# 2. Poll until done — returns organ volumes when finished
curl http://localhost:8000/api/jobs/ab12cd34ef56

# 3. Fetch a rendered slice (base64 PNG) — e.g. slice 28
curl "http://localhost:8000/api/jobs/ab12cd34ef56/slice/28"
```

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness check |
| POST | `/api/jobs` | Upload a CT → start segmentation |
| GET | `/api/jobs` | List jobs |
| GET | `/api/jobs/{id}` | Job status + organ volumes when done |
| GET | `/api/jobs/{id}/slice/{z}` | CT slice with organ overlays (base64 PNG) |
| GET | `/api/samples` | List pre-segmented demo cases |

---

## Configuration

All via environment variables — no code changes needed.

| Variable | Default | Purpose |
|---|---|---|
| `ORGANAI_DATA_DIR` | `/data` | Where uploads + generated masks are stored |
| `ORGANAI_DEVICE` | `cpu` | `cpu` or `gpu` |
| `ORGANAI_FAST` | `true` | 3 mm fast mode (vs full resolution) |
| `ORGANAI_MAX_UPLOAD_MB` | `500` | Upload size limit |
| `ORGANAI_MAX_WORKERS` | `1` | Concurrent segmentation jobs |
| `ORGANAI_API_TOKEN` | *(none)* | If set, uploads require `Authorization: Bearer <token>` |
| `ORGANAI_SAMPLES_MANIFEST` | `api/samples.json` | Path to the demo-cases manifest |

**Adding a demo case:** edit `api/samples.json` with entries of
`{"id","name","ct","seg"}`, pointing at a CT file and its TotalSegmentator output
directory. Entries whose files don't exist are skipped.

---

## Getting a CT scan (free public data)

CT data is not included in this repo. Good sources:

| Dataset | Size | Link |
|---|---|---|
| MSD Task09 Spleen | ~1.5 GB | medicaldecathlon.com |
| MSD Task03 Liver | ~3 GB | medicaldecathlon.com |

> Note: files from these datasets may include hidden macOS `._name.nii.gz` sidecar
> files. Upload the real file (e.g. `spleen_10.nii.gz`), not the tiny `._` one — the
> service rejects the sidecars with a clear message.

---

## Offline CLI (no server)

Segment a single scan and write masks to disk:

```bash
pip install -r requirements-api.txt
python segment.py -i path/to/ct.nii.gz -o path/to/masks/ --device cpu
```

---

## How it works

```
Upload CT ──> background worker runs TotalSegmentator ──> organ masks on disk
                                                              │
        volumes computed from mask voxel counts <────────────┤
        slices rendered on demand (cached in RAM) <───────────┘
```

The API returns a job id immediately; the client polls for the result. Loaded
volumes are cached in memory so scrolling through slices is fast.

---

## Performance (CPU, fast mode)

| Organ | Dice | Volume error |
|---|---|---|
| Liver | ~95–97% | ~3–5% |
| Spleen | ~94–96% | ~3–5% |
| Pancreas | ~85–88% | ~8–12% |

---

## Tech stack

| Layer | Technology |
|---|---|
| AI model | TotalSegmentator v2 (nnU-Net backbone) |
| Backend | Python + FastAPI + Uvicorn |
| Imaging | nibabel + numpy |
| Rendering | PIL (server-side PNG) |
| Frontend | Vanilla JS + CSS |
| Deploy | Docker + docker-compose |

---

## Citation

> Wasserthal J. et al. — *TotalSegmentator: Robust Segmentation of 104 Anatomical
> Structures in CT Images* — Radiology: Artificial Intelligence, 2023.

## License

MIT — free to use, modify, and distribute.
