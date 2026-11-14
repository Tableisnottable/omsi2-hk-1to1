#!/usr/bin/env python3
"""Repair generated road contact offline; never start the simulator.

Keep spline IDs, paths and elevations intact. Add only the uncovered wedges at
shared road endpoints, and cap every terrain-cell corner beneath each road plane.
This avoids the old nearest-centreline, vertex-only terrain fit, whose interpolated
triangles could rise through a road even when its sampled centreline was clear.
"""
import argparse
import hashlib
import importlib.util
import json
import math
import re
import shutil
import struct
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


def load_helper():
    spec = importlib.util.spec_from_file_location('road_tt', Path(__file__).with_name('Generate-TsingYi-Timetable.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cross(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def hull(points):
    points = sorted(set(points))
    def half(seq):
        result = []
        for p in seq:
            while len(result) >= 2 and cross(result[-2], result[-1], p) <= 1e-9:
                result.pop()
            result.append(p)
        return result
    return half(points)[:-1]+half(points[::-1])[:-1]


def clip(poly, a, b, inside=True):
    """Clip a polygon to the left (or right) of a directed infinite line."""
    if not poly:
        return []
    out = []; p = poly[-1]; dp = cross(a, b, p)*(1 if inside else -1)
    for q in poly:
        dq = cross(a, b, q)*(1 if inside else -1)
        if (dp >= 0) != (dq >= 0):
            t = dp/(dp-dq)
            out.append((p[0]+(q[0]-p[0])*t, p[1]+(q[1]-p[1])*t))
        if dq >= 0:
            out.append(q)
        p, dp = q, dq
    return out


def area(poly):
    return abs(sum(a[0]*b[1]-a[1]*b[0] for a, b in zip(poly, poly[1:]+poly[:1])))/2 if poly else 0


def subtract(poly, cutter):
    """Convex polygon minus convex CCW cutter, as disjoint convex pieces."""
    pieces = []; remaining = poly
    for a, b in zip(cutter, cutter[1:]+cutter[:1]):
        outside = clip(remaining, a, b, False)
        if area(outside) > 1e-7:
            pieces.append(outside)
        remaining = clip(remaining, a, b)
        if not remaining:
            break
    return pieces


def inventory(root, helper):
    folder = root/'maps/HK_TsingYi'
    cfg = helper.read(folder/'global.cfg')
    tiles = []; roads = []; nodes = defaultdict(list)
    for tx, ty, name in re.findall(r'\[map\]\s*\n(-?\d+)\s*\n(-?\d+)\s*\n([^\r\n]+)', cfg):
        tx, ty = int(tx), int(ty)
        path = folder/name; data = helper.read(path).splitlines()
        tiles.append((tx, ty, path, data))
        for i, token in enumerate(data):
            if token != '[spline]':
                continue
            r = data[i+1:i+19]
            if float(r[10]) or abs(float(r[11])-float(r[12])) > 1e-7:
                raise ValueError('Road repair requires the straight, constant-grade generated splines')
            a = (tx*300+float(r[5]), ty*300+float(r[7]), float(r[6]))
            angle = math.radians(float(r[8])); length = float(r[9]); grade = float(r[11])/100
            dx, dy = math.sin(angle), math.cos(angle)
            b = (a[0]+dx*length, a[1]+dy*length, a[2]+grade*length)
            sli = helper.read(root/r[1].replace('\\', '/'))
            hp = re.search(r'\[heightprofile\]\s*\n([^\n]+)\n([^\n]+)\n([^\n]+)\n([^\n]+)', sli)
            left, right, z0, z1 = map(float, hp.groups())
            if abs(z0-z1) > 1e-7 or left >= right:
                raise ValueError('Unexpected road cross-section')
            road = dict(id=int(r[2]), a=a, b=b, dx=dx, dy=dy, length=length,
                        grade=grade, left=left, right=right, surface=z0)
            roads.append(road)
            for end, sign in ((a, 1), (b, -1)):
                nodes[tuple(round(v, 2) for v in end)].append((road, end, sign))
    return cfg, tiles, roads, nodes


def connectors(nodes):
    result = []
    for node, arms in nodes.items():
        if len(arms) < 2:
            continue
        ends = []; cutters = []
        radius = max(max(abs(r['left']), abs(r['right'])) for r, _, _ in arms)*4+1
        for r, end, sign in arms:
            dx, dy = r['dx'], r['dy']
            left = (end[0]+dy*r['left'], end[1]-dx*r['left'])
            right = (end[0]+dy*r['right'], end[1]-dx*r['right'])
            ends.extend((left, right))
            cutters.append(hull([left, right,
                (left[0]+dx*sign*radius, left[1]+dy*sign*radius),
                (right[0]+dx*sign*radius, right[1]+dy*sign*radius)]))
        pieces = [hull(ends)]
        for cutter in cutters:
            pieces = [q for p in pieces for q in subtract(p, cutter)]
        # Discard roundoff slivers at otherwise straight joins. Do not cover any
        # existing sloped road: that would introduce a new flat-pad speed bump.
        for p in pieces:
            if area(p) > .002:
                result.append((p, sum(e[2]+r['surface'] for r, e, _ in arms)/len(arms)))
    return result


def corridor(r):
    a, b, dx, dy = r['a'], r['b'], r['dx'], r['dy']
    left, right = r['left']-.03, r['right']+.03
    return hull([(p[0]+dy*w, p[1]-dx*w) for p in (a, b) for w in (left, right)])


def terrain_caps(roads, patches):
    caps = {}; cells = set()
    def cover(poly, height):
        xmin, xmax = min(p[0] for p in poly), max(p[0] for p in poly)
        ymin, ymax = min(p[1] for p in poly), max(p[1] for p in poly)
        for iy in range(math.floor(ymin/5), math.floor(ymax/5)+1):
            # Clip once per grid row before enumerating its columns.
            row = clip(clip(poly, (0, iy*5), (1, iy*5)), (1, (iy+1)*5), (0, (iy+1)*5))
            if not row:
                continue
            for ix in range(math.floor(min(p[0] for p in row)/5), math.floor(max(p[0] for p in row)/5)+1):
                cell = clip(clip(row, (ix*5, 1), (ix*5, 0)), ((ix+1)*5, 0), ((ix+1)*5, 1))
                if area(cell) < 1e-9:
                    continue
                cells.add((ix, iy))
                for key in ((ix,iy), (ix+1,iy), (ix,iy+1), (ix+1,iy+1)):
                    # A triangle interpolates linearly: constraining ALL corners
                    # below the road plane guarantees clearance for either diagonal.
                    z = height(key[0]*5, key[1]*5)-.25
                    caps[key] = min(caps.get(key, math.inf), z)
    for r in roads:
        def height(x, y, r=r):
            return r['a'][2]+((x-r['a'][0])*r['dx']+(y-r['a'][1])*r['dy'])*r['grade']+r['surface']
        cover(corridor(r), height)
    for poly, z in patches:
        cover(poly, lambda x, y, z=z: z)
    return caps, cells


def mesh_text(polygons, tx, ty):
    vertices = []; triangles = []
    for poly, z in polygons:
        offset = len(vertices)
        vertices.extend((x-tx*300, y-ty*300, z) for x, y in poly)
        # Same Z-up to DirectX Y-up transform and upward winding as Build-TsingYi.
        triangles.extend((offset, offset+i+1, offset+i) for i in range(1,len(poly)-1))
    lines = ['xof 0303txt 0032', 'Frame RootFrame {', 'FrameTransformMatrix {',
             '1,0,0,0, 0,0,1,0, 0,1,0,0, 0,0,0,1;;', '}', 'Mesh {', f'{len(vertices)};']
    lines += [f'{x:.6f};{y:.6f};{z:.6f};'+(',' if i<len(vertices)-1 else ';') for i,(x,y,z) in enumerate(vertices)]
    lines += [f'{len(triangles)};']
    lines += [f'3;{a},{b},{c};'+(',' if i<len(triangles)-1 else ';') for i,(a,b,c) in enumerate(triangles)]
    lines += ['MeshTextureCoords {', f'{len(vertices)};']
    lines += [f'{x/8:.6f};{y/8:.6f};'+(',' if i<len(vertices)-1 else ';') for i,(x,y,_) in enumerate(vertices)]
    lines += ['}', 'MeshMaterialList {', '1;', f'{len(triangles)};', ','.join('0' for _ in triangles)+';;',
              'Material {', '1;1;1;1;;', '0;', '0;0;0;;', '0;0;0;;',
              'TextureFilename {', '"asphalt.bmp";', '}', '}', '}', '}', '}']
    return '\r\n'.join(lines)+'\r\n'


def repair(root, audit_only=False):
    root = Path(root).resolve(); helper = load_helper()
    cfg, tiles, roads, nodes = inventory(root, helper)
    patches = connectors(nodes); caps, cells = terrain_caps(roads, patches)
    folder = root/'maps/HK_TsingYi'; objects = root/'Sceneryobjects/HK_TsingYi'
    grouped = defaultdict(list)
    for poly, z in patches:
        tx, ty = math.floor(poly[0][0]/300), math.floor(poly[0][1]/300)
        # Object assignment must use a tile that actually exists.
        if (tx,ty) not in {(x,y) for x,y,_,_ in tiles}:
            raise ValueError(f'Join lies outside generated tiles: {tx},{ty}')
        grouped[tx,ty].append((poly,z))
    manifest = json.loads((folder/'build_manifest.json').read_text(encoding='utf-8'))
    existing = manifest.get('road_contact_repair', {}).get('surface_object_ids', {})
    nextid = int(re.search(r'\[NextIDCode\]\s*\n(\d+)', cfg)[1])
    changed_vertices = 0; failures = 0; ids = {}; pending = {}
    for tx, ty, path, data in tiles:
        terrain = path.with_name(path.name+'.terrain'); raw = terrain.read_bytes()
        if len(raw) != 14888 or struct.unpack_from('<I', raw)[0] != 60:
            raise ValueError(f'Unexpected terrain format: {terrain}')
        heights = list(struct.unpack('<3721f', raw[4:]))
        for j in range(61):
            for i in range(61):
                cap = caps.get((tx*60+i,ty*60+j))
                index = j*61+i
                if cap is not None and heights[index] > cap+1e-5:
                    changed_vertices += 1
                    heights[index] = cap
                if cap is not None and struct.unpack('<f',struct.pack('<f',heights[index]))[0] > cap+.001:
                    failures += 1
        pending[terrain] = struct.pack('<I3721f',60,*heights)
        if (tx,ty) in grouped:
            key = f'{tx}_{ty}'
            oid = existing.get(key)
            if oid is None:
                oid = nextid; nextid += 1
                data += ['', '[object]', '0', f'Sceneryobjects\\HK_TsingYi\\road_join_{key}.sco',
                         str(oid), '0', '0', '0', '0', '0', '0', '0', '']
            ids[key] = oid
            pending[path] = ('\r\n'.join(data)+'\r\n').encode('utf-16')
            pending[objects/f'model/road_join_{key}.x'] = mesh_text(grouped[tx,ty],tx,ty).encode('ascii')
            pending[objects/f'road_join_{key}.sco'] = ('\r\n'.join([
                '[friendlyname]', f'Tsing Yi road joins {key}', '[groups]', '2', 'Hong Kong', 'Tsing Yi',
                '[rendertype]', 'surface', '[fixed]', '[absheight]', '[surface]',
                '[collision_mesh]', f'model\\road_join_{key}.x', '[mesh]', f'model\\road_join_{key}.x', ''])).encode('ascii')
    report = dict(road_pieces=len(roads), uncovered_join_polygons=len(patches), surface_tiles=len(grouped),
                  terrain_cells_constrained=len(cells), terrain_vertices_lowered=changed_vertices,
                  road_clearance_metres=.25, terrain_cap_failures=failures,
                  runtime_tested=False, surface_object_ids=ids)
    if failures:
        raise ValueError(f'Terrain cap serialization failed: {failures}')
    if audit_only:
        return report
    cfg = re.sub(r'(\[NextIDCode\]\s*\n)\d+', lambda m:m[1]+str(nextid), cfg)
    pending[folder/'global.cfg'] = (cfg.replace('\r\n','\n').replace('\n','\r\n')).encode('utf-16')
    pending[objects/'texture/asphalt.bmp'] = (root/'Splines/HK_TsingYi/texture/asphalt.bmp').read_bytes()
    manifest['road_contact_repair'] = report
    pending[folder/'build_manifest.json'] = (json.dumps(manifest,indent=2)+'\n').encode('utf-8')
    preview_path = folder/'preview_data.json'
    if preview_path.exists():
        preview = json.loads(preview_path.read_text(encoding='utf-8')); preview['manifest'] = manifest
        pending[preview_path] = json.dumps(preview,ensure_ascii=False).encode('utf-8')
    backup = root/'work'/('road-contact-backup-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
    changed = 0
    for path, content in pending.items():
        if path.exists() and path.read_bytes() == content:
            continue
        if path.exists():
            dest = backup/path.relative_to(root); dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(path,dest)
        path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(content); changed += 1
    return dict(report,files_updated=changed,backup=str(backup))


def install(root, game):
    """Copy only the three dedicated project directories, preserving overwritten files."""
    game = game.resolve()
    if not (game/'maps/HK_TsingYi/global.cfg').is_file():
        raise ValueError(f'Existing installed map required: {game}')
    if game == root.resolve():
        raise ValueError('Installation target must differ from the authoring root')
    backup = root/'work'/('road-install-backup-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
    copied = 0
    for category in ('maps','Splines','Sceneryobjects'):
        for source in sorted((root/category/'HK_TsingYi').rglob('*')):
            if not source.is_file():
                continue
            relative = source.relative_to(root); dest = game/relative
            if dest.exists() and hashlib.sha256(dest.read_bytes()).digest() == hashlib.sha256(source.read_bytes()).digest():
                continue
            if dest.exists():
                saved = backup/relative; saved.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(dest,saved)
            dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,dest); copied += 1
    return dict(target=str(game),files_updated=copied,backup=str(backup))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--audit-only',action='store_true')
    parser.add_argument('--install',type=Path,action='append',default=[])
    args = parser.parse_args(); result = repair(args.root,args.audit_only)
    if not args.audit_only:
        result['installations'] = [install(args.root,g) for g in args.install]
    print(json.dumps(result,indent=2))
