"""Propose commercially reusable iNaturalist photos for catalog organisms, for HUMAN REVIEW.

    backend/.venv/bin/python scripts/fetch_inaturalist_photos.py --per-taxon 5 [--only Baetidae]

Writes data/review/organism_images_candidates.csv with permission_status=pending.
Nothing is downloaded and nothing is imported. To use a photo:
  1. open its source_url and check that the photo shows the taxon and life stage claimed;
  2. copy the row into data/catalog/organism_images.csv and set permission_status=approved;
  3. run scripts/import_images.py --apply --upload.
Only CC0 / CC BY / CC BY-SA photos are proposed (licenses that allow commercial reuse with
attribution). Requests are throttled to 1/second as iNaturalist asks.
"""

from __future__ import annotations

import csv

from _common import REPO_ROOT, base_parser, load_and_validate

from app.core.config import get_settings
from app.services.taxonomy.inaturalist import INaturalistClient

OUT = REPO_ROOT / "data" / "review" / "organism_images_candidates.csv"
HEADER = ["owner_key", "image_url", "storage_path", "source", "source_id", "source_url", "license", "attribution",
          "commercial_use_allowed", "permission_status", "image_view", "life_stage"]


def main() -> None:
    parser = base_parser(__doc__)
    parser.add_argument("--per-taxon", type=int, default=5)
    parser.add_argument("--only", nargs="*", help="Limit to these scientific names")
    args = parser.parse_args()

    settings = get_settings()
    client = INaturalistClient(settings.inaturalist_api_url, settings.external_user_agent)
    organisms = [o for o in load_and_validate(args.dir, quiet_warnings=True).dataset.organisms if o.inaturalist_taxon_id]
    if args.only:
        wanted = {name.lower() for name in args.only}
        organisms = [o for o in organisms if o.scientific_name.lower() in wanted]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        for organism in organisms:
            photos = client.observation_photos(organism.inaturalist_taxon_id, organism.scientific_name, per_page=args.per_taxon)
            for photo in photos[: args.per_taxon]:
                writer.writerow([
                    organism.scientific_name, photo.url, "", "inaturalist", str(photo.photo_id), photo.source_url,
                    photo.license, photo.attribution, "true", "pending", "", "",
                ])
                total += 1
            print(f"{organism.scientific_name}: {min(len(photos), args.per_taxon)} candidates")
    print(f"Wrote {total} candidates to {OUT} (all pending review; life_stage must be filled in by the reviewer).")


if __name__ == "__main__":
    main()
