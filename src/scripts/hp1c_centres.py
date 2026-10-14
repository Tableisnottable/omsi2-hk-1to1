#!/usr/bin/env python3
"""District centre lookup shared by the terrain and map tools.

Loads src/scripts/hp1c_centres.json into CENTRES: {CODE: {"lat": ..., "lon": ...}}.
"""

from __future__ import annotations

import json
from pathlib import Path

_CENTRES_PATH = Path(__file__).parent / "hp1c_centres.json"

with _CENTRES_PATH.open(encoding="utf-8") as _f:
    _data = json.load(_f)

CENTRES = {code: {"lat": float(c["lat"]), "lon": float(c["lon"])} for code, c in _data["centres"].items()}

if __name__ == "__main__":
    for code, c in sorted(CENTRES.items()):
        print(f"{code}: {c['lat']}, {c['lon']}")
