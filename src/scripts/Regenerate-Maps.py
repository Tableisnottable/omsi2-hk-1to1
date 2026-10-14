#!/usr/bin/env python3
"""Regenerate all district map tiles (buildings + terrain) after a converter change.

Runs Convert-OsmToMap.py for every district (preserving existing terrain),
then Add-TerrainElevation.py for any tile missing elevation.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from hp1c_centres import CENTRES  # noqa: E402

ROOT = Path(__file__).parents[2]
CONVERT = ROOT / "src" / "scripts" / "Convert-OsmToMap.py"
ELEVATE = ROOT / "src" / "scripts" / "Add-TerrainElevation.py"


def run(cmd: list[str]) -> bool:
    print(">>>", " ".join(str(c) for c in cmd), flush=True)
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
    for line in (r.stdout or "").splitlines()[-2:]:
        print("   ", line, flush=True)
    if r.returncode != 0:
        for line in (r.stderr or "").splitlines()[-4:]:
            print("   !!", line, flush=True)
        return False
    return True


def main() -> None:
    codes = sorted(CENTRES.keys())
    for code in codes:
        c = CENTRES[code]
        centre = f"{c['lat']},{c['lon']}"
        osm = ROOT / "src" / "osm" / f"{code}.osm"
        if not osm.exists():
            print(f"!! {code}: no OSM extract", flush=True)
            continue
        if not run([sys.executable, CONVERT, "--osm", osm, "--mapcode", code, "--centre", centre, "--root", ROOT]):
            continue
        time.sleep(0.5)
    # elevate any tile still flat
    for code in codes:
        terrain = ROOT / "maps" / f"HP1C_{code}" / "tile_0_0.map.terrain"
        if not terrain.exists():
            print(f"!! {code}: missing terrain", flush=True)
            run([sys.executable, ELEVATE, "--mapcode", code, "--root", ROOT])
            time.sleep(1)
    print("done", flush=True)


if __name__ == "__main__":
    main()
