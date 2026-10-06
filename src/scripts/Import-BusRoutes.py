"""Import the current Hong Kong bus route catalogue into repository CSV files."""

from __future__ import annotations

import argparse
import csv
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SOURCE_URL = "https://hkbus.github.io/hk-bus-crawling/routeFareList.min.json"
NR_SOURCES = {
    "hong_kong_island": "https://www.td.gov.hk/en/transport_in_hong_kong/public_transport/non_franchised/index.html",
    "kowloon": "https://www.td.gov.hk/en/transport_in_hong_kong/public_transport/non_franchised/index.html",
    "new_territories": "https://www.td.gov.hk/en/transport_in_hong_kong/public_transport/non_franchised/index.html",
}


def text(value: object) -> str:
    if isinstance(value, dict):
        return str(value.get("en") or value.get("zh") or "")
    if isinstance(value, list):
        return "|".join(text(item) for item in value)
    return "" if value is None else str(value)


def download(url: str, path: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "omsi2-hk-1to1 route importer"})
    with urllib.request.urlopen(request, timeout=120) as response:
        path.write_bytes(response.read())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=SOURCE_URL)
    parser.add_argument("--output-root", default=str(Path(__file__).parents[2]))
    parser.add_argument("--source-file")
    args = parser.parse_args()

    root = Path(args.output_root).resolve()
    routes_dir = root / "routes"
    source_dir = root / "src" / "routes"
    routes_dir.mkdir(parents=True, exist_ok=True)
    source_dir.mkdir(parents=True, exist_ok=True)
    source_file = Path(args.source_file) if args.source_file else source_dir / "routeFareList.min.json"
    if not source_file.is_absolute():
        source_file = root / source_file
    if args.source.startswith(("http://", "https://")):
        download(args.source, source_file)
    elif not source_file.exists():
        source_file = Path(args.source).resolve()

    payload = json.loads(source_file.read_text(encoding="utf-8"))
    rows = []
    for route_id, route in payload.get("routeList", {}).items():
        route_number, service_type, origin_key, destination_key = (route_id.split("+", 3) + ["", "", "", ""])[:4]
        operators = route.get("co", [])
        rows.append(
            {
                "route_id": route_id,
                "route_number": route_number,
                "service_type": service_type,
                "operator": "|".join(operators),
                "origin": text(route.get("orig")),
                "destination": text(route.get("dest")),
                "origin_key": origin_key,
                "destination_key": destination_key,
                "bound": text(route.get("bound")),
                "gtfs_id": text(route.get("gtfsId")),
                "source": "HK Bus Crawling",
            }
        )

    rows.sort(key=lambda row: (row["operator"], row["route_number"], row["route_id"]))
    with (routes_dir / "hk_bus_routes.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    with (routes_dir / "nr_routes.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["route_id", "region", "origin", "destination", "operator", "status", "source"],
        )
        writer.writeheader()

    metadata = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "route_count": len(rows),
        "operators": sorted({operator for row in rows for operator in row["operator"].split("|")}),
        "route_source": args.source,
        "nr_route_source": NR_SOURCES,
        "nr_status": "NR route lists require separate Transport Department approval-list ingestion; no NR rows are fabricated.",
    }
    (routes_dir / "sources.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(rows)} franchised/public-transport route records to {routes_dir / 'hk_bus_routes.csv'}")
    print("Created routes/nr_routes.csv with the authoritative NR ingestion boundary documented in routes/sources.json")


if __name__ == "__main__":
    main()
