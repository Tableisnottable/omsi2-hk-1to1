#!/usr/bin/env python3
"""Convert an OSM extract into a loadable OMSI 1:1 map tile (HP1C district).

Writes, under the repository root:
  Maps\\HP1C_<code>\\global.cfg, tile_0_0.map, tile_0_0.map.terrain,
     drivers.txt, ailists.cfg, osm_*.csv, osm_import.json
  Splines\\HK_Roads\\*.sli and Splines\\HK_Roads\\texture\\*.bmp
  Sceneryobjects\\HK_Objects\\*.sco and model\\*.o3d

Tile files (global.cfg / tile_*.map) are UTF-16LE with BOM; the tile uses
[version] 14 so every [spline]/[object] field is present. Coordinates are
tile-local metres (x east, y north, z up), heading clockwise from north.
"""
import argparse
import json
import math
import os
import random
import struct
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict

TILE_SIZE = 300.0
VERSION = 14

# Road categories -> (.sli name, carriageway width in metres)
ROAD_CATS = {
    "motorway":      ("motorway.sli", 14.0),
    "motorway_link": ("motorway.sli", 14.0),
    "trunk":         ("trunk.sli", 12.0),
    "trunk_link":    ("trunk.sli", 12.0),
    "primary":       ("primary.sli", 10.0),
    "primary_link":  ("primary.sli", 10.0),
    "secondary":     ("secondary.sli", 8.0),
    "secondary_link":("secondary.sli", 8.0),
    "tertiary":      ("tertiary.sli", 7.0),
    "tertiary_link": ("tertiary.sli", 7.0),
    "residential":   ("residential.sli", 6.0),
    "unclassified":  ("residential.sli", 6.0),
    "living_street": ("residential.sli", 6.0),
    "service":       ("service.sli", 4.5),
}
DRIVABLE = set(ROAD_CATS)


class Projector:
    """Equirectangular projection around the district centre (m)."""

    def __init__(self, lat0, lon0):
        self.lat0 = lat0
        self.lon0 = lon0
        self.mpdlat = 110574.0
        self.mpdlon = 111320.0 * math.cos(math.radians(lat0))

    def to_local(self, lat, lon):
        x = (lon - self.lon0) * self.mpdlon
        y = (lat - self.lat0) * self.mpdlat
        return x, y


def clip_segment(p1, p2, lo, hi):
    """Liang-Barsky clip of segment p1->p2 to the axis-aligned rect [lo,hi]^2.
    Returns (a, b) clipped endpoints or None if fully outside."""
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    t0, t1 = 0.0, 1.0
    for p, d in ((p1[0], dx), (p1[1], dy)):
        if abs(d) < 1e-12:
            if p < lo or p > hi:
                return None
            continue
        t_in = (lo - p) / d
        t_out = (hi - p) / d
        if t_in > t_out:
            t_in, t_out = t_out, t_in
        t0 = max(t0, t_in)
        t1 = min(t1, t_out)
        if t0 > t1:
            return None
    return (p1[0] + t0 * dx, p1[1] + t0 * dy), (p1[0] + t1 * dx, p1[1] + t1 * dy)


def polygon_area(pts):
    a = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2.0


def write_utf16(path, lines):
    """Write a tile-type text file as UTF-16LE with BOM."""
    text = "\r\n".join(str(x) for x in lines) + "\r\n"
    with open(path, "wb") as f:
        f.write(b"\xff\xfe" + text.encode("utf-16-le"))


def write_ascii(path, lines):
    with open(path, "w", encoding="ascii", newline="\r\n") as f:
        f.write("\r\n".join(str(x) for x in lines) + "\r\n")


def write_bmp(path, width, height, pixel_fn):
    """24-bit uncompressed bottom-up BMP; pixel_fn(x, y) -> (r, g, b)."""
    row_size = (width * 3 + 3) & ~3
    data = bytearray()
    for y in range(height - 1, -1, -1):
        for x in range(width):
            r, g, b = pixel_fn(x, y)
            data += bytes((b, g, r))
        data += b"\x00" * (row_size - width * 3)
    file_size = 54 + len(data)
    header = b"BM" + struct.pack("<IHHI", file_size, 0, 0, 54)
    info = struct.pack("<IiiHHIIiiII", 40, width, height, 1, 24, 0, len(data), 2835, 2835, 0, 0)
    with open(path, "wb") as f:
        f.write(header + info + bytes(data))


def write_o3d(path, vertices, triangles, material_name=b""):
    """Minimal .o3d mesh, version 3 (u32 counts, 16-bit indices, no scramble).
    Vertices may be 3-tuples (x, y, z); normals/UVs are then zeroed."""
    out = bytearray(b"\x84\x19\x03\x00")  # magic, version 3, flags 0
    out += b"\x17" + struct.pack("<I", len(vertices))
    for v in vertices:
        if len(v) == 3:
            v = (v[0], v[1], v[2], 0.0, 0.0, 1.0, 0.0, 0.0)
        out += struct.pack("<8f", *v)
    out += b"\x49" + struct.pack("<I", len(triangles))
    for tri in triangles:
        out += struct.pack("<3H", *tri) + struct.pack("<H", 0)
    out += b"\x26" + struct.pack("<H", 1)
    out += struct.pack("<4f", 0.62, 0.62, 0.62, 1.0)   # diffuse
    out += struct.pack("<3f", 0.0, 0.0, 0.0)           # specular
    out += struct.pack("<3f", 0.0, 0.0, 0.0)           # emissive
    out += struct.pack("<f", 1.0)                      # power
    out += struct.pack("<B", len(material_name)) + material_name
    ident = [1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0]
    out += b"\x79" + struct.pack("<16f", *ident)
    with open(path, "wb") as f:
        f.write(bytes(out))


def building_box_mesh(w, d, h):
    """Box from z=0 to z=h, centred on origin, w across x, d along y."""
    hw, hd = w / 2.0, d / 2.0
    verts = [
        (-hw, -hd, 0.0), (hw, -hd, 0.0), (hw, hd, 0.0), (-hw, hd, 0.0),
        (-hw, -hd, h), (hw, -hd, h), (hw, hd, h), (-hw, hd, h),
    ]
    n = [(0.0, 0.0, 1.0)] * len(verts)
    tris = [
        # top
        (4, 5, 6), (4, 6, 7),
        # bottom
        (0, 2, 1), (0, 3, 2),
        # front (+y)
        (3, 2, 6), (3, 6, 7),
        # back (-y)
        (0, 1, 5), (0, 5, 4),
        # right (+x)
        (1, 2, 6), (1, 6, 5),
        # left (-x)
        (0, 4, 7), (0, 7, 3),
    ]
    return verts, tris, n


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--osm", required=True, help="Path to the .osm extract")
    ap.add_argument("--mapcode", required=True, help="HP1C code, e.g. CW")
    ap.add_argument("--centre", required=True, help="'lat,lon' of the tile centre")
    ap.add_argument("--root", default=".", help="Repository root")
    args = ap.parse_args()

    lat0, lon0 = (float(x) for x in args.centre.split(","))
    proj = Projector(lat0, lon0)

    root = os.path.abspath(args.root)
    map_dir = os.path.join(root, "maps", f"HP1C_{args.mapcode}")
    splines_dir = os.path.join(root, "Splines", "HK_Roads")
    sco_dir = os.path.join(root, "Sceneryobjects", "HK_Objects")
    model_dir = os.path.join(sco_dir, "model")
    for d in (map_dir, splines_dir, os.path.join(splines_dir, "texture"), sco_dir, model_dir):
        os.makedirs(d, exist_ok=True)

    print(f"[{args.mapcode}] parsing {args.osm} ...")
    tree = ET.parse(args.osm)
    osm = tree.getroot()

    nodes = {}
    for n in osm.findall("node"):
        nodes[n.get("id")] = (float(n.get("lat")), float(n.get("lon")))

    # ---- collect ways ----
    highways = []   # (id, tags, [node ids])
    buildings = []  # (id, tags, [node ids])
    stop_ways = []  # platform ways
    for w in osm.findall("way"):
        tags = {t.get("k"): t.get("v") for t in w.findall("tag")}
        refs = [nd.get("ref") for nd in w.findall("nd")]
        if "highway" in tags:
            highways.append((w.get("id"), tags, refs))
        if "building" in tags:
            buildings.append((w.get("id"), tags, refs))
        if tags.get("public_transport") == "platform" or tags.get("highway") == "platform":
            stop_ways.append((w.get("id"), tags, refs))

    # ---- nodes for CSV ----
    node_rows = [{"id": k, "latitude": v[0], "longitude": v[1], "name": ""}
                 for k, v in nodes.items()]
    node_by_id = {r["id"]: r for r in node_rows}
    for n in osm.findall("node"):
        nm = next((t.get("v") for t in n.findall("tag") if t.get("k") == "name"), None)
        if nm:
            node_by_id[n.get("id")]["name"] = nm

    # ---- build splines ----
    spline_records = []
    next_sid = 1
    way_rows = []
    for wid, tags, refs in highways:
        hw = tags.get("highway")
        if hw not in DRIVABLE:
            continue
        sli, width = ROAD_CATS[hw]
        pts = []
        for rid in refs:
            if rid not in nodes:
                continue
            lat, lon = nodes[rid]
            x, y = proj.to_local(lat, lon)
            x += TILE_SIZE / 2.0
            y += TILE_SIZE / 2.0
            pts.append((x, y))
        if len(pts) < 2:
            continue
        # clip each segment, keep chaining info
        emitted = []
        for i in range(len(pts) - 1):
            seg = clip_segment(pts[i], pts[i + 1], 0.0, TILE_SIZE)
            if seg is None:
                continue
            a, b = seg
            length = math.hypot(b[0] - a[0], b[1] - a[1])
            if length < 0.15:
                continue
            emitted.append((a, b, length))
        if not emitted:
            continue
        ids = []
        for a, b, length in emitted:
            heading = math.degrees(math.atan2(b[0] - a[0], b[1] - a[1]))
            sid = next_sid
            next_sid += 1
            ids.append(sid)
            spline_records.append({
                "file": f"Splines\\HK_Roads\\{sli}",
                "id": sid,
                "pos": (a[0], a[1], 0.0),  # x east, y north, z up
                "heading": heading,
                "length": length,
                "radius": 0.0,
            })
        by_id = {r["id"]: r for r in spline_records}
        for j, sid in enumerate(ids):
            rec = by_id[sid]
            rec["prev"] = ids[j - 1] if j > 0 else -1
            rec["next"] = ids[j + 1] if j < len(ids) - 1 else -1
        # CSV row for the way
        coords = " ".join(f"{nodes[rid][1]},{nodes[rid][0]}" for rid in refs if rid in nodes)
        way_rows.append({
            "id": wid, "highway": hw, "name": tags.get("name", ""),
            "oneway": tags.get("oneway", ""), "nodes": " ".join(refs),
            "coordinates": coords,
        })

    # ---- buildings ----
    building_rows = []
    bldg_sco = []
    bldg_meshes = []
    bbox_list = []
    for wid, tags, refs in buildings:
        pts = []
        for rid in refs:
            if rid not in nodes:
                continue
            lat, lon = nodes[rid]
            x, y = proj.to_local(lat, lon)
            x += TILE_SIZE / 2.0
            y += TILE_SIZE / 2.0
            pts.append((x, y))
        if len(pts) < 3:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        if max(xs) < 0 or min(xs) > TILE_SIZE or max(ys) < 0 or min(ys) > TILE_SIZE:
            continue
        area = polygon_area(pts)
        if area < 9.0:
            continue
        # height
        h = None
        if tags.get("height"):
            try:
                h = float(tags["height"])
            except ValueError:
                h = None
        if h is None and tags.get("building:levels"):
            try:
                h = float(tags["building:levels"]) * 3.2
            except ValueError:
                h = None
        if h is None:
            h = 10.0
        h = min(max(h, 3.0), 400.0)
        w = max(xs) - min(xs)
        d = max(ys) - min(ys)
        cx = (min(xs) + max(xs)) / 2.0
        cy = (min(ys) + max(ys)) / 2.0
        bbox_list.append((cx, cy, w, d, h, wid, tags, pts))
        building_rows.append({
            "id": wid, "building": tags.get("building", ""),
            "name": tags.get("name", ""),
            "levels": tags.get("building:levels", ""),
            "height": tags.get("height", ""),
            "nodes": " ".join(refs),
            "coordinates": " ".join(f"{nodes[rid][1]},{nodes[rid][0]}" for rid in refs if rid in nodes),
        })

    # sort by area descending, cap
    bbox_list.sort(key=lambda b: -b[4])
    bbox_list = bbox_list[:400]

    obj_records = []
    next_oid = 1_000_000
    for cx, cy, w, d, h, wid, tags, pts in bbox_list:
        if w < 1.5 or d < 1.5:
            continue
        mesh_name = f"bldg_{wid}.o3d"
        verts, tris, nrm = building_box_mesh(w, d, h)
        write_o3d(os.path.join(model_dir, mesh_name), verts, tris, b"")
        sco_name = f"bldg_{wid}.sco"
        write_ascii(os.path.join(sco_dir, sco_name), [
            "[friendlyname]", f"HK Building {wid}", "",
            "[groups]", "2", "Hong Kong", "Buildings", "",
            "[mesh]", f"model\\{mesh_name}",
        ])
        # place the box: centre offset from tile origin, base at z=0
        obj_records.append({
            "file": f"Sceneryobjects\\HK_Objects\\{sco_name}",
            "id": next_oid,
            "pos": (cx, cy, 0.0),
            "heading": 0.0,
            "labels": [],
        })
        next_oid += 1

    # ---- bus stops ----
    stop_rows = []
    stop_positions = []
    for n in osm.findall("node"):
        tags = {t.get("k"): t.get("v") for t in n.findall("tag")}
        if tags.get("highway") == "bus_stop" or tags.get("public_transport") in ("platform", "stop_position"):
            if n.get("id") not in nodes:
                continue
            lat, lon = nodes[n.get("id")]
            x, y = proj.to_local(lat, lon)
            x += TILE_SIZE / 2.0
            y += TILE_SIZE / 2.0
            if 0 <= x <= TILE_SIZE and 0 <= y <= TILE_SIZE:
                stop_positions.append((x, y, tags.get("name", "")))
                stop_rows.append({
                    "id": n.get("id"), "name": tags.get("name", ""),
                    "latitude": lat, "longitude": lon,
                })
    for wid, tags, refs in stop_ways:
        pts = []
        for rid in refs:
            if rid in nodes:
                lat, lon = nodes[rid]
                x, y = proj.to_local(lat, lon)
                x += TILE_SIZE / 2.0
                y += TILE_SIZE / 2.0
                pts.append((x, y))
        if len(pts) >= 3:
            cx = sum(p[0] for p in pts) / len(pts)
            cy = sum(p[1] for p in pts) / len(pts)
            if 0 <= cx <= TILE_SIZE and 0 <= cy <= TILE_SIZE:
                stop_positions.append((cx, cy, tags.get("name", "")))

    # bus stop pole object
    pole_o3d = os.path.join(model_dir, "HK_BusStop.o3d")
    pole_sco = os.path.join(sco_dir, "HK_BusStop.sco")
    pv, pt, pn = building_box_mesh(0.12, 0.12, 2.6)
    write_o3d(pole_o3d, pv, pt, b"")
    write_ascii(pole_sco, [
        "[friendlyname]", "HK Bus Stop", "",
        "[groups]", "2", "Hong Kong", "Bus Stops", "",
        "[mesh]", "model\\HK_BusStop.o3d",
    ])
    stop_records = []
    for (x, y, name) in stop_positions:
        stop_records.append({
            "file": "Sceneryobjects\\HK_Objects\\HK_BusStop.sco",
            "id": next_oid,
            "pos": (x, y, 0.0),
            "heading": 0.0,
            "labels": [name] if name else [],
        })
        next_oid += 1

    # ---- write tile file ----
    tile_lines = ["[version]", str(VERSION), "", "[terrain]", ""]
    for r in spline_records:
        tile_lines += [
            "[spline]", "0", r["file"], str(r["id"]), str(r["prev"]), str(r["next"]),
            f"{r['pos'][0]:.4f}", f"{r['pos'][2]:.4f}", f"{r['pos'][1]:.4f}",
            f"{r['heading']:.4f}", f"{r['length']:.4f}", f"{r['radius']:.4f}",
            "0", "0", "0", "0", "0", "0", "0",
        ]
        tile_lines.append("[spline_terrain_align]")
        tile_lines.append("")
    for r in obj_records + stop_records:
        tile_lines += [
            "[object]", "0", r["file"], str(r["id"]),
            f"{r['pos'][0]:.4f}", f"{r['pos'][1]:.4f}", f"{r['pos'][2]:.4f}",
            f"{r['heading']:.4f}", "0", "0",
            str(len(r["labels"])),
        ]
        tile_lines += r["labels"]
        tile_lines.append("")

    write_utf16(os.path.join(map_dir, "tile_0_0.map"), tile_lines)

    # ---- terrain (flat) ----
    terrain_path = os.path.join(map_dir, "tile_0_0.map.terrain")
    with open(terrain_path, "wb") as f:
        f.write(struct.pack("<I", 60))
        for _ in range(61 * 61):
            f.write(struct.pack("<f", 0.0))

    # ---- global.cfg ----
    write_utf16(os.path.join(map_dir, "global.cfg"), [
        "[name]", f"HP1C {args.mapcode}", "",
        "[friendlyname]", f"HK 1:1 Map ({args.mapcode}) - OSM import", "",
        "[map]", "0", "0", "tile_0_0.map",
    ])

    # drivers / ailists if missing
    for fname, content in (
        ("drivers.txt", ["DefaultDriver"]),
        ("ailists.cfg", ["[sorts]", "1", "0", "", "[ailist]", "0", "-1"]),
    ):
        p = os.path.join(map_dir, fname)
        if not os.path.exists(p):
            write_utf16(p, content)

    # ---- spline .sli + textures ----
    rng = random.Random(7)
    write_bmp(os.path.join(splines_dir, "texture", "asphalt.bmp"), 256, 256,
              lambda x, y: (90 + rng.randint(-8, 8), 90 + rng.randint(-8, 8), 88 + rng.randint(-8, 8)))
    for sli_name, width in sorted({v[0]: v[1] for v in ROAD_CATS.values()}.items()):
        half = width / 2.0
        write_ascii(os.path.join(splines_dir, sli_name), [
            "[texture]", "texture\\asphalt.bmp", "",
            "[profile]", "0",
            "[profilepnt]", f"{-half:.4f}", "0", "0", "1",
            "[profilepnt]", f"{half:.4f}", "0", "1", "1",
            "",
            "[path]", "0", "0", "0", f"{width:.4f}", "2",
            "",
            "[terrainholeprofile]",
            "[terrainholeprofilepnt]", f"{-half - 0.3:.4f}", "-0.1", "1",
            "[terrainholeprofilepnt]", f"{half + 0.3:.4f}", "-0.1", "1",
        ])

    # ---- CSVs ----
    import csv
    with open(os.path.join(map_dir, "osm_nodes.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "latitude", "longitude", "name"])
        w.writeheader()
        w.writerows(node_rows)
    with open(os.path.join(map_dir, "osm_ways.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "highway", "name", "oneway", "nodes", "coordinates"])
        w.writeheader()
        w.writerows(way_rows)
    with open(os.path.join(map_dir, "osm_stops.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "name", "latitude", "longitude"])
        w.writeheader()
        w.writerows(stop_rows)
    with open(os.path.join(map_dir, "osm_buildings.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "building", "name", "levels", "height", "nodes", "coordinates"])
        w.writeheader()
        w.writerows(building_rows)

    manifest = {
        "source": args.osm, "importedUtc": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "mapCode": args.mapcode, "nodes": len(node_rows),
        "highwayWays": len(way_rows), "buildings": len(building_rows),
        "stops": len(stop_rows),
        "splines": len(spline_records), "objects": len(obj_records),
        "nextStep": "Run in OpenOMSI; terrain heights and authored meshes come later.",
    }
    with open(os.path.join(map_dir, "osm_import.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"[{args.mapcode}] roads={len(way_rows)} splines={len(spline_records)} "
          f"buildings={len(building_rows)} meshes={len(bbox_list)} stops={len(stop_rows)}")


if __name__ == "__main__":
    main()
