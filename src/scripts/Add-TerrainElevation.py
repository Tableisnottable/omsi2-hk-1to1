#!/usr/bin/env python3
"""Add real elevation to OMSI tile terrain files.

Fetches ASTER 30 m elevations from OpenTopoData (free, no key) on an
11x11 grid across the 300 m tile, then bilinearly interpolates to the
61x61 OMSI terrain grid and writes tile_0_0.map.terrain
(u32 cell count = 60 + 61x61 f32 heights, row-major).

Usage:
    python src/scripts/Add-TerrainElevation.py --mapcode CW
    python src/scripts/Add-TerrainElevation.py --all
"""

from __future__ import annotations

import argparse
import json
import math
import struct
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

TILE_SIZE = 300.0
SAMPLES = 61
CELLS = SAMPLES - 1
SRC = 11  # 11x11 source grid at 30 m spacing

API = "https://api.opentopodata.org/v1/aster30m"

sys.path.insert(0, str(Path(__file__).parent))
from hp1c_centres import CENTRES  # noqa: E402


def fetch_batch(points: list[tuple[float, float]]) -> list[float]:
    """Fetch elevations for up to 100 points (OpenTopoData limit)."""
    locs = "|".join(f"{lat:.6f},{lon:.6f}" for lat, lon in points)
    body = urllib.parse.urlencode({"locations": locs}).encode()
    for attempt in range(6):
        req = urllib.request.Request(API, data=body, headers={"User-Agent": "omsi2-hk-1to1 terrain"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                data = json.load(r)
            if data.get("status") != "OK":
                raise RuntimeError(f"status {data.get('status')}: {data.get('error')}")
            return [float(res["elevation"]) for res in data["results"]]
        except (urllib.error.HTTPError, urllib.error.URLError):
            if attempt < 5:
                time.sleep(6 * (attempt + 1))
                continue
            raise
    raise RuntimeError("fetch_batch exhausted retries")


def fetch_elevations(centre_lat: float, centre_lon: float) -> list[list[float]]:
    """Return an 11x11 grid of elevations (rows south->north)."""
    mpdlat = 110574.0
    mpdlon = 111320.0 * math.cos(math.radians(centre_lat))
    half = TILE_SIZE / 2.0
    step = TILE_SIZE / (SRC - 1)
    grid: list[list[float]] = [[0.0] * SRC for _ in range(SRC)]
    points: list[tuple[int, int, float, float]] = []
    for iy in range(SRC):
        y = -half + iy * step
        for ix in range(SRC):
            x = -half + ix * step
            points.append((ix, iy, centre_lat + y / mpdlat, centre_lon + x / mpdlon))
    for start in range(0, len(points), 100):
        batch = points[start : start + 100]
        vals = fetch_batch([(p[2], p[3]) for p in batch])
        for (ix, iy, _, _), v in zip(batch, vals):
            grid[iy][ix] = v
    return grid


def bilinear(grid: list[list[float]], fx: float, fy: float) -> float:
    """Sample the source grid at normalised (fx, fy) in [0, 1]."""
    n = SRC - 1
    x = max(0.0, min(1.0, fx)) * n
    y = max(0.0, min(1.0, fy)) * n
    ix, iy = int(x), int(y)
    if ix >= n:
        ix, x = n - 1, float(n)
    if iy >= n:
        iy, y = n - 1, float(n)
    tx, ty = x - ix, y - iy
    h00 = grid[iy][ix]
    h10 = grid[iy][ix + 1]
    h01 = grid[iy + 1][ix]
    h11 = grid[iy + 1][ix + 1]
    return (h00 * (1 - tx) + h10 * tx) * (1 - ty) + (h01 * (1 - tx) + h11 * tx) * ty


def build_terrain_heights(grid: list[list[float]]) -> list[float]:
    """Interpolate the 11x11 grid to 61x61 rows south->north."""
    out: list[float] = []
    for iy in range(SAMPLES):
        fy = iy / CELLS
        for ix in range(SAMPLES):
            fx = ix / CELLS
            out.append(bilinear(grid, fx, fy))
    return out


def write_terrain(map_dir: Path, heights: list[float]) -> None:
    path = map_dir / "tile_0_0.map.terrain"
    with path.open("wb") as f:
        f.write(struct.pack("<I", CELLS))
        for h in heights:
            f.write(struct.pack("<f", h))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mapcode", action="append", help="HP1C code (repeatable)")
    parser.add_argument("--all", action="store_true", help="Process every district")
    parser.add_argument("--root", default=str(Path(__file__).parents[2]))
    args = parser.parse_args()

    root = Path(args.root).resolve()
    codes = args.mapcode or []
    if args.all:
        codes = sorted(CENTRES.keys())

    for code in codes:
        if code not in CENTRES:
            print(f"!! {code}: unknown map code", file=sys.stderr)
            continue
        centre = CENTRES[code]
        map_dir = root / "maps" / f"HP1C_{code}"
        if not map_dir.exists():
            print(f"!! {code}: map dir missing", file=sys.stderr)
            continue
        print(f"[{code}] fetching {SRC}x{SRC} ASTER30m at ({centre['lat']}, {centre['lon']}) ...", flush=True)
        try:
            grid = fetch_elevations(centre["lat"], centre["lon"])
        except Exception as e:
            print(f"!! {code}: elevation fetch failed: {e}", file=sys.stderr)
            continue
        heights = build_terrain_heights(grid)
        write_terrain(map_dir, heights)
        mn, mx = min(heights), max(heights)
        print(f"[{code}] wrote {map_dir / 'tile_0_0.map.terrain'}  min={mn:.1f}m max={mx:.1f}m", flush=True)
        time.sleep(1)


if __name__ == "__main__":
    main()
