"""
Robust CT downloader with resume + retry support
"""
import urllib.request, ssl, os, time, sys

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def download(url, dest, label="file"):
    os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
    existing = os.path.getsize(dest) if os.path.exists(dest) else 0

    for attempt in range(6):
        try:
            headers = [('User-Agent', 'Mozilla/5.0')]
            if existing:
                headers.append(('Range', f'bytes={existing}-'))
                print(f"  Resuming from {existing/1024/1024:.1f} MB...")

            opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))
            opener.addheaders = headers
            with opener.open(url, timeout=30) as r:
                total_str = r.headers.get('Content-Length', '0')
                total = int(total_str) + existing if total_str else 0
                mode = 'ab' if existing else 'wb'
                with open(dest, mode) as f:
                    downloaded = existing
                    while True:
                        chunk = r.read(512 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            pct = downloaded / total * 100
                            mb = downloaded / 1024 / 1024
                            tot_mb = total / 1024 / 1024
                            print(f"\r  {pct:.1f}%  ({mb:.1f} / {tot_mb:.1f} MB)", end='', flush=True)
            print(f"\n  Saved: {dest}  ({os.path.getsize(dest)/1024/1024:.1f} MB)")
            return True
        except Exception as e:
            print(f"\n  Attempt {attempt+1}/6 failed: {e}")
            existing = os.path.getsize(dest) if os.path.exists(dest) else 0
            time.sleep(3)
    print("  Download failed after 6 attempts.")
    return False


# ── Real abdominal CT scan ──────────────────────────────────────────────────
# From MONAI's public test data — a real small abdominal CT (spleen, ~30MB)
# Hosted on Google Drive via a direct link
CT_SOURCES = [
    # MONAI spleen CT example (real clinical CT, small)
    ("https://msd-for-monai.s3-us-west-2.amazonaws.com/Task09_Spleen.tar",
     r"C:\digitalHealth\real_ct\Task09_Spleen.tar",
     "MSD Spleen CT (~1.5 GB - too large, skipping)"),

    # A single-case liver CT from Harvard Dataverse (public, small)
    ("https://dataverse.harvard.edu/api/access/datafile/6168551",
     r"C:\digitalHealth\real_ct\liver_case.nii.gz",
     "Harvard Dataverse liver CT"),
]

print("=" * 55)
print("Downloading a real abdominal CT scan")
print("=" * 55)

for url, dest, label in CT_SOURCES:
    if "too large" in label:
        print(f"\nSkipping: {label}")
        continue
    print(f"\nSource: {label}")
    if download(url, dest, label):
        break
