"""Import organisms (with common names, texts, synonyms, life stages) into Supabase.

    backend/.venv/bin/python scripts/import_organisms.py            # dry run
    backend/.venv/bin/python scripts/import_organisms.py --apply    # write
Idempotent: re-running updates existing rows (IDs are derived from scientific_name).
"""

from __future__ import annotations

from _common import base_parser, load_and_validate, write_dataset


def main() -> None:
    args = base_parser(__doc__, writes_db=True).parse_args()
    write_dataset(load_and_validate(args.dir, quiet_warnings=True), args.apply, ["organisms"])


if __name__ == "__main__":
    main()
