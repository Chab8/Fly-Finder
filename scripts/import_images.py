"""Import catalog image metadata (organism_images.csv, fly_images.csv).

    backend/.venv/bin/python scripts/import_images.py --apply [--upload]

Only rows with permission_status=approved AND commercial_use_allowed=true are imported
unless --include-non-commercial is given (e.g. for an internal, non-commercial build).
With --upload, each image_url is downloaded once and stored in the public Supabase bucket
(catalog-images) so the app does not hotlink third-party servers.
"""

from __future__ import annotations

import sys

import httpx
from _common import base_parser, load_and_validate, write_dataset

from app.core.config import get_settings
from app.models.enums import PermissionStatus
from app.services.storage import SupabaseStorage


def main() -> None:
    parser = base_parser(__doc__, writes_db=True)
    parser.add_argument("--upload", action="store_true", help="Copy images into Supabase Storage")
    parser.add_argument("--include-non-commercial", action="store_true")
    args = parser.parse_args()

    result = load_and_validate(args.dir, quiet_warnings=True)
    kept = [
        image for image in result.dataset.images
        if image.permission_status == PermissionStatus.approved and (image.commercial_use_allowed or args.include_non_commercial)
    ]
    print(f"{len(kept)} of {len(result.dataset.images)} images are approved for import.")
    result.dataset.images = kept

    if args.upload and args.apply:
        settings = get_settings()
        if not (settings.supabase_url and settings.supabase_service_role_key):
            sys.exit("--upload needs SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in backend/.env")
        storage = SupabaseStorage(settings.supabase_url, settings.supabase_service_role_key.get_secret_value())
        uploaded = []
        with httpx.Client(timeout=30, headers={"User-Agent": settings.external_user_agent}, follow_redirects=True) as http:
            for image in kept:
                if image.storage_path or not image.image_url:
                    uploaded.append(image)
                    continue
                response = http.get(image.image_url)
                response.raise_for_status()
                path = f"{image.owner_kind}/{image.owner_id}/{image.id}.jpg"
                storage.upload(settings.supabase_storage_bucket_catalog, path, response.content, response.headers.get("content-type", "image/jpeg"), upsert=True)
                uploaded.append(image.model_copy(update={"storage_path": path}))
                print("uploaded", path)
        result.dataset.images = uploaded

    write_dataset(result, args.apply, ["images"])


if __name__ == "__main__":
    main()
