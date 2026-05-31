import io
import os
import urllib.request
import zipfile

TARGET_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "natural_earth")

DATASETS = [
    ("110m", "physical", "ne_110m_land"),
    ("110m", "cultural", "ne_110m_admin_0_countries"),
    ("110m", "physical", "ne_110m_lakes"),
    ("50m", "cultural", "ne_50m_admin_0_countries"),
    ("50m", "physical", "ne_50m_land"),
]

BASE_URL = "https://naciscdn.org/naturalearth"


def download_and_extract(resolution, category, name):
    url = f"{BASE_URL}/{resolution}/{category}/{name}.zip"
    dest = os.path.join(TARGET_DIR, name)
    os.makedirs(dest, exist_ok=True)

    existing = [f for f in os.listdir(dest) if f.endswith((".shp", ".shx", ".dbf", ".prj"))]
    if existing:
        print(f"  [skip] {name} — already exists ({len(existing)} files)")
        return True

    print(f"  [download] {name} from {url}")
    try:
        resp = urllib.request.urlopen(url, timeout=60)
        data = resp.read()
    except Exception as e:
        print(f"  [error] failed to download {name}: {e}")
        return False

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for member in zf.namelist():
            if "__MACOSX" in member:
                continue
            if member.endswith("/"):
                continue
            filename = os.path.basename(member)
            with zf.open(member) as src, open(os.path.join(dest, filename), "wb") as dst:
                dst.write(src.read())

    shp_files = [f for f in os.listdir(dest) if f.endswith(".shp")]
    if shp_files:
        print(f"  [ok] {name} — {len(os.listdir(dest))} files extracted")
        return True
    else:
        print(f"  [error] {name} — no .shp file found after extraction")
        return False


def main():
    os.makedirs(TARGET_DIR, exist_ok=True)
    print("Downloading Natural Earth data...")
    results = {}
    for resolution, category, name in DATASETS:
        results[name] = download_and_extract(resolution, category, name)

    print()
    print("Summary:")
    for name, ok in results.items():
        status = "OK" if ok else "FAILED"
        dest = os.path.join(TARGET_DIR, name)
        count = len(os.listdir(dest)) if os.path.isdir(dest) else 0
        print(f"  {name}: {status} ({count} files)")

    if not all(results.values()):
        print("\nSome downloads failed!")
        return 1
    print("\nAll downloads succeeded!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
