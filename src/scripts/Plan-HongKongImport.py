#!/usr/bin/env python3
"""Measure OSM road coverage on the HK_BigMap grid and export a GeoJSON tile plan."""

import argparse
import hashlib
import importlib.util
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from tempfile import NamedTemporaryFile

import osmium


spec = importlib.util.spec_from_file_location(
    "bigmap", Path(__file__).with_name("Convert-OsmToBigMap.py")
)
bigmap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bigmap)


def registered_tiles(path):
    raw = path.read_bytes()
    encoding = "utf-16" if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"
    records = re.findall(r"^\[map\]\r?\n(-?\d+)\r?\n(-?\d+)\r?\n", raw.decode(encoding), re.M)
    if not records:
        raise ValueError(f"No tile records in {path}")
    return {(int(x), int(y)) for x, y in records}


def tile_lengths(start, end, bounds):
    """Clip a segment to the selection, then distribute its length across grid cells."""
    delta = [b - a for a, b in zip(start, end)]
    length = math.hypot(*delta)
    if not length:
        return
    first, last = 0.0, 1.0
    if bounds:
        for origin, step, low, high in zip(start, delta, bounds[:2], bounds[2:]):
            if not step:
                if not low <= origin <= high:
                    return
                continue
            enter, leave = sorted(((low - origin) / step, (high - origin) / step))
            first, last = max(first, enter), min(last, leave)
        if first >= last:
            return

    cuts = {first, last}
    for origin, step in zip(start, delta):
        if not step:
            continue
        low, high = sorted((origin + step * first, origin + step * last))
        for index in range(math.floor(low / bigmap.TILE) + 1, math.ceil(high / bigmap.TILE)):
            cut = (index * bigmap.TILE - origin) / step
            if first < cut < last:
                cuts.add(cut)
    ordered = sorted(cuts)
    for a, b in zip(ordered, ordered[1:]):
        midpoint = (a + b) / 2
        tile = tuple(math.floor((origin + step * midpoint) / bigmap.TILE)
                     for origin, step in zip(start, delta))
        yield tile, (b - a) * length


class RoadCoverage(osmium.SimpleHandler):
    def __init__(self, bounds):
        super().__init__()
        self.bounds = bounds
        self.tiles = defaultdict(lambda: defaultdict(float))
        self.incomplete_ways = 0

    def way(self, way):
        tags = way.tags
        if tags.get("highway") not in bigmap.DRIVABLE:
            return
        if tags.get("access") in ("private", "no") and tags.get("bus") not in ("yes", "designated"):
            return
        if not all(node.location.valid() for node in way.nodes):
            self.incomplete_ways += 1
            return
        kind = "surface"
        if tags.get("tunnel") not in (None, "no"):
            kind = "tunnel"
        elif tags.get("bridge") not in (None, "no"):
            kind = "bridge"
        points = [bigmap.to_global(node.lat, node.lon) for node in way.nodes]
        for a, b in zip(points, points[1:]):
            for tile, metres in tile_lengths(a, b, self.bounds):
                self.tiles[tile][kind] += metres


def tile_feature(tile, lengths, in_map):
    tx, ty = tile
    corners = ((tx, ty), (tx + 1, ty), (tx + 1, ty + 1), (tx, ty + 1), (tx, ty))
    ring = []
    for x, y in corners:
        lat, lon = bigmap.to_latlon(x * bigmap.TILE, y * bigmap.TILE)
        ring.append([round(lon, 8), round(lat, 8)])
    return {
        "type": "Feature",
        "geometry": {"type": "Polygon", "coordinates": [ring]},
        "properties": {
            "tile_x": tx, "tile_y": ty, "registered_in_bigmap": in_map,
            **{f"{kind}_road_m": round(lengths.get(kind, 0), 3)
               for kind in ("surface", "bridge", "tunnel")},
        },
    }


def main():
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=root / "work/tsingyi-inputs/hong-kong-latest.osm.pbf")
    parser.add_argument("--global-cfg", type=Path, default=root / "maps/HK_BigMap/global.cfg")
    parser.add_argument("--output", type=Path, default=root / "work/hk-import/road-tiles.geojson")
    parser.add_argument("--bounds", nargs=4, type=float, metavar=("WEST", "SOUTH", "EAST", "NORTH"),
                        help="Limit measured roads to a WGS84 rectangle")
    args = parser.parse_args()
    for path in (args.source, args.global_cfg):
        if not path.is_file():
            parser.error(f"Missing {path}")
        if args.output.resolve() == path.resolve():
            parser.error("Output must differ from the inputs")
    bounds = None
    if args.bounds:
        west, south, east, north = args.bounds
        if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
            parser.error("Expected ordered WGS84 bounds WEST SOUTH EAST NORTH")
        bounds = (*bigmap.to_global(south, west), *bigmap.to_global(north, east))

    existing = registered_tiles(args.global_cfg)
    coverage = RoadCoverage(bounds)
    coverage.apply_file(str(args.source), locations=True, idx="flex_mem")
    with args.source.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    overlaps = coverage.tiles.keys() & existing
    summary = {
        "source_sha256": digest,
        "bounds_wgs84": args.bounds,
        "road_tiles": len(coverage.tiles),
        "road_tiles_in_bigmap": len(overlaps),
        "road_tiles_outside_bigmap": len(coverage.tiles) - len(overlaps),
        "source_road_km": round(sum(sum(v.values()) for v in coverage.tiles.values()) / 1000, 3),
        "source_road_km_outside_bigmap": round(sum(
            sum(lengths.values()) for tile, lengths in coverage.tiles.items() if tile not in existing
        ) / 1000, 3),
        "source_ways_with_missing_nodes": coverage.incomplete_ways,
    }
    features = [tile_feature(tile, lengths, tile in existing)
                for tile, lengths in sorted(coverage.tiles.items())]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=args.output.parent, delete=False) as output:
        temp_path = Path(output.name)
        json.dump({"type": "FeatureCollection", "features": features, "summary": summary}, output)
        output.write("\n")
    try:
        temp_path.replace(args.output)
    finally:
        temp_path.unlink(missing_ok=True)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
