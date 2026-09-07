"""Download the BPI Challenge 2013 logs into data/raw/.

4TU hosts the dataset on figshare. File download ids change between platform
migrations, so they are resolved through the API rather than hardcoded.
"""
import json
import sys
import urllib.request
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
API = "https://api.figshare.com/v2/articles/{}"
LANDING = "https://data.4tu.nl/search?q=BPI+Challenge+2013"

ARTICLES = {
    "incidents": 12693914,
    "open_problems": 12688556,
    "closed_problems": 12714476,
}


def resolve(article_id: int) -> tuple[str, str]:
    """Return (filename, download_url) for the .xes.gz in an article."""
    with urllib.request.urlopen(API.format(article_id), timeout=60) as response:
        payload = json.load(response)
    for entry in payload.get("files", []):
        if entry["name"].endswith(".xes.gz"):
            return entry["name"], entry["download_url"]
    raise LookupError(f"No .xes.gz in article {article_id} ({payload.get('title')})")


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    failures = []

    for label, article_id in ARTICLES.items():
        try:
            name, url = resolve(article_id)
        except Exception as exc:  # noqa: BLE001 - reported to the user below
            failures.append((label, exc))
            print(f"{label}: could not resolve download url: {exc}")
            continue

        target = RAW / name
        if target.exists():
            print(f"skip {name} (already present)")
            continue

        print(f"fetch {name} ...")
        try:
            urllib.request.urlretrieve(url, target)
            print(f"  {target.stat().st_size / 1_000_000:.1f} MB")
        except Exception as exc:  # noqa: BLE001 - reported to the user below
            target.unlink(missing_ok=True)
            failures.append((label, exc))
            print(f"  failed: {exc}")

    if failures:
        print(f"\n{len(failures)} log(s) could not be downloaded.")
        print(f"Download them by hand from {LANDING} and place them in {RAW}")
        return 1

    print(f"\nAll logs present in {RAW}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
