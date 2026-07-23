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


# Small in-memory cache of loaded volumes, keyed by (ct_path, seg_dir).
# Keeps the whole CT + present organ masks in RAM so scrolling is instant
# instead of re-decompressing gzipped NIfTI on every slice request.
_CACHE: "dict[tuple, dict]" = {}
_CACHE_MAX = 2  # number of distinct cases to keep resident


def _get_volumes(ct_path: str, seg_dir: str) -> dict:
    key = (ct_path, seg_dir)
    hit = _CACHE.get(key)
    if hit is not None:
        return hit

    ct = nib.load(ct_path).get_fdata()
    masks = {}
    for organ in ORGANS:
        f = os.path.join(seg_dir, organ + ".nii.gz")
        if os.path.exists(f):
            m = nib.load(f).get_fdata() > 0
            if m.any():
                masks[organ] = m
    entry = {"ct": ct, "masks": masks}

    if len(_CACHE) >= _CACHE_MAX:
        _CACHE.pop(next(iter(_CACHE)))  # evict oldest
    _CACHE[key] = entry
    return entry


def render_slice(ct_path: str, seg_dir: str, z: int, wc: int = 40, ww: int = 400) -> str:
    """Render an axial CT slice with organ overlays; return base64 PNG.

    Encodes directly with PIL/numpy (no matplotlib) so scrolling is fast.
    """
    from PIL import Image

    vol = _get_volumes(ct_path, seg_dir)
    ct, masks = vol["ct"], vol["masks"]
    n = ct.shape[2]
    z = max(0, min(int(z), n - 1))

    # HU windowing -> 0..1 grayscale, flipped vertically to match origin="lower"
    lo, hi = wc - ww / 2, wc + ww / 2
    slc = np.clip(ct[:, :, z], lo, hi)
    slc = (slc - lo) / (hi - lo)
    slc = np.flipud(slc)

    rgb = np.repeat(slc[:, :, None], 3, axis=2)  # gray -> RGB

    # Alpha-composite each organ overlay (0.55 opacity) onto the grayscale
    alpha = 0.55
    for organ, cfg in ORGANS.items():
        m = masks.get(organ)
        if m is None:
            continue
        ms = np.flipud(m[:, :, z])
        if not ms.any():
            continue
        color = np.array(_hex_rgb(cfg["color"]))
        rgb[ms] = rgb[ms] * (1 - alpha) + color * alpha

    img = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8), "RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()
