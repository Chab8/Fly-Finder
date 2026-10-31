"""Compute OpenCLIP embeddings for approved catalog images (once, at import time).

    backend/.venv/bin/python scripts/generate_embeddings.py --target postgres --apply
    backend/.venv/bin/python scripts/generate_embeddings.py --target memory

postgres: embeds images in organism_images / fly_images that have no embedding for the
          current model (OPENCLIP_MODEL / OPENCLIP_PRETRAINED) and stores them in pgvector.
memory:   embeds approved images from the CSV catalog and writes
          data/catalog/embeddings/<model>.npz for the CATALOG_BACKEND=memory mode.
User searches never recompute catalog embeddings.
"""

from __future__ import annotations

import io
import sys

import httpx
import numpy as np
from _common import base_parser, load_and_validate, require_database
from PIL import Image

from app.api.deps import embeddings_file, image_url_resolver
from app.core.config import get_settings
from app.models.enums import PermissionStatus
from app.repositories.vector_index import InMemoryVectorIndex
from app.services.embeddings.openclip import OpenClipEmbedder


def fetch(http: httpx.Client, url: str) -> Image.Image:
    response = http.get(url)
    response.raise_for_status()
    return Image.open(io.BytesIO(response.content)).convert("RGB")


def main() -> None:
    parser = base_parser(__doc__, writes_db=True)
    parser.add_argument("--target", choices=["postgres", "memory"], required=True)
    parser.add_argument("--limit", type=int, default=1000)
    args = parser.parse_args()

    settings = get_settings()
    embedder = OpenClipEmbedder(settings.openclip_model, settings.openclip_pretrained, settings.openclip_device, settings.embedding_dimension)
    resolve = image_url_resolver(settings)
    http = httpx.Client(timeout=30, follow_redirects=True, headers={"User-Agent": settings.external_user_agent})

    if args.target == "memory":
        images = [i for i in load_and_validate(args.dir, quiet_warnings=True).dataset.images if i.permission_status == PermissionStatus.approved]
        ids, kinds, owners, vectors = [], [], [], []
        for image in images[: args.limit]:
            url = resolve(image)
            if not url:
                continue
            vectors.append(embedder.embed(fetch(http, url)))
            ids.append(image.id)
            kinds.append(image.owner_kind)
            owners.append(image.owner_id)
            print("embedded", image.owner_kind, image.id)
        if not vectors:
            sys.exit("No approved images with a URL in the catalog: nothing to embed.")
        path = embeddings_file(settings)
        InMemoryVectorIndex(embedder.model_id, ids, kinds, owners, np.vstack(vectors)).save(path)
        print(f"Wrote {len(vectors)} embeddings to {path}")
        return

    from app.repositories.postgres import PgEmbeddingStore

    with require_database(settings) as conn:
        store = PgEmbeddingStore(conn)
        done = 0
        for kind in ("organism", "fly"):
            for row in store.images_missing_embedding(kind, embedder.model_id, args.limit):
                path = row["storage_path"]
                url = (
                    f"{settings.supabase_url.rstrip('/')}/storage/v1/object/public/{settings.supabase_storage_bucket_catalog}/{path}"
                    if path and settings.supabase_url else row["image_url"]
                )
                vector = embedder.embed(fetch(http, url))
                if args.apply:
                    store.save_embedding(kind, row["id"], embedder.model_id, vector)
                    conn.commit()
                done += 1
                print("embedded" if args.apply else "would embed", kind, row["id"])
        print(f"{done} images {'embedded' if args.apply else 'pending (dry run, use --apply)'}.")


if __name__ == "__main__":
    main()
