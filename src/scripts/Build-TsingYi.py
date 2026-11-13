#!/usr/bin/env python3
"""Build an isolated 1:1 Tsing Yi OMSI 2 development map from OSM and Skadi DEM.

No third-party OMSI meshes or textures are copied. Assets are authored here.
The output is a free-drive foundation, not a completed scheduled-service map.
Run with --help. Requires requirements-tsingyi.txt; no network access at build time.
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import shutil
import struct
import tempfile
import heapq
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import osmium

WEST, SOUTH, EAST, NORTH = 114.074, 22.315, 114.119, 22.368
LAT0 = (SOUTH + NORTH) / 2
MX = 111320 * math.cos(math.radians(LAT0))
MY = 110574.
TILE = 300.
ASSET = 'HK_TsingYi'
ROAD_TYPES = {
    'motorway': 10.2, 'motorway_link': 7., 'trunk': 10.2, 'trunk_link': 7.,
    'primary': 10.2, 'primary_link': 7., 'secondary': 7., 'secondary_link': 7.,
    'tertiary': 7., 'tertiary_link': 7., 'residential': 6., 'unclassified': 6.,
    'living_street': 4.5, 'service': 4.5,
}


def project(lat, lon):
    return (lon - WEST) * MX + 300., (lat - SOUTH) * MY + 300.


def unproject(x, y):
    return SOUTH + (y - 300.) / MY, WEST + (x - 300.) / MX


def inside_bounds(lat, lon):
    return SOUTH <= lat <= NORTH and WEST <= lon <= EAST


def in_polygon(x, y, polygon):
    hit = False
    ax, ay = polygon[-1]
    for bx, by in polygon:
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
            hit = not hit
        ax, ay = bx, by
    return hit


def text(path, lines, encoding='ascii'):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(('\r\n'.join(map(str, lines)) + '\r\n').encode(encoding, errors='replace'))


def mesh(path, vertices, triangles, texture=None):
    """Native DirectX text mesh, avoiding undocumented binary O3D assumptions."""
    if not vertices or not triangles:
        raise ValueError('Empty mesh')
    # OMSI's stock .x assets transform authored Z-up coordinates into DirectX
    # Y-up coordinates at the root frame. Keep the same native convention.
    lines = ['xof 0303txt 0032', 'Frame RootFrame {', 'FrameTransformMatrix {',
             '1,0,0,0, 0,0,1,0, 0,1,0,0, 0,0,0,1;;', '}', 'Mesh {', f'{len(vertices)};']
    lines += [f'{v[0]:.5f};{v[1]:.5f};{v[2]:.5f};' + (',' if i < len(vertices)-1 else ';')
              for i, v in enumerate(vertices)]
    lines += [f'{len(triangles)};']
    lines += [f'3;{a},{b},{c};' + (',' if i < len(triangles)-1 else ';')
              for i, (a, b, c) in enumerate(triangles)]
    # .x is left-handed; reverse winding is supplied by callers for outward faces.
    if texture:
        lines += ['MeshTextureCoords {', f'{len(vertices)};']
        lines += [f'{v[6] if len(v)>6 else v[0]/8:.5f};{v[7] if len(v)>7 else v[1]/8:.5f};' +
                  (',' if i < len(vertices)-1 else ';') for i,v in enumerate(vertices)]
        lines += ['}', 'MeshMaterialList {', '1;', f'{len(triangles)};',
                  ','.join('0' for _ in triangles) + ';;', 'Material {',
                  '1.0;1.0;1.0;1.0;;', '0.0;', '0.0;0.0;0.0;;', '0.0;0.0;0.0;;',
                  'TextureFilename {', f'"{texture}";', '}', '}', '}']
    lines += ['}', '}']
    text(path, lines)


class Source(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.roads=[]; self.buildings=[]; self.stops={}; self.coasts=[]; self.routes=[]

    def node(self, node):
        if not node.location.valid() or not inside_bounds(node.lat, node.lon):
            return
        if node.tags.get('highway') == 'bus_stop':
            self.stops[node.id] = {'osm_id':node.id, 'lat':node.lat, 'lon':node.lon, 'tags':dict(node.tags)}

    def way(self, way):
        tags = dict(way.tags)
        relevant = tags.get('highway') in ROAD_TYPES or 'building' in tags or tags.get('natural') == 'coastline'
        if not relevant or not all(n.location.valid() for n in way.nodes):
            return
        points = [(n.lat, n.lon) for n in way.nodes]
        if tags.get('natural') == 'coastline':
            self.coasts.append([(n.ref, *project(n.lat,n.lon)) for n in way.nodes])
        if not any(inside_bounds(*p) for p in points):
            return
        item = {'id':way.id,'tags':tags,'points':[project(*p) for p in points],
                'nodes':[n.ref for n in way.nodes]}
        if tags.get('highway') in ROAD_TYPES:
            self.roads.append(item)
        if 'building' in tags and tags['building'] not in ('no','construction'):
            self.buildings.append(item)

    def relation(self, relation):
        if relation.tags.get('route') == 'bus' and relation.tags.get('ref') in ('248M','249M'):
            self.routes.append({'osm_id':relation.id, 'tags':dict(relation.tags),
                                'members':[(m.type,m.ref,m.role) for m in relation.members]})


def island_ring(chains):
    """Join directed OSM coastline ways; select the closed Tsing Yi island ring."""
    remaining = {i:chain for i,chain in enumerate(chains) if len(chain)>1}
    starts = defaultdict(list)
    for i,chain in remaining.items():
        starts[chain[0][0]].append(i)
    rings=[]
    while remaining:
        _, chain = remaining.popitem()
        chain = list(chain)
        while chain[-1][0] != chain[0][0]:
            matches=[i for i in starts.get(chain[-1][0],[]) if i in remaining]
            if not matches:
                break
            chain.extend(remaining.pop(matches[0])[1:])
        if chain[-1][0] == chain[0][0]:
            rings.append([(p[1],p[2]) for p in chain])
    centre=project(22.345,114.100)
    matches=[p for p in rings if in_polygon(*centre,p)]
    if not matches:
        raise RuntimeError('A complete Tsing Yi coastline ring is required; source may be incomplete')
    return max(matches,key=len)


class DEM:
    def __init__(self,path):
        with gzip.open(path,'rb') as f:
            self.data=f.read()
        self.n=math.isqrt(len(self.data)//2)
        if self.n*self.n*2 != len(self.data) or self.n not in (1201,3601):
            raise ValueError('Expected a 1 or 3 arcsecond HGT tile')

    def at(self,x,y):
        lat,lon=unproject(x,y)
        fx=max(0.,min(self.n-1.000001,(lon-114)*(self.n-1)))
        fy=max(0.,min(self.n-1.000001,(23-lat)*(self.n-1)))
        ix,iy=int(fx),int(fy); u,v=fx-ix,fy-iy
        values=[struct.unpack_from('>h',self.data,2*(row*self.n+col))[0]
                for row,col in ((iy,ix),(iy,ix+1),(iy+1,ix),(iy+1,ix+1))]
        if min(values) <= -32768:
            raise ValueError('DEM void in build area')
        return max(0.,(values[0]*(1-u)+values[1]*u)*(1-v)+(values[2]*(1-u)+values[3]*u)*v)


def road_profile(tags):
    try:
        lanes=max(0,min(8,int(tags.get('lanes','0'))))
    except ValueError:
        lanes=0
    oneway=tags.get('oneway') in ('yes','1','true','-1') or tags.get('junction') == 'roundabout'
    if not lanes:
        lanes=max(1,round(ROAD_TYPES[tags['highway']]/3.25))
        if oneway and tags['highway'] in ('service','residential'):
            lanes=1
    try:
        width=float(tags.get('width','').replace(' m',''))
    except ValueError:
        width=lanes*3.25+0.5
    width=round(max(3.5,min(30.,width)),1)
    forward=lanes if oneway else (lanes+1)//2
    try:
        if not oneway:
            forward=max(1,min(lanes-1,int(tags.get('lanes:forward',forward))))
    except ValueError:
        pass
    return width,lanes,forward,oneway


def spline_file(path,width,lanes,forward,oneway):
    half=width/2
    lines=['[heightprofile]',-half,half,'0.08','0.08','', '[texture]','asphalt.bmp','',
           '[profile]',0,'[profilepnt]',-half,'0.08',0,'0.125',
           '[profilepnt]',half,'0.08',1,'0.125','']
    lane_width=width/lanes
    for lane in range(lanes):
        # Along a forward OSM way the left side is negative spline x.
        direction=0 if oneway or lane<forward else 1
        lines += ['[path]',0,f'{-half+(lane+.5)*lane_width:.4f}','0.08',f'{lane_width:.4f}',direction,'']
    text(path,lines)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--inputs',type=Path,help='Folder with hong-kong-latest.osm.pbf and N22E114.hgt.gz')
    args=parser.parse_args()
    root=args.root.resolve(); inputs=(args.inputs or root/'work'/'tsingyi-inputs').resolve()
    source_path=inputs/'hong-kong-latest.osm.pbf'; dem_path=inputs/'N22E114.hgt.gz'
    for path in (source_path,dem_path):
        if not path.is_file():
            parser.error(f'Missing {path}; run Fetch-TsingYi.py first')
    spec=importlib.util.spec_from_file_location('geometry',Path(__file__).with_name('Convert-OsmToMap.py'))
    geometry=importlib.util.module_from_spec(spec); spec.loader.exec_module(geometry)
    print('Reading territory-wide OSM source ...',flush=True)
    source=Source(); source.apply_file(str(source_path),locations=True,idx='flex_mem')
    coast=island_ring(source.coasts); dem=DEM(dem_path)
    print(f'Tsing Yi coast: {len(coast)} points; {len(source.roads)} candidate road ways',flush=True)
    work=root/'work'; work.mkdir(exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='tsingyi-build-',dir=work))
    mapdir=stage/'maps'/ASSET; objects=stage/'Sceneryobjects'/ASSET
    models=objects/'model'; textures=objects/'texture'; splines=stage/'Splines'/ASSET
    for p in (mapdir/'TTData',models,textures,splines/'texture'):
        p.mkdir(parents=True,exist_ok=True)
    geometry.write_bmp(splines/'texture'/'asphalt.bmp',128,128,
                       lambda x,y:(75+(x*17+y*13)%15,76+(x*17+y*13)%15,77+(x*17+y*13)%15))
    geometry.write_bmp(textures/'grass.bmp',128,128,lambda x,y:(48+(x*7+y*13)%20,77+(x*7+y*13)%24,38+(x*7+y*13)%16))
    geometry.write_bmp(textures/'grass_detail.bmp',64,64,lambda x,y:(100+(x*11+y*17)%25,110+(x*11+y*17)%25,95+(x*11+y*17)%25))
    # Seed the existing procedural texture helper consistently across Python processes.
    for name in ('residential','glass','retail','concrete'):
        def facade(x,y,kind=name):
            noise=(x*37+y*19)%13-6
            window=6<x%24<19 and 6<y%24<20
            if kind=='glass':
                return (64+noise,91+noise,110+noise) if window else (150,156,160)
            if kind=='concrete': return (155+noise,155+noise,151+noise)
            if window: return (60+noise,74+noise,87+noise)
            return (196+noise,187+noise,172+noise)
        geometry.write_bmp(textures/f'facade_{name}.bmp',128,128,facade)
    tiles={}; nextid=1; road_segments=[]; profiles={}; diagnostics=[]
    # Include hills and sea between roads, not just cells with placed objects.
    xmax,ymax=project(NORTH,EAST)
    for tx in range(1,math.ceil(xmax/TILE)):
        for ty in range(1,math.ceil(ymax/TILE)):
            tiles[(tx,ty)]={'roads':[],'objects':[],'buildings':defaultdict(list)}
    def tile_for(x,y):
        key=(math.floor(x/TILE),math.floor(y/TILE))
        return key,tiles.setdefault(key,{'roads':[],'objects':[],'buildings':defaultdict(list)})
    def object_at(x,y,z,file,labels=(),heading=0.):
        nonlocal nextid
        key,tile=tile_for(x,y); oid=nextid; nextid+=1
        tile['objects'].append({'id':oid,'file':file,'x':x-key[0]*TILE,'y':y-key[1]*TILE,
                                'z':z,'labels':list(labels),'heading':heading})
        return oid,key
    def ground(x,y):
        return dem.at(x,y) if in_polygon(x,y,coast) else -2.
    # Coastal polygon edges are indexed per 300m cell, avoiding a full polygon scan
    # for every DEM vertex. This preserves the same classification at tile borders.
    coast_rows={}
    def land_row(y):
        key=round(y,6)
        if key not in coast_rows:
            intersections=[]
            ax,ay=coast[-1]
            for bx,by in coast:
                if (ay>y)!=(by>y):
                    intersections.append((bx-ax)*(y-ay)/(by-ay)+ax)
                ax,ay=bx,by
            coast_rows[key]=sorted(intersections)
        return coast_rows[key]
    import bisect
    def terrain_height(x,y):
        land=bisect.bisect_right(land_row(y),x)%2 == 1
        return dem.at(x,y) if land else -2.

    # Surface DEMs include roofs and vegetation rather than surveyed road
    # grades. Average upper/lower 8.5% Lipschitz envelopes on the road graph
    # to smooth heights while preserving common elevations at shared nodes.
    graph=defaultdict(list); initial={}; bridge_nodes=set()
    for way in source.roads:
        tags=way['tags']
        if tags.get('tunnel') not in (None,'no'): continue
        if tags.get('access') in ('no','private') and tags.get('bus') not in ('yes','designated'): continue
        for (ax,ay),(bx,by) in zip(way['points'],way['points'][1:]):
            if not inside_bounds(*unproject((ax+bx)/2,(ay+by)/2)): continue
            if not in_polygon((ax+bx)/2,(ay+by)/2,coast) and tags.get('bridge') in (None,'no'): continue
            a=(round(ax,6),round(ay,6)); b=(round(bx,6),round(by,6))
            distance=math.dist(a,b)
            if distance<.01: continue
            graph[a].append((b,distance*.085)); graph[b].append((a,distance*.085))
            if tags.get('bridge') not in (None,'no'): bridge_nodes.update((a,b))
    for x,y in graph:
        initial[(x,y)]=statistics.median(dem.at(x+dx,y+dy) for dx in (-25.,0.,25.) for dy in (-25.,0.,25.))+.12
        if (x,y) in bridge_nodes: initial[(x,y)]=max(initial[(x,y)]+3.,12.)
    def envelope(sign):
        distances={p:sign*z for p,z in initial.items()}
        queue=[(z,p) for p,z in distances.items()]; heapq.heapify(queue)
        while queue:
            z,p=heapq.heappop(queue)
            if z>distances[p]: continue
            for q,cost in graph[p]:
                candidate=z+cost
                if candidate<distances[q]:
                    distances[q]=candidate; heapq.heappush(queue,(candidate,q))
        return distances
    upper=envelope(1); lower=envelope(-1)
    road_heights={p:(upper[p]-lower[p])/2 for p in initial}

    # Native road splines are linked only within their real OSM way, including
    # across tile boundaries. Unrelated streets never receive arbitrary links.
    retained_ways=set(); elevated=0; tunnel_count=0
    for way in sorted(source.roads,key=lambda w:w['id']):
        tags=way['tags']; pts=way['points']
        if tags.get('access') in ('no','private') and tags.get('bus') not in ('yes','designated'):
            continue
        if tags.get('oneway') == '-1':
            pts=list(reversed(pts))
        width,lanes,forward,oneway=road_profile(tags)
        profile=(width,lanes,forward,oneway)
        name=f'road_{width:.1f}_{lanes}_{forward}_{int(oneway)}.sli'
        profiles[name]=profile
        segments=[]
        is_bridge=tags.get('bridge') not in (None,'no')
        is_tunnel=tags.get('tunnel') not in (None,'no')
        if is_tunnel:
            tunnel_count+=1
            # No open cut or tunnel portals are authored in this foundation.
            # Retain its alignment in the review data, not as a road buried in terrain.
            diagnostics.append({'osm_way':way['id'],'issue':'tunnel_not_generated','name':tags.get('name:en',tags.get('name',''))})
            continue
        # Bridge decks need surveyed profiles. An estimated level is explicitly
        # recorded; it cannot be mistaken for DEM-derived bridge geometry.
        for (ax,ay),(bx,by) in zip(pts,pts[1:]):
            mid=((ax+bx)/2,(ay+by)/2)
            if not in_polygon(*mid,coast) and not is_bridge:
                continue
            if not inside_bounds(*unproject(*mid)):
                continue
            for tx in range(math.floor(min(ax,bx)/TILE),math.floor(max(ax,bx)/TILE)+1):
                for ty in range(math.floor(min(ay,by)/TILE),math.floor(max(ay,by)/TILE)+1):
                    seg=geometry.clip_segment((ax-tx*TILE,ay-ty*TILE),(bx-tx*TILE,by-ty*TILE),0.,TILE)
                    if seg is None: continue
                    (x0,y0),(x1,y1)=seg; length=math.hypot(x1-x0,y1-y0)
                    if length<.15: continue
                    gx,gy=tx*TILE+x0,ty*TILE+y0
                    za=road_heights[(round(ax,6),round(ay,6))]
                    zb=road_heights[(round(bx,6),round(by,6))]
                    original_length=math.hypot(bx-ax,by-ay)
                    t0=math.hypot(gx-ax,gy-ay)/original_length
                    t1=math.hypot(tx*TILE+x1-ax,ty*TILE+y1-ay)/original_length
                    z0=za+(zb-za)*t0; z1=za+(zb-za)*t1
                    road={'id':nextid,'prev':0,'next':0,'file':f'Splines\\{ASSET}\\{name}',
                          'x':x0,'y':y0,'z':z0,'heading':math.degrees(math.atan2(x1-x0,y1-y0))%360,
                          'length':length,'grade':(z1-z0)/length*100,'tile':(tx,ty),'end':(tx*TILE+x1,ty*TILE+y1),
                          'start':(gx,gy),'osm_way':way['id'],'name':tags.get('name:en',tags.get('name','')),
                          'bridge':is_bridge,'width':width,'z1':z1}
                    nextid+=1
                    _,tile=tile_for(gx+(x1-x0)/2,gy+(y1-y0)/2)
                    tile['roads'].append(road); segments.append(road); road_segments.append(road)
                    retained_ways.add(way['id'])
        for before,after in zip(segments,segments[1:]):
            if math.dist(before['end'],after['start'])<.02:
                before['next']=after['id']; after['prev']=before['id']
        if is_bridge and segments:
            elevated+=1
            diagnostics.append({'osm_way':way['id'],'issue':'bridge_height_estimated','name':tags.get('name:en',tags.get('name',''))})
    for name,profile in profiles.items():
        spline_file(splines/name,*profile)
    print(f'Roads: {len(road_segments)} segments from {len(retained_ways)} ways',flush=True)
    if not road_segments: raise RuntimeError('No roads generated')
    # Fit terrain to each ground-level carriageway, fading over a 4 m verge.
    # Leave land/seabed below bridges at its original elevation.
    road_cells=defaultdict(list)
    for r in road_segments:
        if r['bridge']: continue
        radius=r['width']/2+4.
        for cx in range(math.floor((min(r['start'][0],r['end'][0])-radius)/50),math.floor((max(r['start'][0],r['end'][0])+radius)/50)+1):
            for cy in range(math.floor((min(r['start'][1],r['end'][1])-radius)/50),math.floor((max(r['start'][1],r['end'][1])+radius)/50)+1):
                road_cells[(cx,cy)].append(r)
    def road_surface(x,y):
        best=None
        for r in road_cells.get((math.floor(x/50),math.floor(y/50)),()):
            ax,ay=r['start']; bx,by=r['end']; dx=bx-ax; dy=by-ay
            t=max(0.,min(1.,((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy)))
            distance=math.hypot(x-ax-t*dx,y-ay-t*dy)
            edge=max(0.,distance-r['width']/2)
            if edge<4. and (best is None or distance<best[0]):
                best=(distance,edge,r['z']+(r['z1']-r['z'])*t)
        return best
    unmodified_terrain=terrain_height
    def terrain_height(x,y):
        raw=unmodified_terrain(x,y); hit=road_surface(x,y)
        if hit:
            blend=1.-hit[1]/4.
            return raw*(1.-blend)+(hit[2]-.08)*blend
        return raw

    # Buildings may cross tile edges; retaining the complete footprint avoids
    # deleting every building that happens to straddle an artificial tile grid.
    building_count=0
    for building in source.buildings:
        pts=building['points']; cx=sum(p[0] for p in pts)/len(pts); cy=sum(p[1] for p in pts)/len(pts)
        if not in_polygon(cx,cy,coast) or geometry.polygon_area(pts)<9: continue
        tags=building['tags']; height=10.
        try:
            height=float(tags['height'].replace(' m','')) if 'height' in tags else float(tags.get('building:levels',3))*3.2
        except ValueError: pass
        height=max(3.,min(500.,height)); key,tile=tile_for(cx,cy)
        local=[(x-key[0]*TILE,y-key[1]*TILE) for x,y in pts]
        vertices,triangles=geometry.building_footprint_mesh(local,height)
        if not triangles: continue
        z=min(dem.at(x,y) for x,y in pts)
        vertices=[(v[0],v[1],v[2]+z,*v[3:]) for v in vertices]
        _,texture=geometry.BUILDING_MATERIALS.get(tags.get('building'),geometry.DEFAULT_BUILDING_MATERIAL)
        tile['buildings'][texture].append((vertices,triangles))
        building_count+=1
    for key,tile in list(tiles.items()):
        sco=['[friendlyname]',f'Tsing Yi buildings {key[0]} {key[1]}','[groups]',2,'Hong Kong','Tsing Yi']
        for i,(texture,parts) in enumerate(sorted(tile['buildings'].items())):
            vertices=[]; triangles=[]
            for verts,tris in parts:
                offset=len(vertices); vertices.extend(verts)
                triangles.extend((a+offset,c+offset,b+offset) for a,b,c in tris)
            filename=f'buildings_{key[0]}_{key[1]}_{i}.x'
            mesh(models/filename,vertices,triangles,texture)
            sco+=['[mesh]',f'model\\{filename}','[collision_mesh]',f'model\\{filename}']
        if tile['buildings']:
            filename=f'buildings_{key[0]}_{key[1]}.sco'; text(objects/filename,sco)
            object_at(key[0]*TILE+.001,key[1]*TILE+.001,0,f'Sceneryobjects\\{ASSET}\\{filename}')
            tile['objects'][-1]['x']=tile['objects'][-1]['y']=0.

    # A visible custom pole is also a native bus-stop object. Use English names
    # in legacy ANSI TTData; preserve original Chinese names in UTF-8 source data.
    verts,tris,_=geometry.building_box_mesh(.12,.12,2.8)
    sign_v,sign_t,_=geometry.building_box_mesh(.5,.12,.6)
    offset=len(verts); verts += [(x,y,z+2.2) for x,y,z in sign_v]
    tris += [(a+offset,b+offset,c+offset) for a,b,c in sign_t]
    mesh(models/'bus_stop.x',verts,[(a,c,b) for a,b,c in tris])
    text(objects/'bus_stop.sco',['[friendlyname]','Tsing Yi Bus Stop','[groups]',2,'Hong Kong','Tsing Yi',
                               '[busstop]','[mesh]','model\\bus_stop.x'])
    stop_records=[]; stop_ids={}
    for sid,stop in sorted(source.stops.items()):
        x,y=project(stop['lat'],stop['lon'])
        if not in_polygon(x,y,coast): continue
        name=stop['tags'].get('name:en') or stop['tags'].get('ref') or f'Tsing Yi stop {sid}'
        name=name.encode('ascii','replace').decode()
        surface=road_surface(x,y)
        z=surface[2] if surface else terrain_height(x,y)
        oid,key=object_at(x,y,z,f'Sceneryobjects\\{ASSET}\\bus_stop.sco',[name,'30','0','0'])
        stop_ids[sid]=oid; stop_records.append({**stop,'name':name,'object_id':oid,'tile':key})

    # Place spawn points on actual road centre lines near useful local landmarks.
    # Full vehicle-width clearance remains an editor/in-game check.
    mesh(models/'spawn.x',[(0,0,0),(.01,0,0),(0,.01,0)],[(0,2,1)])
    text(objects/'spawn.sco',['[friendlyname]','Tsing Yi Entry Point','[groups]',2,'Hong Kong','Tsing Yi',
                            '[entrypoint]','[onlyeditor]','[mesh]','model\\spawn.x'])
    entries=[]
    landmarks=[('Tsing Yi Station',22.3586,114.1074),('Cheung On',22.3616,114.1035),
               ('Cheung Hong',22.3501,114.0996),('Tsing Yi Estate',22.3477,114.1053),
               ('Tsing Yi South',22.335,114.107),('Tsing Yi West',22.349,114.084)]
    candidates=[r for r in road_segments if not r['bridge'] and r['length']>=12 and r['width']>=6 and abs(r['grade'])<12]
    for name,lat,lon in landmarks:
        px,py=project(lat,lon)
        road=min(candidates,key=lambda r:math.dist((px,py),r['start']))
        x=(road['start'][0]+road['end'][0])/2; y=(road['start'][1]+road['end'][1])/2
        z=(road['z']+road['z1'])/2+.15
        oid,key=object_at(x,y,z,f'Sceneryobjects\\{ASSET}\\spawn.sco',[name],road['heading'])
        entries.append((name,oid,key,road['heading']))

    # Ocean is an explicit horizontal mesh. Seabed terrain is below it, using
    # the actual OSM coastline rather than turning the whole rectangle into grass.
    for key,tile in list(tiles.items()):
        filename=f'water_{key[0]}_{key[1]}.x'
        mesh(models/filename,[(0,0,-.4),(TILE,0,-.4),(TILE,TILE,-.4),(0,TILE,-.4)],[(0,2,1),(0,3,2)])
        # A project-authored blue material; no water simulation is claimed.
        p=models/filename
        data=p.read_text(); data=data.replace('\r','')
        # Insert a material inside Mesh, retaining the root transform frame.
        data=data.rsplit('}',2)[0]+'MeshMaterialList {\n1;\n2;\n0,0;;\nMaterial {\n0.08;0.29;0.39;1.0;;\n16.0;\n0.15;0.15;0.15;;\n0.0;0.0;0.0;;\n}\n}\n}\n}\n'
        p.write_text(data,encoding='ascii')
        sco=f'water_{key[0]}_{key[1]}.sco'
        text(objects/sco,['[friendlyname]','Tsing Yi Water','[groups]',2,'Hong Kong','Tsing Yi',
                          '[nocollision]','[mesh]',f'model\\{filename}'])
        object_at(key[0]*TILE+.001,key[1]*TILE+.001,0,f'Sceneryobjects\\{ASSET}\\{sco}')
        tile['objects'][-1]['x']=tile['objects'][-1]['y']=0.
    order=sorted(tiles); indices={key:i for i,key in enumerate(order)}
    print(f'Writing {len(order)} tiles, {building_count} buildings, {len(stop_records)} stops ...',flush=True)
    for key in order:
        tile=tiles[key]; lines=['[version]',14,'[terrain]','','[variable_terrain]','']
        for r in tile['roads']:
            # Matches stock OMSI v14 [spline] field count: final value is texture
            # offset, not delta-height. Height comes from the two grade fields.
            lines+=['[spline]',0,r['file'],r['id'],r['prev'],r['next'],
                    f"{r['x']:.6f}",f"{r['z']:.6f}",f"{r['y']:.6f}",f"{r['heading']:.6f}",
                    f"{r['length']:.6f}",0,f"{r['grade']:.6f}",f"{r['grade']:.6f}",0,0,0,0,0,'']
        for o in tile['objects']:
            lines+=['[object]',0,o['file'],o['id'],f"{o['x']:.5f}",f"{o['y']:.5f}",f"{o['z']:.5f}",
                    f"{o['heading']:.6f}",0,0,len(o['labels']),*o['labels'],'']
        text(mapdir/f'tile_{key[0]}_{key[1]}.map',lines,'utf-16')
        heights=[terrain_height(key[0]*TILE+i*5.,key[1]*TILE+j*5.) for j in range(61) for i in range(61)]
        (mapdir/f'tile_{key[0]}_{key[1]}.map.terrain').write_bytes(struct.pack('<I3721f',60,*heights))
    gl=['[name]',ASSET,'[friendlyname]','Tsing Yi 1:1 - development','[description]',
        'Real OSM road and building foundation. Free-drive development map; see TSING_YI.md.','[end]',
        '[version]',14,'[NextIDCode]',nextid,'[LHT]',
        '[moneysystem]','Money\\DM\\DM.cfg','[ticketpack]','TicketPacks\\Berlin_1\\Berlin_1.otp',
        '[years]',1988,2099,'[standarddepot]','Tsing Yi Test','[groundtex]',
        f'Sceneryobjects\\{ASSET}\\texture\\grass.bmp',f'Sceneryobjects\\{ASSET}\\texture\\grass_detail.bmp',0,1,60,
        '[entrypoints]',len(entries)]
    for name,oid,key,heading in entries:
        tile=tiles[key]; index=next(i for i,o in enumerate(tile['objects']) if o['id']==oid); obj=tile['objects'][index]
        angle=math.radians(heading)/2
        gl += [index,oid,0,f"{obj['x']:.5f}",f"{obj['z']:.5f}",f"{obj['y']:.5f}",
               0,f'{math.sin(angle):.6f}',0,f'{math.cos(angle):.6f}',indices[key],name]
    spawn_id=entries[0][1]; spawn_key=entries[0][2]
    spawn_obj=next(o for o in tiles[spawn_key]['objects'] if o['id']==spawn_id)
    gl+=['[mapcam]',spawn_key[0],spawn_key[1],spawn_obj['x'],spawn_obj['z']+12,
         spawn_obj['y'],spawn_obj['heading'],-25,80]
    for tx,ty in order: gl+=['[map]',tx,ty,f'tile_{tx}_{ty}.map']
    text(mapdir/'global.cfg',gl,'utf-16')
    text(mapdir/'drivers.txt',['humans\\axyz\\man01.hum'])
    text(mapdir/'ailists.cfg',['[aigroup_2]','NormalCars','','[end]'])
    busstops=['Time Table BusStopList File','']
    for st in stop_records:
        busstops+=['[busstop]',st['name'],indices[st['tile']],st['object_id'],'30.0',0,0,'']
    text(mapdir/'TTData'/'Busstops.cfg',busstops)
    # Publish exact OSM route memberships as authoring references. Do not create
    # plausible-looking .ttl/.ttp service schedules without road-track validation.
    route_refs=[]
    for r in source.routes:
        members=[{'osm_node':ref,'role':role,'map_object':stop_ids.get(ref)}
                 for typ,ref,role in r['members'] if typ=='n' and role.startswith(('stop','platform'))]
        route_refs.append({'osm_relation':r['osm_id'],'tags':r['tags'],'stop_members':members,
                           'all_stops_present':bool(members) and all(s['map_object'] for s in members),
                           'runtime_service_ready':False})
    (mapdir/'route_references.json').write_text(json.dumps(route_refs,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (mapdir/'bus_stops.json').write_text(json.dumps(stop_records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (mapdir/'authoring_issues.json').write_text(json.dumps(diagnostics,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    manifest={'generator':'Build-TsingYi.py','map':ASSET,'status':'development_free_drive_foundation',
              'bounds_wgs84':[WEST,SOUTH,EAST,NORTH],'tile_size_metres':TILE,'tiles':len(order),
              'road_ways':len(retained_ways),'road_splines':len(road_segments),'buildings':building_count,
              'bus_stops':len(stop_records),'entrypoints':len(entries),'estimated_bridge_ways':elevated,
              'omitted_tunnel_ways':tunnel_count,'dem_grid_samples_per_degree':dem.n-1,
              'maximum_engineered_road_grade_percent':8.5,
              'source_sha256':{p.name:hashlib.file_digest(p.open('rb'),'sha256').hexdigest() for p in (source_path,dem_path)},
              'limitations':['No authored junction AI connectors or signal control','Bridge deck elevations are estimated',
                             'Tunnel roads omitted until portals and terrain cuts are authored',
                             'No scheduled passenger routes; OSM 248M/249M references supplied',
                             'Road profiles are engineered from DEM with an 8.5% cap, not surveyed elevations',
                             'Generic building extrusions; OSM multipolygon buildings not imported',
                             'Runtime driving and performance validation pending']}
    (mapdir/'build_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    # Compact geographic review data, also used by the standalone local viewer.
    preview={'coast':coast,'roads':[{'start':r['start'],'end':r['end'],'bridge':r['bridge'],'name':r['name']} for r in road_segments],
             'stops':[{'x':project(s['lat'],s['lon'])[0],'y':project(s['lat'],s['lon'])[1],'name':s['name']} for s in stop_records],
             'manifest':manifest}
    (mapdir/'preview_data.json').write_text(json.dumps(preview,ensure_ascii=False),encoding='utf-8')
    # Replace only the three dedicated generated folders. Preserve the previous
    # build under work/ instead of deleting it or touching any prototype map.
    backup=work/('tsingyi-previous-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
    for category in ('maps','Sceneryobjects','Splines'):
        target=root/category/ASSET
        if target.exists():
            (backup/category).mkdir(parents=True,exist_ok=True)
            shutil.move(str(target),str(backup/category/ASSET))
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.move(str(stage/category/ASSET),str(target))
    print(json.dumps(manifest,indent=2),flush=True)


if __name__ == '__main__':
    main()
