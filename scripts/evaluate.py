"""Measure recognition quality on a held-out photo set through the running API.

    backend/.venv/bin/python scripts/evaluate.py --api http://localhost:8000 [--manifest data/evaluation/manifest.csv]

The evaluation photos must NOT be in the catalog (otherwise visual search just finds the
same picture). Manifest columns (see docs/TESTING.md):
  image_path,kind,expected_outcome,expected_order,expected_family,expected_genus,expected_species,
  expected_pattern_slug,expected_fly_slugs
Each run calls Gemini once per photo: it consumes API quota.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import Counter
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
UNSURE = {"inconclusive", "insufficient_image", "not_compatible"}
# Fixed anonymous id so evaluation runs are grouped in the identification log.
CLIENT = {"X-Client-Id": "00000000-0000-4000-8000-00000000e7a1"}


def ratio(hits: int, total: int) -> str:
    return f"{hits}/{total} ({hits / total:.0%})" if total else "n/a"


def post_image(http: httpx.Client, kind: str, image: Path, lang: str) -> httpx.Response:
    """POST one photo, waiting out the API rate limit (Retry-After) instead of counting it as an error."""
    for _ in range(5):
        with image.open("rb") as f:
            response = http.post(f"/api/v1/identify/{kind}", files={"image": (image.name, f)}, params={"lang": lang}, headers=CLIENT)
        if response.status_code != 429:
            return response
        wait = int(response.headers.get("Retry-After", "10"))
        print(f"rate limited, waiting {wait}s", file=sys.stderr)
        time.sleep(wait)
    return response


def evaluate(api: str, manifest: Path, lang: str, timeout: float = 120) -> dict:
    rows = list(csv.DictReader(line for line in manifest.open(encoding="utf-8") if not line.startswith("#")))
    stats: Counter = Counter()
    details = []
    with httpx.Client(base_url=api.rstrip("/"), timeout=timeout) as http:
        for row in rows:
            image = (manifest.parent / row["image_path"]).resolve()
            kind = row["kind"]
            response = post_image(http, kind, image, lang)
            if response.status_code != 200:
                stats["api_errors"] += 1
                details.append({"image": row["image_path"], "error": response.status_code})
                continue
            result = response.json()
            level = result["match_level"]
            expected_outcome = row.get("expected_outcome") or "identified"
            if expected_outcome != "identified":
                stats["abstain_total"] += 1
                stats["abstain_correct"] += int(level in UNSURE)
            elif kind == "organism":
                primary = result.get("primary") or {}
                for rank in ("order", "family", "genus"):
                    expected = row.get(f"expected_{rank}")
                    if expected:
                        stats[f"{rank}_total"] += 1
                        stats[f"{rank}_hit"] += int((primary.get(rank) or "").lower() == expected.lower())
                if row.get("expected_species"):
                    stats["species_total"] += 1
                    stats["species_hit"] += int((primary.get("scientific_name") or "").lower() == row["expected_species"].lower())
                expected_flies = {s for s in (row.get("expected_fly_slugs") or "").split("|") if s}
                if expected_flies:
                    top3 = {r["fly"]["slug"] for r in result.get("recommendations", [])[:3]}
                    stats["top3_total"] += 1
                    stats["top3_hit"] += int(bool(top3 & expected_flies))
            else:
                expected = row.get("expected_pattern_slug")
                if expected:
                    primary = (result.get("primary") or {}).get("fly") or {}
                    alternatives = [((a.get("fly") or {}).get("slug")) for a in result.get("alternatives", [])[:2]]
                    stats["pattern_total"] += 1
                    stats["pattern_hit"] += int(primary.get("slug") == expected)
                    stats["pattern_top3_hit"] += int(primary.get("slug") == expected or expected in alternatives)
            if expected_outcome == "identified":
                stats["false_abstain"] += int(level in UNSURE)
            primary = result.get("primary") or {}
            analysis = result.get("analysis") or {}
            details.append({
                "image": row["image_path"], "match_level": level,
                "primary": (primary.get("fly") or {}).get("slug") or primary.get("scientific_name"),
                "life_stage": result.get("life_stage"),
                "top3": [r["fly"]["slug"] for r in result.get("recommendations", [])[:3]],
                "ai_available": analysis.get("ai_available"), "duration_ms": analysis.get("duration_ms"),
            })

    report = {
        "photos": len(rows),
        "order_accuracy": ratio(stats["order_hit"], stats["order_total"]),
        "family_accuracy": ratio(stats["family_hit"], stats["family_total"]),
        "genus_accuracy": ratio(stats["genus_hit"], stats["genus_total"]),
        "species_accuracy": ratio(stats["species_hit"], stats["species_total"]),
        "pattern_top1_accuracy": ratio(stats["pattern_hit"], stats["pattern_total"]),
        "pattern_top3_accuracy": ratio(stats["pattern_top3_hit"], stats["pattern_total"]),
        "recommendation_top3_hit_rate": ratio(stats["top3_hit"], stats["top3_total"]),
        "correct_abstentions": ratio(stats["abstain_correct"], stats["abstain_total"]),
        "abstained_on_identifiable_photos": stats["false_abstain"],
        "api_errors": stats["api_errors"],
        "ai_unavailable": sum(1 for d in details if d.get("ai_available") is False),
        "details": details,
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--api", default="http://localhost:8000")
    parser.add_argument("--manifest", type=Path, default=ROOT / "data" / "evaluation" / "manifest.csv")
    parser.add_argument("--lang", default="en")
    parser.add_argument("--out", type=Path, help="Write the JSON report here")
    parser.add_argument("--timeout", type=float, default=120, help="Seconds to wait for each identification")
    args = parser.parse_args()
    report = evaluate(args.api, args.manifest, args.lang, args.timeout)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    print(text)
    if args.out:
        args.out.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
