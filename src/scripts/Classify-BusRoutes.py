#!/usr/bin/env python3
"""Add route `category` and `region` columns to the HK route CSVs.

Reads routes/hk_bus_routes.csv, routes/nr_routes.csv, routes/other_routes.csv,
routes/route_details.csv and routes/cancelled_routes.csv, classifies each row
with RouteCategories (HK Bus Wiki numbering method) and rewrites the files
with the extra columns.

Also writes routes/category_summary.json with per-dataset counts.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from RouteCategories import CATEGORY_LABELS, REGION_LABELS, classify, infer_region  # noqa: E402


def rewrite_csv(
    path: Path,
    number_key: str,
    text_keys: tuple[str, ...],
    operator_keys: tuple[str, ...],
    region_keys: tuple[str, ...],
) -> Counter:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    if "category" not in fields:
        fields.append("category")
    if "region" not in fields:
        fields.append("region")
    counts: Counter = Counter()
    for row in rows:
        number = row.get(number_key, "")
        text = " ".join(row.get(k, "") for k in text_keys)
        operator = " ".join(row.get(k, "") for k in operator_keys)
        cat = classify(number, text, operator)
        row["category"] = cat
        counts[cat] += 1
        if region_keys:
            origin = row.get(region_keys[0], "")
            destination = row.get(region_keys[1], "") if len(region_keys) > 1 else ""
            row["region"] = infer_region(origin, destination)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", default=str(Path(__file__).parents[2]))
    args = parser.parse_args()

    root = Path(args.output_root).resolve()
    routes_dir = root / "routes"

    summary = {}
    targets = [
        ("hk_bus_routes.csv", "route_number", ("origin", "destination"), ("operator",), ("origin", "destination")),
        ("nr_routes.csv", "route_id", ("destination",), ("operator",), ("destination",)),
        ("other_routes.csv", "route_id", ("origin", "destination"), ("operator",), ("origin", "destination")),
        ("route_details.csv", "route_number", ("origin", "destination"), ("operator",), ("origin", "destination")),
        ("cancelled_routes.csv", "route_number", ("route",), ("operator",), ()),
    ]
    for name, number_key, text_keys, operator_keys, region_keys in targets:
        path = routes_dir / name
        if not path.exists():
            continue
        counts = rewrite_csv(path, number_key, text_keys, operator_keys, region_keys)
        summary[name] = {
            "total": sum(counts.values()),
            "categories": {CATEGORY_LABELS.get(k, k): v for k, v in counts.most_common()},
        }
        print(f"{name}: {sum(counts.values())} rows -> {dict(counts.most_common())}")

    (routes_dir / "category_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {routes_dir / 'category_summary.json'}")


if __name__ == "__main__":
    main()

