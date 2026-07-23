"""Organ display config and clinical normal ranges (mL)."""

ORGANS = {
    "liver":          {"color": "#e07b54", "label": "Liver",       "normal": (1000, 1800)},
    "spleen":         {"color": "#7b8fe0", "label": "Spleen",      "normal": (80, 350)},
    "kidney_right":   {"color": "#54b8a0", "label": "Kidney (R)",  "normal": (100, 200)},
    "kidney_left":    {"color": "#54c8a0", "label": "Kidney (L)",  "normal": (100, 200)},
    "pancreas":       {"color": "#d4a843", "label": "Pancreas",    "normal": (60, 120)},
    "aorta":          {"color": "#e05454", "label": "Aorta",       "normal": None},
    "stomach":        {"color": "#a0c4e0", "label": "Stomach",     "normal": None},
    "gallbladder":    {"color": "#c8e054", "label": "Gallbladder", "normal": None},
    "inferior_vena_cava": {"color": "#b054e0", "label": "IVC",     "normal": None},
    "portal_vein_and_splenic_vein": {"color": "#e07bb8", "label": "Portal Vein", "normal": None},
}


def status_for(volume, normal):
    """Classify a volume against a normal range."""
    if not normal:
        return "info", "—"
    lo, hi = normal
    rng = f"{lo}–{hi} mL"
    if volume <= 0:
        return "unknown", rng
    if volume < lo:
        return "low", rng
    if volume > hi:
        return "high", rng
    return "normal", rng
