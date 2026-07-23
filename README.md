# OrganAI — Abdominal Organ Segmentation & Volumetry

AI-powered abdominal organ segmentation and volumetry tool built on [TotalSegmentator](https://github.com/wasserth/TotalSegmentator), with an interactive web-based CT viewer and volume dashboard.

---

## What It Does

- Automatically segments **117 anatomical structures** from abdominal CT scans
- Calculates **organ volumes** (liver, spleen, kidneys, pancreas, aorta, and more)
- Flags abnormal volumes against clinical normal ranges
- Displays results in an **interactive web app** with a CT slice viewer

**Clinical context:** Replaces manual organ measurement (10+ min/organ) with automated volumetry in ~4 minutes on CPU — making routine volumetric reporting feasible for the first time.

---

## Project Structure

```
digitalHealth/
├── webapp/
│   ├── app.py              # Flask backend — serves CT slices + volumes via API
│   └── templates/
│       └── index.html      # Interactive CT viewer + organ volume dashboard
├── create_realistic_ct.py  # Generates synthetic abdominal CT for testing
├── download_ct.py          # Robust CT downloader with resume + retry
├── requirements.txt        # Python dependencies
└── README.md
```

---

## Quick Start (for a new machine)

### 1 — Clone and install

```bash
git clone https://github.com/vajihehTarahomi/organai-segmentation.git
cd organai-segmentation

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
```

> TotalSegmentator will automatically download AI model weights (~150 MB) on first run.

### 2 — Get a CT scan (required)

CT data is not included in this repo (too large). Download the free **MSD Task09 Spleen** dataset:

1. Go to [medicaldecathlon.com](http://medicaldecathlon.com)
2. Download **Task09_Spleen.tar** (~1.5 GB)
3. Extract it so you have this path:
   ```
   organai-segmentation/
   └── real_ct/
       └── Task09_Spleen/
           └── Task09_Spleen/
               └── imagesTr/
                   └── spleen_10.nii.gz
   ```

### 3 — Run segmentation

```bash
python segment.py -i real_ct/Task09_Spleen/Task09_Spleen/imagesTr/spleen_10.nii.gz -o real_ct/spleen10_seg
```

This takes ~4 minutes on CPU and produces 117 organ masks in `real_ct/spleen10_seg/`.

### 4 — Launch the web app

```bash
python webapp/app.py
# Open: http://localhost:5000
```

The app auto-detects the segmentation output and displays organ volumes with clinical normal ranges.

---

## Deploying as a Service (recommended)

The `api/` package is a **FastAPI service** with on-demand inference — upload a CT and get organ volumes back over HTTP. No hardcoded paths; everything is configured via environment variables.

### Run with Docker

```bash
docker compose up --build
# open http://localhost:8000
```

Upload a `.nii/.nii.gz` CT in the browser, or via the API:

```bash
# start a segmentation job
curl -F "file=@abdomen_ct.nii.gz" http://localhost:8000/api/jobs
# -> {"id":"ab12cd34ef56","status":"queued"}

# poll status (returns volumes when done)
curl http://localhost:8000/api/jobs/ab12cd34ef56

# fetch a rendered slice (base64 PNG) at slice z=28
curl "http://localhost:8000/api/jobs/ab12cd34ef56/slice/28"
```

### API endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness probe |
| POST | `/api/jobs` | Upload CT → start segmentation job |
| GET | `/api/jobs` | List jobs |
| GET | `/api/jobs/{id}` | Job status + organ volumes when done |
| GET | `/api/jobs/{id}/slice/{z}` | Rendered CT slice with overlays (base64 PNG) |

### Configuration (environment variables)

| Variable | Default | Purpose |
|---|---|---|
| `ORGANAI_DATA_DIR` | `/data` | Where uploads + masks are stored |
| `ORGANAI_DEVICE` | `cpu` | `cpu` or `gpu` |
| `ORGANAI_FAST` | `true` | 3mm fast mode vs full resolution |
| `ORGANAI_MAX_UPLOAD_MB` | `500` | Upload size limit |
| `ORGANAI_MAX_WORKERS` | `1` | Concurrent segmentation jobs |
| `ORGANAI_API_TOKEN` | *(none)* | If set, `POST /api/jobs` requires `Authorization: Bearer <token>` |

### Run without Docker

```bash
pip install -r requirements-api.txt
ORGANAI_DATA_DIR=./data uvicorn api.main:app --host 0.0.0.0 --port 8000
```

> **Architecture note:** segmentation runs in a background worker pool; the API returns a job id immediately and the client polls for the result. Model weights (~150 MB) download on the first inference and are cached in the `totalseg-weights` volume.

---

## Offline / CLI use (no server)

The original one-shot scripts still work for local experimentation:

### Installation (alternative — no real CT)

If you just want to see the UI without real CT data:

```bash
python create_realistic_ct.py   # generates a synthetic abdomen CT
python webapp/app.py            # launches app with synthetic data (volumes = 0)
```

> Note: TotalSegmentator won't find organs in synthetic data — volumes will show 0. Use real CT for meaningful results.

---

## Usage

### Step 1 — Segment a CT scan

```python
from totalsegmentator.python_api import totalsegmentator

totalsegmentator(
    input="path/to/abdomen_ct.nii.gz",
    output="path/to/output_masks/",
    device="cpu",   # or "gpu" if NVIDIA GPU available
    fast=True       # 3mm resolution — faster, good enough for volumetry
)
```

### Step 2 — Launch the web app

Edit `webapp/app.py` to point to your CT and segmentation output:

```python
CT_PATH = r"path/to/your_ct.nii.gz"
SEG_DIR = r"path/to/output_masks/"
```

Then run:

```bash
python webapp/app.py
# Open: http://localhost:5000
```

### Step 3 — Use the web app

- **Scroll** on the CT image to browse through slices
- **Window buttons** — switch between Abdomen / Liver / Bone / Lung / Fat views
- **Organ cards** — show volume in mL with normal range and status (Normal / High / Low)

---

## Getting a CT Scan (Free Public Data)

| Dataset | Organs | Size | Link |
|---|---|---|---|
| MSD Task09 Spleen | Abdomen + spleen | ~1.5 GB | medicaldecathlon.com |
| MSD Task03 Liver | Abdomen + liver | ~3 GB | medicaldecathlon.com |
| AbdomenAtlas 3.0 | 25+ structures | Large | Request access |

---

## Performance (CPU, fast mode)

| Organ | Dice Score | Volume Error |
|---|---|---|
| Liver | ~95–97% | ~3–5% |
| Spleen | ~94–96% | ~3–5% |
| Pancreas | ~85–88% | ~8–12% |
| Portal vein | ~80–88% | — |

---

## Clinical Validation (Next Steps)

1. Run on 20–50 local hospital CTs
2. Compare AI volumes to expert manual measurements
3. Fine-tune with `nnU-Net` if error > 10%
4. Submit validation paper

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI Model | TotalSegmentator v2.14 (nnU-Net backbone) |
| Backend | Python + Flask |
| Medical imaging | nibabel + SimpleITK |
| Visualization | matplotlib (server-side rendering) |
| Frontend | Vanilla JS + CSS (no framework) |

---

## Citation

If you use TotalSegmentator, please cite:

> Wasserthal J. et al. — *TotalSegmentator: Robust Segmentation of 104 Anatomical Structures in CT Images* — Radiology: Artificial Intelligence, 2023.

---

## License

MIT License — free to use, modify, and distribute.
