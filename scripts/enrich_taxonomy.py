"""Check every organism in organisms.csv against the GBIF Backbone and fill taxonomy fields.

    backend/.venv/bin/python scripts/enrich_taxonomy.py            # report only
    backend/.venv/bin/python scripts/enrich_taxonomy.py --write    # update the CSV in place
    backend/.venv/bin/python scripts/enrich_taxonomy.py --write --inaturalist   # also iNat ids

Rules:
- Only an EXACT GBIF match at the same rank sets gbif_taxon_id, fills kingdom..genus and
  marks the record source_verified. Anything else is reported and left untouched.
- Existing values that disagree with GBIF are reported, never silently overwritten.
- expert_verified is never set by this script.
"""

from __future__ import annotations

import csv
import time

from _common import DEFAULT_CATALOG_DIR, base_parser

from app.core.config import get_settings
from app.services.taxonomy.gbif import GbifClient
from app.services.taxonomy.inaturalist import INaturalistClient

FIELDS = {"kingdom": "kingdom", "phylum": "phylum", "class": "class_name", "order": "order", "family": "family", "genus": "genus"}


def main() -> None:
    parser = base_parser(__doc__)
    parser.add_argument("--write", action="store_true", help="Write changes back to organisms.csv")
    parser.add_argument("--inaturalist", action="store_true", help="Also look up iNaturalist taxon ids (1 request/second)")
    args = parser.parse_args()

    settings = get_settings()
    gbif = GbifClient(settings.gbif_api_url, settings.external_user_agent, 15.0)
    inat = INaturalistClient(settings.inaturalist_api_url, settings.external_user_agent) if args.inaturalist else None

    path = (args.dir or DEFAULT_CATALOG_DIR) / "organisms.csv"
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        rows = list(reader)

    verified = 0
    for row in rows:
        name, rank = row["scientific_name"], row["taxonomic_rank"]
        match = gbif.match(name, rank=rank)
        if not match or match.match_type != "EXACT" or match.rank != rank:
            got = f"{match.match_type} {match.rank} {match.accepted_name}" if match else "no match"
            print(f"[CHECK] {name} ({rank}): GBIF -> {got}")
            continue
        if match.status not in ("ACCEPTED", "DOUBTFUL"):
            print(f"[CHECK] {name}: GBIF status {match.status} (synonym?) accepted name may differ")
        for column, attr in FIELDS.items():
            value = getattr(match, attr)
            if value and row.get(column) and row[column] != value:
                print(f"[DIFF]  {name}: {column} CSV={row[column]!r} GBIF={value!r} -> using GBIF")
            if value:
                row[column] = value
        row["gbif_taxon_id"] = str(match.gbif_taxon_id)
        if row.get("verification_status") in ("", "unverified"):
            row["verification_status"] = "source_verified"
        verified += 1
        if inat and not row.get("inaturalist_taxon_id"):
            taxon_id = inat.find_taxon_id(name, rank=rank)
            if taxon_id:
                row["inaturalist_taxon_id"] = str(taxon_id)
        time.sleep(0.1)  # be gentle with GBIF

    print(f"{verified}/{len(rows)} organisms matched exactly in GBIF.")
    if args.write:
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Updated {path}")


if __name__ == "__main__":
    main()
