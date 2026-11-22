#!/usr/bin/env python3
"""Write HK_BigMap's TTData (Busstops.cfg + .ttp/.ttl) from the map itself.

`Generate-TTData.py` was written for the single-tile district maps: it wrote
tile index 0 for every stop, which is wrong now that the map has 483 tiles, and
it only matched a handful of routes.

This reads the finished map instead of the OSM extracts, so every stop it lists
is one the map actually places:

  Busstops.cfg   [busstop] name / <tile index> / object id / radius / 0 / 0
                 where tile index is the stop's position in global.cfg's [map]
                 list, which is what OMSI uses to find the tile file.
  <line>.ttl     the line and its tour list
  <line>_1.ttp   one trip: title, line, its stops in order, running profile

Routes come from routes/route_details.csv. A route is only written when its
origin and destination both match a stop in the map, so a route that would run
on roads this map does not carry is skipped rather than made up.

Usage:
  python src/scripts/Generate-BigMapTTData.py --root .
"""

import argparse
import csv
import os
import re
import sys
import unicodedata

# Stop records are "name / tile index / object id / radius / 0 / 0".
RADIUS = 60.0


def norm(s):
    """Lower-case, drop bracketed qualifiers and punctuation, collapse spaces."""
    s = (s or "").lower()
    s = re.sub(r"\s*\(.*?\)\s*", " ", s)
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"[^0-9a-z\u4e00-\u9fff ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def tokens(s):
    return set(norm(s).split())


def score(a, b):
    """0..1 similarity of a route terminus and a stop name."""
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    if na in nb or nb in na:
        return 0.9
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / min(len(ta), len(tb))


def read_utf16(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return data[2:].decode("utf-16-le" if data[0] == 0xFF else "utf-16-be")
    return data.decode("cp1252", errors="replace")


# Characters Hong Kong uses that the cp950 codec has no byte for. They are the
# HKSCS / variant forms; OMSI can only draw what the code page holds, so each is
# mapped to the standard character it is a variant of. Without this 275 of the
# 2,126 stop names would come out as question marks ("深水埗" is very common).
CP950_FALLBACK = {
    "\u57d7": "\u57d4",   # 埗 -> 埔
    "\u90a8": "\u6751",   # 邨 -> 村
    "\u6ed9": "\u532f",   # 滙 -> 匯
    "\u8137": "\u814e",   # 脷 -> 腎 (nearest codepage form)
    "\u6822": "\u67cf",   # 栢 -> 柏
    "\u5cef": "\u5cf0",   # 峯 -> 峰
}


def to_cp950_text(text):
    """Make a string encodable in cp950 by swapping HK variant characters."""
    out = []
    for ch in text:
        try:
            ch.encode("cp950")
            out.append(ch)
        except UnicodeEncodeError:
            out.append(CP950_FALLBACK.get(ch, ""))
    return "".join(out)


def write_ansi(path, text):
    """Write a TTData file in the system ANSI code page.

    OMSI reads these as Delphi AnsiStrings, i.e. the machine's ANSI code page.
    This machine reports 950 (Traditional Chinese), so that is the code page the
    engine will use and the one to encode for. Variant characters the code page
    lacks are transliterated instead of becoming question marks.
    """
    normalised = to_cp950_text(text).replace("\r\n", "\n").replace("\n", "\r\n")
    data = normalised.encode("cp950", errors="replace")
    with open(path, "wb") as f:
        f.write(data)
    return "cp950"


def parse_map(map_dir):
    """Return (entries, stops) where entries is [(tile_x, tile_y, file)] and
    stops is [(name, tile_index, object_id)]."""
    cfg = read_utf16(os.path.join(map_dir, "global.cfg"))

    # [map] records, in order: the 0-based position is the tile index OMSI uses
    entries = []
    for m in re.finditer(r"\[map\]\r?\n(-?\d+)\r?\n(-?\d+)\r?\n([^\r\n]+)", cfg):
        entries.append((int(m.group(1)), int(m.group(2)), m.group(3).strip()))

    stops = []
    for i, (tx, ty, fname) in enumerate(entries):
        path = os.path.join(map_dir, fname)
        if not os.path.isfile(path):
            continue
        # Walk the tile line by line: an object record is
        #   [object] / 0 / <path.sco> / id / x / y / z / heading / pitch / bank / n
        # followed by n label lines.
        lines = read_utf16(path).replace("\r\n", "\n").split("\n")
        j = 0
        while j < len(lines):
            if lines[j].strip() != "[object]":
                j += 1
                continue
            try:
                obj_path = lines[j + 2].strip()
                oid = int(lines[j + 3].strip())
                label_count = int(lines[j + 10].strip())
            except (IndexError, ValueError):
                j += 1
                continue
            labels = []
            for k in range(label_count):
                if j + 11 + k < len(lines):
                    labels.append(lines[j + 11 + k].strip())
            if "HK_BusStop.sco" in obj_path and labels:
                stops.append((labels[0], i, oid))
            j += 11 + label_count
    return entries, stops


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".")
    ap.add_argument("--map", default="HK_BigMap")
    ap.add_argument("--min-stops", type=int, default=2,
                    help="only routes whose both termini are found")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    map_dir = os.path.join(root, "maps", args.map)
    if not os.path.isdir(map_dir):
        sys.exit(f"map not found: {map_dir}")

    entries, stops = parse_map(map_dir)
    if not stops:
        sys.exit("no bus stops found in the map; run the converter first")
    print(f"map: {len(entries)} tiles, {len(stops)} bus stops")

    tt = os.path.join(map_dir, "TTData")
    os.makedirs(tt, exist_ok=True)

    # ---- Busstops.cfg ----
    head = ("---------------------------\r\n"
            "Time Table BusStopList File\r\n"
            "---------------------------\r\n\r\n"
            "Created with omsi2-hk-1to1\r\n\r\n")
    body = []
    for name, tile_index, oid in stops:
        body.append(f"[busstop]\r\n{name}\r\n{tile_index}\r\n{oid}\r\n"
                    f"{RADIUS:.10f}\r\n0\r\n0\r\n\r\n")
    write_ansi(os.path.join(tt, "Busstops.cfg"), head + "".join(body))
    print(f"Busstops.cfg: {len(stops)} entries")

    # ---- routes ----
    csv_path = os.path.join(root, "routes", "route_details.csv")
    if not os.path.isfile(csv_path):
        print("routes/route_details.csv missing - only Busstops.cfg written")
        return
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        routes = list(csv.DictReader(f))
    bus = [r for r in routes if r.get("service_group") == "Franchised public bus"]
    print(f"route catalogue: {len(bus)} franchised routes")

    # Normalize each mapped stop once. The route catalogue contains thousands
    # of rows; recomputing Unicode normalization for every route/stop pair made
    # a full territory rebuild unnecessarily slow.
    by_name = [(st, norm(st[0])) for st in stops]
    written = skipped = 0
    for r in bus:
        origin, dest = r.get("origin", ""), r.get("destination", "")
        number = (r.get("route_number") or "").strip()
        if not number:
            continue
        # best stop for each terminus
        def best(text):
            nt = norm(text)
            hi, hit = 0.0, None
            for st, nsn in by_name:
                if not nt or not nsn:
                    sc = 0.0
                elif nt == nsn:
                    sc = 1.0
                elif nt in nsn or nsn in nt:
                    sc = 0.9
                else:
                    ta, tb = set(nt.split()), set(nsn.split())
                    sc = len(ta & tb) / min(len(ta), len(tb)) if ta and tb else 0.0
                if sc > hi:
                    hi, hit = sc, st
            return hi, hit

        o_sc, o_st = best(origin)
        d_sc, d_st = best(dest)
        if o_sc < 0.5 or d_sc < 0.5 or o_st is None or d_st is None:
            skipped += 1
            continue
        if o_st[2] == d_st[2]:
            skipped += 1
            continue

        safe = re.sub(r"[^\w\-]", "_", number) or "line"
        # .ttp: one trip between the two matched stops
        trip = (f"[trip]\r\n\r\n{dest}\r\n{number}\r\n"
                f"[station_typ2]\r\n{o_st[2]}\r\n"
                f"[station_typ2]\r\n{d_st[2]}\r\n"
                f"[profile]\r\n{number} 30\r\n")
        write_ansi(os.path.join(tt, f"{safe}_1.ttp"), trip)
        # .ttl: the line, pointing at that trip
        ttl = ("[userallowed]\r\n[priority]\r\n1\r\n"
               f"[newtour]\r\n1 0 0\r\n[addtrip]\r\n{safe}_1 {number} 360\r\n")
        write_ansi(os.path.join(tt, f"{safe}.ttl"), ttl)
        written += 1

    print(f"TTData: {written} routes written, {skipped} skipped (terminus not on this map)")


if __name__ == "__main__":
    main()
