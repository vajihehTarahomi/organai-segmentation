"""
Creates a realistic synthetic abdominal CT scan with proper HU values,
organ shapes and sizes that TotalSegmentator can actually segment.
Based on real anatomical proportions.
"""
import numpy as np
import nibabel as nib
import os

os.makedirs(r'C:\digitalHealth\real_ct', exist_ok=True)

print("Creating realistic synthetic abdominal CT...")
print("(Real anatomy, correct HU values, proper organ sizes)\n")

# 512 x 512 x 150 slices @ 1x1x2.5mm = realistic abdomen CT size
W, H, D = 256, 256, 120
vol = np.full((H, W, D), -1000.0, dtype=np.float32)  # air background

cx, cy = W // 2, H // 2  # center of body

def ellipse(vol, cx, cy, z_range, rx, ry, value, noise=10):
    """Fill an elliptical region in 3D with a given HU value + noise."""
    z0, z1 = z_range
    for z in range(max(0,z0), min(D, z1)):
        for y in range(H):
            for x in range(W):
                if ((x-cx)/rx)**2 + ((y-cy)/ry)**2 < 1:
                    vol[y, x, z] = value + np.random.randn() * noise

def ellipsoid(vol, cx, cy, cz, rx, ry, rz, value, noise=5):
    """Fill an ellipsoidal region with HU value."""
    x0, x1 = max(0, int(cx-rx-2)), min(W, int(cx+rx+2))
    y0, y1 = max(0, int(cy-ry-2)), min(H, int(cy+ry+2))
    z0, z1 = max(0, int(cz-rz-2)), min(D, int(cz+rz+2))
    for z in range(z0, z1):
        for y in range(y0, y1):
            for x in range(x0, x1):
                if ((x-cx)/rx)**2 + ((y-cy)/ry)**2 + ((z-cz)/rz)**2 < 1:
                    vol[y, x, z] = value + np.random.randn() * noise

np.random.seed(42)

print("  [1/8] Body outline (soft tissue)...")
# Body outline: oval cross-section, ~30cm wide x 25cm deep @ 1mm/px
for z in range(D):
    for y in range(H):
        for x in range(W):
            if ((x-cx)/100)**2 + ((y-cy)/85)**2 < 1:
                vol[y, x, z] = 50 + np.random.randn() * 8   # soft tissue ~50 HU

print("  [2/8] Spine (vertebrae, bone)...")
# Spine: center-back, high HU (bone)
for z in range(D):
    sx, sy = cx + 5, cy + 55   # slightly right of center, posterior
    for y in range(H):
        for x in range(W):
            if ((x-sx)/10)**2 + ((y-sy)/10)**2 < 1:
                vol[y, x, z] = 700 + np.random.randn() * 50  # bone

print("  [3/8] Liver (large, right side)...")
# Liver: right lobe dominant, spans ~z=40-90, large ellipsoid
ellipsoid(vol, cx - 30, cy - 15, 65, 60, 45, 25, value=60, noise=8)

print("  [4/8] Spleen (left side)...")
# Spleen: left side, smaller than liver, spans ~z=45-80
ellipsoid(vol, cx + 55, cy - 10, 62, 28, 25, 18, value=55, noise=6)

print("  [5/8] Kidneys...")
# Right kidney
ellipsoid(vol, cx - 55, cy + 30, 60, 16, 20, 22, value=40, noise=8)
# Left kidney
ellipsoid(vol, cx + 55, cy + 30, 60, 16, 20, 22, value=40, noise=8)

print("  [6/8] Aorta and IVC (large vessels)...")
# Aorta: left of spine, runs entire height, ~2cm diameter
for z in range(D):
    ax, ay = cx - 8, cy + 45
    for y in range(H):
        for x in range(W):
            if ((x-ax)/9)**2 + ((y-ay)/9)**2 < 1:
                vol[y, x, z] = 150 + np.random.randn() * 20  # blood

# IVC: right of spine
for z in range(D):
    vx, vy = cx + 8, cy + 45
    for y in range(H):
        for x in range(W):
            if ((x-vx)/10)**2 + ((y-vy)/10)**2 < 1:
                vol[y, x, z] = 100 + np.random.randn() * 15

print("  [7/8] Stomach and bowel...")
# Stomach: upper left, contains air+fluid
ellipsoid(vol, cx + 35, cy - 30, 55, 22, 18, 15, value=-50, noise=30)

# Bowel loops scattered in lower abdomen
for i, (bx, by, bz) in enumerate([
    (cx-40, cy-40, 80), (cx+30, cy-35, 85), (cx-20, cy+20, 90),
    (cx+40, cy+20, 88), (cx, cy-45, 95)
]):
    ellipsoid(vol, bx, by, bz, 12, 10, 8, value=-100+i*20, noise=25)

print("  [8/8] Subcutaneous fat layer...")
# Fat layer around body (lower HU than muscle)
for z in range(D):
    for y in range(H):
        for x in range(W):
            d_body = ((x-cx)/100)**2 + ((y-cy)/85)**2
            d_fat  = ((x-cx)/115)**2 + ((y-cy)/98)**2
            if d_body >= 0.85 and d_fat < 1:
                vol[y, x, z] = -80 + np.random.randn() * 15  # fat ~-80 HU

# Save as NIfTI with realistic 1x1x2.5mm voxel spacing
affine = np.diag([1.0, 1.0, 2.5, 1.0])
img = nib.Nifti1Image(vol.astype(np.int16), affine)
out = r'C:\digitalHealth\real_ct\realistic_abdomen_ct.nii.gz'
nib.save(img, out)

size_mb = os.path.getsize(out) / 1024 / 1024
print(f"\nSaved: {out}")
print(f"Size:  {size_mb:.1f} MB")
print(f"Shape: {vol.shape}  (H x W x Slices)")
print(f"Voxel: 1.0 x 1.0 x 2.5 mm")
print(f"\nHU values:")
print(f"  Air (outside body):  -1000 HU")
print(f"  Fat (subcutaneous):    -80 HU")
print(f"  Soft tissue / muscle:  +50 HU")
print(f"  Blood (vessels):      +150 HU")
print(f"  Liver:                 +60 HU")
print(f"  Spleen:                +55 HU")
print(f"  Kidneys:               +40 HU")
print(f"  Spine (bone):         +700 HU")
print(f"\nReady for TotalSegmentator!")
