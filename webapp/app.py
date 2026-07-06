"""
Organ Segmentation Demo Web App
Flask backend — serves CT slices + organ volumes
"""
from flask import Flask, jsonify, render_template, request
import nibabel as nib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import base64, io, os, glob

app = Flask(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────
# Default: switch to real CT once segmentation is done
REAL_CT   = r"C:\digitalHealth\real_ct\Task09_Spleen\Task09_Spleen\imagesTr\spleen_10.nii.gz"
REAL_SEG  = r"C:\digitalHealth\real_ct\spleen10_seg"
SYN_CT    = r"C:\digitalHealth\real_ct\realistic_abdomen_ct.nii.gz"
SYN_SEG   = r"C:\digitalHealth\real_ct\segmentation_output"

# Use real CT if segmentation is ready, else synthetic
import glob as _glob
_real_ready = os.path.exists(REAL_SEG) and len(_glob.glob(REAL_SEG + r"\*.nii.gz")) > 10
CT_PATH = REAL_CT  if _real_ready else SYN_CT
SEG_DIR = REAL_SEG if _real_ready else SYN_SEG
print(f"Using {'REAL' if _real_ready else 'SYNTHETIC'} CT: {CT_PATH}")

# ── Organ config ───────────────────────────────────────────────────────────
ORGANS = {
    "liver":          {"color": "#e07b54", "label": "Liver",         "normal": (1000,1800), "unit":"mL"},
    "spleen":         {"color": "#7b8fe0", "label": "Spleen",        "normal": (80, 350),   "unit":"mL"},
    "kidney_right":   {"color": "#54b8a0", "label": "Kidney (R)",    "normal": (100,200),   "unit":"mL"},
    "kidney_left":    {"color": "#54c8a0", "label": "Kidney (L)",    "normal": (100,200),   "unit":"mL"},
    "pancreas":       {"color": "#d4a843", "label": "Pancreas",      "normal": (60, 120),   "unit":"mL"},
    "aorta":          {"color": "#e05454", "label": "Aorta",         "normal": None,        "unit":"mL"},
    "stomach":        {"color": "#a0c4e0", "label": "Stomach",       "normal": None,        "unit":"mL"},
    "gallbladder":    {"color": "#c8e054", "label": "Gallbladder",   "normal": None,        "unit":"mL"},
    "inferior_vena_cava": {"color": "#b054e0", "label": "IVC",      "normal": None,        "unit":"mL"},
    "portal_vein_and_splenic_vein": {"color": "#e07bb8","label":"Portal Vein","normal":None,"unit":"mL"},
}

# ── Load data once at startup ───────────────────────────────────────────────
print("Loading CT scan...")
ct_img  = nib.load(CT_PATH)
ct_data = ct_img.get_fdata().astype(np.float32)
zooms   = ct_img.header.get_zooms()
n_slices = ct_data.shape[2]
print(f"CT shape: {ct_data.shape}, voxel: {zooms}")

print("Loading segmentation masks...")
masks = {}
volumes = {}
for organ, cfg in ORGANS.items():
    f = os.path.join(SEG_DIR, organ + ".nii.gz")
    if os.path.exists(f):
        m = nib.load(f).get_fdata().astype(np.uint8)
        masks[organ] = m
        vox_ml = (zooms[0] * zooms[1] * zooms[2]) / 1000.0
        vol = float(np.sum(m > 0) * vox_ml)
        volumes[organ] = round(vol, 1)
print(f"Loaded {len(masks)} masks.")

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16)/255 for i in (0, 2, 4))

def render_slice(z, window_center=40, window_width=400):
    """Render a single axial CT slice with organ overlays as base64 PNG."""
    fig, ax = plt.subplots(1, 1, figsize=(6, 6), facecolor='black')
    ax.set_facecolor('black')

    # Windowed CT slice
    lo = window_center - window_width / 2
    hi = window_center + window_width / 2
    slc = np.clip(ct_data[:, :, z], lo, hi)
    slc = (slc - lo) / (hi - lo)
    ax.imshow(slc, cmap='gray', origin='lower', aspect='equal')

    # Organ overlays
    overlay = np.zeros((*ct_data.shape[:2], 4), dtype=np.float32)
    for organ, cfg in ORGANS.items():
        if organ not in masks:
            continue
        m = masks[organ][:, :, z]
        if m.sum() == 0:
            continue
        r, g, b = hex_to_rgb(cfg["color"])
        overlay[m > 0] = [r, g, b, 0.55]

    ax.imshow(overlay, origin='lower', aspect='equal')

    # Slice info
    ax.set_title(f"Axial Slice {z+1} / {n_slices}", color='white', fontsize=11, pad=4)
    ax.axis('off')
    plt.tight_layout(pad=0.2)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=110, bbox_inches='tight',
                facecolor='black', edgecolor='none')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


# ── Routes ─────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html",
                           n_slices=n_slices,
                           mid_slice=n_slices // 2)


@app.route("/api/slice/<int:z>")
def api_slice(z):
    z = max(0, min(z, n_slices - 1))
    wc = int(request.args.get("wc", 40))
    ww = int(request.args.get("ww", 400))
    img_b64 = render_slice(z, wc, ww)
    return jsonify({"image": img_b64, "slice": z})


@app.route("/api/volumes")
def api_volumes():
    result = []
    for organ, cfg in ORGANS.items():
        vol = volumes.get(organ, 0)
        normal = cfg["normal"]
        if normal:
            lo, hi = normal
            if vol == 0:
                status = "unknown"
            elif vol < lo:
                status = "low"
            elif vol > hi:
                status = "high"
            else:
                status = "normal"
            range_str = f"{lo}–{hi} mL"
        else:
            status = "info"
            range_str = "—"
        result.append({
            "id":       organ,
            "label":    cfg["label"],
            "color":    cfg["color"],
            "volume":   vol,
            "normal":   normal,
            "range":    range_str,
            "status":   status,
        })
    return jsonify(result)


@app.route("/api/info")
def api_info():
    return jsonify({
        "ct_shape": list(ct_data.shape),
        "voxel_mm": [round(float(z), 2) for z in zooms],
        "n_slices": n_slices,
        "n_organs": len(masks),
        "model": "TotalSegmentator v2.14 (fast/3mm)",
        "device": "CPU",
    })


if __name__ == "__main__":
    print("\n" + "="*50)
    print("  Organ Segmentation Demo")
    print("  Open: http://localhost:5000")
    print("="*50 + "\n")
    app.run(debug=False, port=5000)
