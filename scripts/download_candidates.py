"""Download the candidate photos listed in a review CSV so they can be checked quickly.

    backend/.venv/bin/python scripts/download_candidates.py [--csv a.csv b.csv ...]

Saves every image_url into data/review/images/ (named NNN_<taxon>_<source_id>.jpg) and writes
data/review/images/index.csv (file, owner_key, life_stage, license, attribution, source_url).
Nothing is imported or approved: these files are only for looking at the photos. Requests are
throttled to 1 per second. Only rows with an http(s) image_url are downloaded.
"""

from __future__ import annotations

import csv
import re
import sys
import time
from pathlib import Path

import httpx
from _common import REPO_ROOT, base_parser

from app.core.config import get_settings

DEFAULT_CSV = REPO_ROOT / "data" / "review" / "organism_images_candidates.csv"
OUT_DIR = REPO_ROOT / "data" / "review" / "images"


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "x"


def main() -> None:
    parser = base_parser(__doc__)
    parser.add_argument("--csv", type=Path, nargs="+", default=[DEFAULT_CSV])
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    rows = []
    for csv_path in args.csv:
        if not csv_path.exists():
            sys.exit(f"{csv_path} does not exist. Run scripts/fetch_inaturalist_photos.py first.")
        rows += list(csv.DictReader(line for line in csv_path.open(encoding="utf-8") if not line.startswith("#")))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    settings = get_settings()
    index = []
    with httpx.Client(timeout=30, follow_redirects=True, headers={"User-Agent": settings.external_user_agent}) as http:
        for n, row in enumerate(rows, 1):
            url = (row.get("image_url") or "").strip()
            if not url.startswith(("http://", "https://")):
                continue
            name = f"{n:03d}_{slug(row['owner_key'])}_{slug(row.get('source_id') or str(n))}.jpg"
            target = args.out_dir / name
            if not target.exists():
                try:
                    response = http.get(url)
                    response.raise_for_status()
                except httpx.HTTPError as exc:
                    print(f"[{n}/{len(rows)}] FAILED {row['owner_key']}: {exc}")
                    continue
                target.write_bytes(response.content)
                time.sleep(1.0)
            print(f"[{n}/{len(rows)}] {name}")
            index.append([name, row["owner_key"], row.get("life_stage", ""), row.get("license", ""), row.get("attribution", ""), row.get("source_url", "")])

    with (args.out_dir / "index.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["file", "owner_key", "life_stage", "license", "attribution", "source_url"])
        writer.writerows(index)
    print(f"Downloaded {len(index)} photos to {args.out_dir}. Index: {args.out_dir / 'index.csv'}")


if __name__ == "__main__":
    main()
