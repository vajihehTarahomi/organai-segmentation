"""On-demand segmentation + volumetry, plus slice rendering."""
import io
import os
import glob
import base64
import numpy as np
import nibabel as nib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .config import DEVICE, FAST
from .organs import ORGANS, status_for


def run_segmentation(ct_path: str, seg_dir: str) -> None:
    """Run TotalSegmentator on ct_path, writing masks into seg_dir."""
    # Imported lazily so the API can boot without the heavy model deps present.
    from totalsegmentator.python_api import totalsegmentator
    os.makedirs(seg_dir, exist_ok=True)
    totalsegmentator(input=ct_path, output=seg_dir, device=DEVICE, fast=FAST)


def compute_volumes(ct_path: str, seg_dir: str) -> dict:
    """Return {organ: volume_mL} plus voxel/shape metadata for a segmented case."""
    ct_img = nib.load(ct_path)
    zooms = ct_img.header.get_zooms()
    vox_ml = float(zooms[0] * zooms[1] * zooms[2]) / 1000.0

    volumes = {}
    for organ in ORGANS:
        f = os.path.join(seg_dir, organ + ".nii.gz")
        if os.path.exists(f):
            m = nib.load(f).get_fdata()
            volumes[organ] = round(float(np.sum(m > 0)) * vox_ml, 1)

    return {
        "volumes": volumes,
        "voxel_mm": [round(float(z), 2) for z in zooms],
        "shape": [int(x) for x in ct_img.shape],
        "n_slices": int(ct_img.shape[2]),
        "n_masks": len(glob.glob(os.path.join(seg_dir, "*.nii.gz"))),
    }


def volumes_payload(volumes: dict) -> list:
    """Shape the volumes dict into the API's per-organ list with statuses."""
    out = []
    for organ, cfg in ORGANS.items():
        vol = volumes.get(organ, 0.0)
        status, rng = status_for(vol, cfg["normal"])
        out.append({
            "id": organ, "label": cfg["label"], "color": cfg["color"],
            "volume": vol, "range": rng, "status": status,
        })
    return out


def _hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4))


def render_slice(ct_path: str, seg_dir: str, z: int, wc: int = 40, ww: int = 400) -> str:
    """Render an axial CT slice with organ overlays; return base64 PNG."""
    ct = nib.load(ct_path).get_fdata()
    n = ct.shape[2]
    z = max(0, min(int(z), n - 1))

    lo, hi = wc - ww / 2, wc + ww / 2
    slc = np.clip(ct[:, :, z], lo, hi)
    slc = (slc - lo) / (hi - lo)

    fig, ax = plt.subplots(figsize=(6, 6), facecolor="black")
    ax.imshow(slc, cmap="gray", origin="lower", aspect="equal")

    overlay = np.zeros((*ct.shape[:2], 4), dtype=np.float32)
    for organ, cfg in ORGANS.items():
        f = os.path.join(seg_dir, organ + ".nii.gz")
        if not os.path.exists(f):
            continue
        m = nib.load(f).get_fdata()[:, :, z]
        if m.sum() == 0:
            continue
        r, g, b = _hex_rgb(cfg["color"])
        overlay[m > 0] = [r, g, b, 0.55]
    ax.imshow(overlay, origin="lower", aspect="equal")

    ax.set_title(f"Axial Slice {z + 1} / {n}", color="white", fontsize=11, pad=4)
    ax.axis("off")
    plt.tight_layout(pad=0.2)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=110, bbox_inches="tight", facecolor="black")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()
