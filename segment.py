"""
Run TotalSegmentator on a CT scan and save organ masks (offline/CLI use).

For the deployable service, use the FastAPI app in `api/` instead — see README.

Usage:
    python segment.py --input path/to/ct.nii.gz --output path/to/masks/
    python segment.py -i ct.nii.gz -o masks/ --device gpu
"""
import argparse
from totalsegmentator.python_api import totalsegmentator


def main():
    ap = argparse.ArgumentParser(description="Segment a CT with TotalSegmentator")
    ap.add_argument("-i", "--input", required=True, help="CT NIfTI file (.nii.gz)")
    ap.add_argument("-o", "--output", required=True, help="Output directory for masks")
    ap.add_argument("--device", default="cpu", choices=["cpu", "gpu"])
    ap.add_argument("--full", action="store_true",
                    help="Full resolution (default is fast/3mm)")
    args = ap.parse_args()

    print(f"Segmenting: {args.input}")
    print(f"Output:     {args.output}")
    print(f"Device:     {args.device}  |  mode: {'full' if args.full else 'fast (3mm)'}")

    totalsegmentator(
        input=args.input,
        output=args.output,
        device=args.device,
        fast=not args.full,
    )
    print("Done! Masks saved to:", args.output)


if __name__ == "__main__":
    main()
