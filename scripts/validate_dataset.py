"""Validate catalog CSVs: schema, controlled vocabularies, duplicates and references.

    backend/.venv/bin/python scripts/validate_dataset.py [--dir data/catalog]
Exit code 1 if there are errors (warnings do not fail).
"""

from __future__ import annotations

import sys

from _common import base_parser, load_and_validate


def main() -> None:
    parser = base_parser(__doc__)
    parser.add_argument("--errors-only", action="store_true", help="Hide warnings")
    args = parser.parse_args()
    result = load_and_validate(args.dir, quiet_warnings=args.errors_only)
    sys.exit(1 if result.errors else 0)


if __name__ == "__main__":
    main()
