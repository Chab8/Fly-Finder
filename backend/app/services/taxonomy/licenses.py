"""Image license policy for a commercial app (see docs/IMAGE_LICENSES.md).

Allowed for commercial reuse WITH attribution: CC0, CC BY, CC BY-SA (share-alike applies
to adaptations; we only resize). Everything else is rejected by default:
- CC BY-NC*      non-commercial only
- CC BY-ND*      no derivatives; resizing/cropping for the app is a grey area
- no license     "all rights reserved"
"""

from __future__ import annotations

COMMERCIAL_OK = {"cc0", "cc-by", "cc-by-sa"}

LICENSE_NAMES = {
    "cc0": "CC0 1.0",
    "cc-by": "CC BY 4.0",
    "cc-by-sa": "CC BY-SA 4.0",
    "cc-by-nc": "CC BY-NC 4.0",
    "cc-by-nc-sa": "CC BY-NC-SA 4.0",
    "cc-by-nd": "CC BY-ND 4.0",
    "cc-by-nc-nd": "CC BY-NC-ND 4.0",
}


def normalize_license(code: str | None) -> str:
    return (code or "").strip().lower() or "all-rights-reserved"


def commercial_use_allowed(code: str | None) -> bool:
    return normalize_license(code) in COMMERCIAL_OK


def license_label(code: str | None) -> str:
    normalized = normalize_license(code)
    return LICENSE_NAMES.get(normalized, "All rights reserved" if normalized == "all-rights-reserved" else normalized)
