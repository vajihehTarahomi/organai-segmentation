"""
Run TotalSegmentator on a CT scan and save organ masks.
Usage: python segment.py
"""

from totalsegmentator.python_api import totalsegmentator

CT_INPUT = r"C:\digitalHealth\real_ct\Task09_Spleen\Task09_Spleen\imagesTr\spleen_10.nii.gz"
SEG_OUTPUT = r"C:\digitalHealth\real_ct\spleen10_seg"

print(f"Segmenting: {CT_INPUT}")
print(f"Output:     {SEG_OUTPUT}")
print("This takes ~4 minutes on CPU...")

totalsegmentator(
    input=CT_INPUT,
    output=SEG_OUTPUT,
    device="cpu",
    fast=True,       # 3mm resolution — good enough for volumetry
)

print("Done! Organ masks saved to:", SEG_OUTPUT)
print("Now run:  python webapp/app.py")
