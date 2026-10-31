"""Propose commercially reusable iNaturalist photos for catalog organisms, for HUMAN REVIEW.

    backend/.venv/bin/python scripts/fetch_inaturalist_photos.py --per-taxon 5 [--only Baetidae] [--life-stage nymph]

Writes data/review/organism_images_candidates.csv with permission_status=pending.
Nothing is downloaded and nothing is imported. To use a photo:
  1. open its source_url and check that the photo shows the taxon and life stage claimed;
  2. copy the row into data/catalog/organism_images.csv and set permission_status=approved;
  3. run scripts/import_images.py --apply --upload.
With --life-stage, only observations carrying that community life-stage annotation are used and
the life_stage column is pre-filled (still to be checked by the reviewer); taxa whose catalog
record does not list that stage are skipped. iNaturalist "adult" maps to "imago" for mayflies.
Only CC0 / CC BY / CC BY-SA photos are proposed (licenses that allow commercial reuse with
attribution). Requests are throttled to 1/second as iNaturalist asks.
"""

from __future__ import annotations

import csv
from pathlib import Path

from _common import REPO_ROOT, base_parser, load_and_validate

from app.core.config import get_settings
from app.models.enums import LifeStage
from app.services.taxonomy.inaturalist import LIFE_STAGE_VALUE_IDS, INaturalistClient

OUT = REPO_ROOT / "data" / "review" / "organism_images_candidates.csv"
HEADER = ["owner_key", "image_url", "storage_path", "source", "source_id", "source_url", "license", "attribution",
          "commercial_use_allowed", "permission_status", "image_view", "life_stage"]


def catalog_stage(requested: str | None, stages: tuple[LifeStage, ...]) -> str:
    """Catalog life stage for an iNaturalist annotation, or "" if the organism has no such stage."""
    if not requested:
        return ""
    if requested == "adult" and LifeStage.adult not in stages and LifeStage.imago in stages:
        return LifeStage.imago.value
    return requested if LifeStage(requested) in stages else ""


def first_photo_per_observation(photos):
    """The observation's main photo only, so candidates show different individuals."""
    seen, kept = set(), []
    for photo in photos:
        if photo.observation_id not in seen:
            seen.add(photo.observation_id)
            kept.append(photo)
    return kept


def main() -> None:
    parser = base_parser(__doc__)
    parser.add_argument("--per-taxon", type=int, default=5)
    parser.add_argument("--only", nargs="*", help="Limit to these scientific names")
    parser.add_argument("--life-stage", choices=sorted(LIFE_STAGE_VALUE_IDS), help="Only photos annotated with this life stage")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()

    settings = get_settings()
    client = INaturalistClient(settings.inaturalist_api_url, settings.external_user_agent)
    organisms = [o for o in load_and_validate(args.dir, quiet_warnings=True).dataset.organisms if o.inaturalist_taxon_id]
    if args.only:
        wanted = {name.lower() for name in args.only}
        organisms = [o for o in organisms if o.scientific_name.lower() in wanted]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with args.out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        for organism in organisms:
            stage = catalog_stage(args.life_stage, organism.life_stages)
            if args.life_stage and not stage:
                print(f"{organism.scientific_name}: skipped (no {args.life_stage} stage in the catalog)")
                continue
            photos = client.observation_photos(
                organism.inaturalist_taxon_id, organism.scientific_name, per_page=args.per_taxon * 2, life_stage=args.life_stage,
            )
            photos = first_photo_per_observation(photos)
            for photo in photos[: args.per_taxon]:
                writer.writerow([
                    organism.scientific_name, photo.url, "", "inaturalist", str(photo.photo_id), photo.source_url,
                    photo.license, photo.attribution, "true", "pending", "", stage,
                ])
                total += 1
            print(f"{organism.scientific_name}: {min(len(photos), args.per_taxon)} candidates")
    print(f"Wrote {total} candidates to {args.out} (all pending review; check or fill in life_stage).")


if __name__ == "__main__":
    main()
