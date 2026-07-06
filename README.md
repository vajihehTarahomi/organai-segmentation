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

## Installation

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd digitalHealth

# 2. Create virtual environment
python -m venv venv
source venv/Scripts/activate   # Windows
# or: source venv/bin/activate  # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt
```

> **Note:** TotalSegmentator will automatically download AI model weights (~150 MB) on first run.

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
