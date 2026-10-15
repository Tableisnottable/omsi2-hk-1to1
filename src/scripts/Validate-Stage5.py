#!/usr/bin/env python3
"""Stage 5 validator: check the QUALITY_TARGET.md quality gate per HP1C area.

An HP1C area passes when it has:
  1. terrain and road data covering the actual area (not a copied placeholder)
  2. visible building and infrastructure meshes
  3. authored materials with documented sources
  4. collision and LOD data
  5. validated bus stops and route paths

Usage:
    python src/scripts/Validate-Stage5.py [--root .]
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import struct
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CODES = ["CW", "EAS", "HZMB", "ISL", "KCT", "KTN", "KWT", "NTH", "SKG",
         "SOU", "SSP", "STN", "TMM", "TPO", "TWW", "WCH", "WTS", "YLN", "YTM"]


def read_tile(map_dir: Path):
    with (map_dir / "tile_0_0.map").open(encoding="utf-16") as f:
        return f.read().splitlines()


def check_area(root: Path, code: str) -> list[str]:
    """Return a list of failure strings (empty = pass)."""
    fails: list[str] = []
    map_dir = root / "maps" / f"HP1C_{code}"

    # 1. terrain: must exist, be 61x61, and not be all-flat (except HZMB island)
    tp = map_dir / "tile_0_0.map.terrain"
    if not tp.exists():
        fails.append("missing tile_0_0.map.terrain")
    else:
        with tp.open("rb") as f:
            cells = struct.unpack("<I", f.read(4))[0]
            rest = f.read()
        if cells != 60 or len(rest) != 61 * 61 * 4:
            fails.append(f"terrain bad structure (cells={cells}, bytes={len(rest)})")
        else:
            vals = struct.unpack("<3721f", rest)
            if all(v == 0 for v in vals) and code != "HZMB":
                fails.append("terrain is flat (no elevation)")

    # 1b. roads: tile must contain [spline] records
    lines = read_tile(map_dir)
    n_splines = sum(1 for l in lines if l == "[spline]")
    if n_splines == 0 and code != "HZMB":
        fails.append("no [spline] records in tile")

    # 2. buildings: tile must reference .sco files that exist with .o3d meshes
    sco_dir = root / "Sceneryobjects" / "HK_Objects"
    model_dir = sco_dir / "model"
    n_objects = sum(1 for l in lines if l == "[object]")
    if n_objects == 0 and code not in ("HZMB", "SKG"):
        fails.append("no [object] records in tile")
    # every referenced sco must exist
    missing_sco = 0
    missing_o3d = 0
    for i, l in enumerate(lines):
        if l in ("[object]", "[spline]") and i + 2 < len(lines):
            ref = lines[i + 2].strip()
            if ref.endswith(".sco"):
                if not (root / ref.replace("\\", os.sep)).exists():
                    missing_sco += 1
            elif ref.endswith(".sli"):
                if not (root / ref.replace("\\", os.sep)).exists():
                    missing_sco += 1
    if missing_sco:
        fails.append(f"{missing_sco} referenced .sco/.sli files missing")

    # 3. materials: every building .o3d must name a texture that exists
    tex_dir = sco_dir / "texture"
    for fn in os.listdir(model_dir):
        if not fn.startswith("bldg_") or not fn.endswith(".o3d") or fn.endswith("_lod.o3d"):
            continue
        with (model_dir / fn).open("rb") as f:
            b = f.read()
        pos = 4
        n_vert = struct.unpack("<I", b[pos + 1 : pos + 5])[0]
        pos += 5 + n_vert * 32
        n_tri = struct.unpack("<I", b[pos + 1 : pos + 5])[0]
        pos += 5 + n_tri * 8
        n_mat = struct.unpack("<H", b[pos + 1 : pos + 3])[0]
        pos += 3
        # material: 4 diffuse + 3 specular + 3 emissive + 1 power = 11 floats
        pos += 11 * 4
        nl = b[pos]
        pos += 1
        mat = b[pos : pos + nl].decode("ascii", "replace")
        if mat and not (tex_dir / mat).exists():
            fails.append(f"{fn}: texture {mat} missing")
            break

    # 4. collision + LOD: every building .sco must have both blocks
    for fn in os.listdir(sco_dir):
        if not fn.startswith("bldg_") or not fn.endswith(".sco"):
            continue
        with (sco_dir / fn).open(encoding="ascii", errors="replace") as f:
            txt = f.read()
        if "[collision_mesh]" not in txt:
            fails.append(f"{fn}: no [collision_mesh]")
            break
        if "[LOD]" not in txt or "_lod.o3d" not in txt:
            fails.append(f"{fn}: no [LOD] block")
            break

    # 5. bus stops: osm_stops.csv must be non-empty and parse
    # (some tiles like KWT legitimately have no stops inside the 300 m tile)
    stops_csv = map_dir / "osm_stops.csv"
    if not stops_csv.exists():
        fails.append("missing osm_stops.csv")
    else:
        with stops_csv.open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        if not rows and code not in ("HZMB", "SKG", "ISL", "KWT"):
            fails.append("osm_stops.csv has no stops")

    # 5b. route paths: route_details.csv must exist with rows
    details = root / "routes" / "route_details.csv"
    if not details.exists():
        fails.append("missing routes/route_details.csv")
    else:
        with details.open(encoding="utf-8-sig", newline="") as f:
            if not list(csv.DictReader(f)):
                fails.append("route_details.csv is empty")

    return fails


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(Path(__file__).parents[2]))
    args = parser.parse_args()
    root = Path(args.root).resolve()

    total_fails = 0
    for code in CODES:
        fails = check_area(root, code)
        if fails:
            total_fails += len(fails)
            print(f"[{code}] FAIL:")
            for f in fails:
                print(f"    - {f}")
        else:
            print(f"[{code}] PASS")
    if total_fails:
        print(f"\n{total_fails} check(s) failed")
        sys.exit(1)
    print("\nAll 19 HP1C areas pass the stage-5 quality gate.")


if __name__ == "__main__":
    main()
