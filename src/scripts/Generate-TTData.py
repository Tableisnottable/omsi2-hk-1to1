#!/usr/bin/env python3
"""Generate OMSI TTData (Busstops.cfg + .ttp/.ttr/.ttl) per HP1C district.

For each district, matches route_details.csv routes against the district's
osm_stops.csv by origin/destination name, then writes:
  maps/HP1C_<code>/TTData/<line>_<bound>.ttp   (trip with station_typ2 stops)
  maps/HP1C_<code>/TTData/<line>.ttl           (line with tours)
  maps/HP1C_<code>/TTData/Busstops.cfg         (all stops of the district)

Only franchised bus routes with at least 2 matched stops are emitted.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path


def norm(s: str) -> str:
    s = (s or "").lower()
    # strip parenthetical qualifiers: "Central (Macao Ferry)" -> "central"
    s = re.sub(r"\s*\(.*?\)\s*", " ", s)
    s = re.sub(r"[^a-z0-9\u4e00-\u9fff ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def stop_key(name: str) -> set[str]:
    """Token set for fuzzy stop matching."""
    return set(norm(name).split())


def match_score(route_text: str, stop_name: str) -> float:
    rt = stop_key(route_text)
    st = stop_key(stop_name)
    if not rt or not st:
        return 0.0
    # exact substring either way (after normalisation)
    nr, ns = norm(route_text), norm(stop_name)
    if nr and ns and (nr in ns or ns in nr):
        return 1.0
    inter = rt & st
    if not inter:
        return 0.0
    # token overlap relative to the shorter side
    return len(inter) / min(len(rt), len(st))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(Path(__file__).parents[2]))
    parser.add_argument("--mapcode", action="append", help="HP1C code (repeatable)")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    routes_dir = root / "routes"

    with (routes_dir / "route_details.csv").open(encoding="utf-8-sig", newline="") as f:
        all_routes = list(csv.DictReader(f))

    # franchised bus routes only
    bus_routes = [r for r in all_routes if r.get("service_group") == "Franchised public bus"]

    codes = args.mapcode or []
    if args.all or not codes:
        codes = sorted(d.name[5:] for d in (root / "maps").glob("HP1C_*") if d.is_dir())

    for code in codes:
        map_dir = root / "maps" / f"HP1C_{code}"
        stops_csv = map_dir / "osm_stops.csv"
        if not stops_csv.exists():
            continue
        with stops_csv.open(encoding="utf-8-sig", newline="") as f:
            stops = list(csv.DictReader(f))
        if not stops:
            continue

        # match routes to this district's stops
        matched: dict[str, list[dict]] = defaultdict(list)
        for r in bus_routes:
            origin, dest = r.get("origin", ""), r.get("destination", "")
            o_hits = [(s, match_score(origin, s.get("name", ""))) for s in stops]
            d_hits = [(s, match_score(dest, s.get("name", ""))) for s in stops]
            o_best = max(o_hits, key=lambda x: x[1]) if o_hits else (None, 0)
            d_best = max(d_hits, key=lambda x: x[1]) if d_hits else (None, 0)
            if o_best[1] >= 0.5 and d_best[1] >= 0.5 and o_best[0]["id"] != d_best[0]["id"]:
                matched[r["route_number"]].append({
                    "route": r, "origin_stop": o_best[0], "dest_stop": d_best[0],
                })

        if not matched:
            print(f"[{code}] no routes matched ({len(stops)} stops)")
            continue

        tt = map_dir / "TTData"
        tt.mkdir(exist_ok=True)

        # Busstops.cfg: all district stops
        with (tt / "Busstops.cfg").open("w", encoding="utf-8", newline="") as f:
            for s in stops:
                # [busstop] name tile-index object-id offset 0 0
                # tile index 0 (single tile), object-id = stop node id, offset 0
                f.write(f"[busstop]\n{s.get('name') or s['id']}\n0\n{s['id']}\n0\n0\n0\n\n")

        # .ttp + .ttl per route number (first bound only, keep it simple)
        n_trips = 0
        for number, bounds in sorted(matched.items()):
            b = bounds[0]
            safe = re.sub(r"[^\w\-]", "_", number) or "line"
            ttp = tt / f"{safe}_1.ttp"
            with ttp.open("w", encoding="utf-8", newline="") as f:
                f.write(f"[trip]\n\n{b['route']['destination']}\n{number}\n")
                f.write(f"[station_typ2]\n{b['origin_stop']['id']}\n")
                f.write(f"[station_typ2]\n{b['dest_stop']['id']}\n")
                f.write(f"[profile]\n{number} 30\n")
            ttl = tt / f"{safe}.ttl"
            with ttl.open("w", encoding="utf-8", newline="") as f:
                f.write(f"[userallowed]\n[priority]\n1\n[newtour]\n1 0 0\n")
                f.write(f"[addtrip]\n{safe}_1 {number} 360\n")
            n_trips += 1

        print(f"[{code}] {len(stops)} stops, {n_trips} routes -> TTData/")


if __name__ == "__main__":
    main()
