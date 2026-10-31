"""Import fly patterns (materials, variants, texts) and organism<->fly relations.

    backend/.venv/bin/python scripts/import_fly_patterns.py --apply
Run import_organisms.py first: relations reference organisms. Use --no-matches to skip them.
"""

from __future__ import annotations

from _common import base_parser, load_and_validate, write_dataset


def main() -> None:
    parser = base_parser(__doc__, writes_db=True)
    parser.add_argument("--no-matches", action="store_true", help="Import patterns only, not fly_organism_matches")
    args = parser.parse_args()
    sections = ["flies"] if args.no_matches else ["flies", "matches"]
    write_dataset(load_and_validate(args.dir, quiet_warnings=True), args.apply, sections)


if __name__ == "__main__":
    main()
