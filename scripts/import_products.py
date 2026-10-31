"""Import stores and commercial products (and their links to fly patterns).

    backend/.venv/bin/python scripts/import_products.py --apply
Reads stores.csv and products.csv. Prices must come with currency and last_verified_at;
never enter estimated prices. Fly patterns must be imported first.
"""

from __future__ import annotations

from _common import base_parser, load_and_validate, write_dataset


def main() -> None:
    args = base_parser(__doc__, writes_db=True).parse_args()
    write_dataset(load_and_validate(args.dir, quiet_warnings=True), args.apply, ["stores", "products"])


if __name__ == "__main__":
    main()
