"""Import the current Hong Kong bus route catalogue into repository CSV files."""

from __future__ import annotations

import argparse
import csv
from html.parser import HTMLParser
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SOURCE_URL = "https://hkbus.github.io/hk-bus-crawling/routeFareList.min.json"
HKEMOBILITY_URL = "https://www.hkemobility.gov.hk/en/route-search/pt"
NR_SOURCES = {
    "hong_kong_island": "https://www.td.gov.hk/en/transport_in_hong_kong/public_transport/non_franchised/list_of_approved_rs_hk/index.html",
    "kowloon": "https://www.td.gov.hk/en/transport_in_hong_kong/public_transport/non_franchised/list_of_approved_rs_kln/index.html",
    "new_territories": "https://www.td.gov.hk/en/transport_in_hong_kong/public_transport/non_franchised/list_of_approved_rs_nt/index.html",
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


class ResidentsServiceTableParser(HTMLParser):
    """Extract route number and origin/destination cells from a TD HTML table."""

    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._link_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self._row = []
        elif tag == "td" and self._row is not None:
            self._cell = []
        elif tag == "a" and self._cell is not None:
            self._link_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._link_depth:
            self._link_depth -= 1
        elif tag == "td" and self._row is not None and self._cell is not None:
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if len(self._row) >= 2:
                self.rows.append(self._row[:2])
            self._row = None

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)


def import_nr_routes() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    route_pattern = re.compile(r"^(?:HR|KR|DB|NR)\d+[A-Z]*", re.IGNORECASE)
    for region, url in NR_SOURCES.items():
        request = urllib.request.Request(url, headers={"User-Agent": "omsi2-hk-1to1 route importer"})
        with urllib.request.urlopen(request, timeout=120) as response:
            html = response.read().decode("utf-8", errors="replace")
        parser = ResidentsServiceTableParser()
        parser.feed(html)
        for route_label, destination in parser.rows:
            match = route_pattern.match(route_label.strip())
            if not match:
                continue
            route_number = match.group(0).upper()
            rows.append(
                {
                    "route_id": route_number,
                    "region": region,
                    "origin": "",
                    "destination": destination,
                    "operator": "Residents' Service",
                    "status": "approved",
                    "source": url,
                }
            )
    rows.sort(key=lambda row: (row["region"], row["route_id"]))
    return rows


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

    nr_rows = import_nr_routes()
    with (routes_dir / "nr_routes.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["route_id", "region", "origin", "destination", "operator", "status", "source"],
        )
        writer.writeheader()
        writer.writerows(nr_rows)

    metadata = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "route_count": len(rows),
        "nr_route_count": len(nr_rows),
        "operators": sorted({operator for row in rows for operator in row["operator"].split("|")}),
        "route_source": args.source,
        "hkemobility_route_search": HKEMOBILITY_URL,
        "hkemobility_api": "https://www.hkemobility.gov.hk/api/em",
        "hkemobility_api_status": "Interactive route-search backend; direct bulk requests require a browser session and returned Forbidden during validation.",
        "nr_route_source": NR_SOURCES,
        "nr_status": "Imported from the Transport Department approved Residents' Service HTML route lists.",
    }
    (routes_dir / "sources.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(rows)} franchised/public-transport route records to {routes_dir / 'hk_bus_routes.csv'}")
    print(f"Wrote {len(nr_rows)} approved Residents' Service route records to {routes_dir / 'nr_routes.csv'}")


if __name__ == "__main__":
    main()
