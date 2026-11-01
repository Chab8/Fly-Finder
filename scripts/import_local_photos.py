"""Import YOUR OWN photos of fly patterns (or organisms) into the catalog in one go.

Folder layout (one sub-folder per fly slug, or per scientific name with "_" for spaces):

    data/local_photos/fly/zonker/IMG_0001.heic, IMG_0002.jpg, ...
    data/local_photos/fly/clouser-minnow/lateral.jpg, top.jpg
    data/local_photos/organism/Baetis/nymph_1.jpg

    backend/.venv/bin/python scripts/import_local_photos.py --kind fly --author "Your Name"           # dry run
    backend/.venv/bin/python scripts/import_local_photos.py --kind fly --author "Your Name" --apply   # upload + CSV rows

For each photo it validates the image (JPEG/PNG/WEBP/HEIC), removes EXIF/GPS, corrects the
orientation, resizes to 1536 px, skips blurry photos (unless --allow-blurry), uploads the result
to the Supabase bucket and appends an approved row (source=own_photo) to data/catalog/*_images.csv.
Re-running is safe: a photo already imported (same file content) is skipped.
An image_view is taken from the file name when it contains lateral, side, top, dorsal, ventral,
front, back, macro or 3-4. For organisms, a life stage in the file name (nymph, larva, ...) is used.
Afterwards run:  scripts/import_images.py --apply  and  scripts/generate_embeddings.py --target postgres --apply
"""

from __future__ import annotations

import csv
import difflib
import sys
from pathlib import Path

from _common import REPO_ROOT, base_parser, load_and_validate

from app.core.config import get_settings
from app.core.errors import ImageTooLargeError, InvalidImageError
from app.models.catalog import stable_id
from app.models.enums import LifeStage
from app.services.images.processing import process_image
from app.services.storage import SupabaseStorage

HEADER = ["owner_key", "image_url", "storage_path", "source", "source_id", "source_url", "license", "attribution",
          "commercial_use_allowed", "permission_status", "image_view", "life_stage"]
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
VIEWS = ("lateral", "side", "top", "dorsal", "ventral", "front", "back", "macro", "3-4")
MAX_BYTES = 40 * 1024 * 1024


def view_from_name(name: str) -> str:
    lowered = name.lower()
    return next((v for v in VIEWS if v in lowered), "")


def stage_from_name(name: str, allowed: set[str]) -> str:
    lowered = name.lower()
    return next((s.value for s in LifeStage if s.value in lowered and s.value in allowed), "")


def main() -> None:
    parser = base_parser(__doc__, writes_db=True)
    parser.add_argument("--kind", choices=["fly", "organism"], required=True)
    parser.add_argument("--author", required=True, help='Name shown in the credit, e.g. "Chab"')
    parser.add_argument("--photos", type=Path, default=None, help="Folder with the photos (default data/local_photos/<kind>)")
    parser.add_argument("--allow-blurry", action="store_true")
    args = parser.parse_args()

    root = args.photos or (REPO_ROOT / "data" / "local_photos" / args.kind)
    if not root.is_dir():
        sys.exit(f"Folder {root} does not exist. Create it with one sub-folder per {'slug' if args.kind == 'fly' else 'scientific name'}.")

    result = load_and_validate(args.dir, quiet_warnings=True)
    if result.errors:
        sys.exit("Fix the catalog errors above first.")
    dataset = result.dataset
    if args.kind == "fly":
        owners = {f.slug: f for f in dataset.flies}
        stages_of = lambda key: set()  # noqa: E731 - fly photos have no life stage
    else:
        owners = {o.scientific_name.replace(" ", "_"): o for o in dataset.organisms}
        stages_of = lambda key: {s.value for s in owners[key].life_stages}  # noqa: E731
    existing = {image.id for image in dataset.images}
    csv_path = args.dir / ("fly_images.csv" if args.kind == "fly" else "organism_images.csv")

    storage = None
    if args.apply:
        settings = get_settings()
        if not (settings.supabase_url and settings.supabase_service_role_key):
            sys.exit("--apply needs SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in backend/.env")
        storage = SupabaseStorage(settings.supabase_url, settings.supabase_service_role_key.get_secret_value())
        bucket = settings.supabase_storage_bucket_catalog

    new_rows, problems, skipped, per_owner = [], [], 0, {}
    for folder in sorted(p for p in root.iterdir() if p.is_dir()):
        if folder.name not in owners:
            hint = difflib.get_close_matches(folder.name, list(owners), n=3)
            problems.append(f"{folder.name}: no such {'pattern slug' if args.kind == 'fly' else 'taxon'}" + (f" (did you mean {', '.join(hint)}?)" if hint else ""))
            continue
        owner = owners[folder.name]
        owner_key = owner.slug if args.kind == "fly" else owner.scientific_name
        for path in sorted(p for p in folder.iterdir() if p.suffix.lower() in EXTENSIONS):
            try:
                processed = process_image(path.read_bytes(), max_bytes=MAX_BYTES)
            except (InvalidImageError, ImageTooLargeError) as exc:
                problems.append(f"{folder.name}/{path.name}: {exc}")
                continue
            if "possibly_blurry" in processed.warnings and not args.allow_blurry:
                problems.append(f"{folder.name}/{path.name}: looks out of focus (skipped; use --allow-blurry to keep it)")
                continue
            source_id = processed.sha256[:16]
            image_id = stable_id(f"{args.kind}_image", owner_key, "own_photo", source_id)
            if image_id in existing:
                skipped += 1
                continue
            existing.add(image_id)
            storage_path = f"{args.kind}/{owner.id}/{image_id}.jpg"
            if storage:
                storage.upload(bucket, storage_path, processed.jpeg_bytes, "image/jpeg", upsert=True)
            stage = stage_from_name(path.name, stages_of(folder.name)) if args.kind == "organism" else ""
            new_rows.append([owner_key, "", storage_path, "own_photo", source_id, "", "Own photo", f"Foto: {args.author}", "true",
                             "approved", view_from_name(path.name), stage])
            per_owner[owner_key] = per_owner.get(owner_key, 0) + 1
            print(f"{'uploaded' if storage else 'ok (dry run)'}: {folder.name}/{path.name} -> {storage_path}")

    for line in problems:
        print("PROBLEM:", line)
    print(f"\n{len(new_rows)} new photos for {len(per_owner)} items, {skipped} already imported, {len(problems)} problems.")
    if args.apply and new_rows:
        with csv_path.open("a", newline="", encoding="utf-8") as f:
            if f.tell() and csv_path.read_bytes()[-1:] not in (b"\n", b"\r"):
                f.write("\n")
            csv.writer(f).writerows(new_rows)
        print(f"Appended {len(new_rows)} rows to {csv_path}. Next: scripts/import_images.py --apply, then scripts/generate_embeddings.py --target postgres --apply")
    elif not args.apply:
        print("Dry run: nothing was uploaded or written. Re-run with --apply.")


if __name__ == "__main__":
    main()
