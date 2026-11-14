#!/usr/bin/env python3
"""Validate generated Tsing Yi references, native records, and terrain continuity.

This is an offline structural check; it does not certify runtime drivability.
"""
import argparse
import importlib.util
import json
import math
import re
import struct
from collections import Counter
from pathlib import Path


def read(path):
    raw=path.read_bytes()
    return raw.decode('utf-16' if raw[:2] in (b'\xff\xfe',b'\xfe\xff') else 'ascii').replace('\r\n','\n')


def validate(root):
    root=Path(root); folder=root/'maps'/'HK_TsingYi'
    errors=[]; cfg=read(folder/'global.cfg'); lines=cfg.splitlines()
    entries=[(int(x),int(y),name) for x,y,name in re.findall(r'\[map\]\n(-?\d+)\n(-?\d+)\n([^\n]+)',cfg)]
    if not entries or len(entries)!=len(set((x,y) for x,y,_ in entries)):
        errors.append('Missing or duplicate global tile records')
    ids={}; splines={}; terrains={}; refs=set(); tile_objects=[]; steep=0; max_grade=0.
    for ti,(tx,ty,name) in enumerate(entries):
        p=folder/name
        if not p.exists():
            errors.append(f'Missing tile {name}'); continue
        data=read(p).splitlines(); objects=[]; i=0
        while i<len(data):
            kind=data[i].strip()
            try:
                if kind=='[spline]':
                    record=data[i+1:i+19]
                    if len(record)!=18 or record[-1]=='':
                        raise ValueError('Spline must match the 18-field stock OMSI v14 format')
                    oid=int(record[2]); refs.add(record[1])
                    numbers=[float(v) for j,v in enumerate(record) if j!=1]
                    if not all(math.isfinite(v) for v in numbers): raise ValueError('Non-finite spline')
                    if float(record[9])<=0: raise ValueError('Non-positive spline length')
                    # fields: kind, file, id, prev, next, x,z,y,heading,length,
                    # radius,grad0,grad1,cant0,cant1,skew0,skew1,texture_offset
                    start=(tx*300+float(record[5]),ty*300+float(record[7]),float(record[6]))
                    angle=math.radians(float(record[8])); length=float(record[9]); grade=float(record[11])
                    max_grade=max(max_grade,abs(grade))
                    end=(start[0]+math.sin(angle)*length,start[1]+math.cos(angle)*length,start[2]+length*grade/100)
                    splines[oid]={'prev':int(record[3]),'next':int(record[4]),'start':start,'end':end}
                    if abs(grade)>15: steep+=1
                    i+=19
                elif kind=='[object]':
                    record=data[i+1:i+11]; oid=int(record[2]); count=int(record[9]); refs.add(record[1])
                    labels=data[i+11:i+11+count]
                    if len(labels)!=count: raise ValueError('Truncated object labels')
                    objects.append({'id':oid,'file':record[1],'labels':labels,'pos':tuple(map(float,record[3:6]))})
                    i+=11+count
                else:
                    i+=1; continue
                if oid in ids: errors.append(f'Duplicate ID {oid}')
                ids[oid]=(ti,kind)
            except (ValueError,IndexError) as exc:
                errors.append(f'{name}:{i+1}: {exc}'); i+=1
        tile_objects.append(objects)
        terrain=folder/(name+'.terrain')
        if not terrain.exists(): errors.append(f'Missing {terrain.name}'); continue
        raw=terrain.read_bytes()
        if len(raw)!=14888 or struct.unpack('<I',raw[:4])[0]!=60:
            errors.append(f'Invalid terrain lattice {terrain.name}'); continue
        values=struct.unpack('<3721f',raw[4:]); terrains[(tx,ty)]=values
        if not all(math.isfinite(h) for h in values): errors.append(f'Non-finite terrain {name}')
    for oid,s in splines.items():
        for field,otherfield,a,b in (('next','prev','end','start'),('prev','next','start','end')):
            other=s[field]
            if other==0: continue
            if other not in splines:
                errors.append(f'{oid}: missing linked spline {other}'); continue
            neighbor=splines[other]
            if neighbor[otherfield]!=oid or math.dist(s[a],neighbor[b])>.03:
                errors.append(f'{oid}: disconnected or asymmetric {field} link to {other}')
    seam_count=0; max_seam=0.
    for (tx,ty),v in terrains.items():
        right=terrains.get((tx+1,ty)); north=terrains.get((tx,ty+1))
        pairs=[]
        if right: pairs += [(v[j*61+60],right[j*61]) for j in range(61)]
        if north: pairs += [(v[60*61+i],north[i]) for i in range(61)]
        for a,b in pairs:
            seam_count+=1; max_seam=max(max_seam,abs(a-b))
    if max_seam>.001: errors.append(f'Terrain seams differ by {max_seam:.4f} metres')
    if max_grade>8.501: errors.append(f'Engineered road grade cap exceeded: {max_grade:.6f}%')
    ei=lines.index('[entrypoints]'); n=int(lines[ei+1])
    for i in range(n):
        r=lines[ei+2+i*12:ei+2+(i+1)*12]
        try:
            index,oid,ti=int(r[0]),int(r[1]),int(r[10]); obj=tile_objects[ti][index]
            if obj['id']!=oid or not obj['file'].endswith('spawn.sco'):
                raise ValueError('Entry point does not reference its actual tile object')
            if math.dist(obj['pos'],(float(r[3]),float(r[5]),float(r[4])))>.001:
                raise ValueError('Entry point and object positions disagree')
        except (ValueError,IndexError) as exc:
            errors.append(f'Entry {i}: {exc}')
    bus=read(folder/'TTData'/'Busstops.cfg')
    stops=re.findall(r'\[busstop\]\n([^\n]+)\n(\d+)\n(\d+)\n',bus)
    for name,ti,oid in stops:
        if ids.get(int(oid))!=(int(ti),'[object]'):
            errors.append(f'Stop {name}: invalid tile/object reference')
    mesh_count=0
    for ref in refs:
        path=root/Path(ref.replace('\\','/'))
        if not path.exists(): errors.append(f'Missing asset {ref}'); continue
        if path.suffix=='.sco':
            sco=read(path)
            for mesh_ref in re.findall(r'\[(?:mesh|collision_mesh)\]\n([^\n]+)',sco):
                mesh_path=path.parent/Path(mesh_ref.replace('\\','/'))
                if not mesh_path.exists(): errors.append(f'Missing mesh {mesh_path}'); continue
                m=read(mesh_path); mesh_count+=1
                if not m.startswith('xof 0303txt 0032') or m.count('{')!=m.count('}'):
                    errors.append(f'Invalid DirectX mesh structure {mesh_path.name}')
                for tex in re.findall(r'TextureFilename\s*\{\s*"([^"]+)";',m):
                    if not (path.parent/'texture'/tex).exists(): errors.append(f'Missing mesh texture {tex}')
            if path.name=='bus_stop.sco' and '[busstop]' not in sco:
                errors.append('Bus pole is not an OMSI bus-stop object')
        elif path.suffix=='.sli':
            sli=read(path)
            if '[heightprofile]' not in sli: errors.append(f'Missing road collision profile {path.name}')
            for tex in re.findall(r'\[texture\]\n([^\n]+)',sli):
                if not (path.parent/'texture'/tex).exists(): errors.append(f'Missing spline texture {tex}')
    manifest=json.loads((folder/'build_manifest.json').read_text())
    if manifest['road_splines']!=len(splines) or manifest['bus_stops']!=len(stops) or manifest['tiles']!=len(entries):
        errors.append('Manifest counts differ from generated records')
    report={'passed':not errors,'tiles':len(entries),'road_splines':len(splines),'objects':len(ids)-len(splines),
            'bus_stops':len(stops),'entrypoints':n,'asset_references':len(refs),'mesh_checks':mesh_count,
            'terrain_border_samples':seam_count,'maximum_terrain_seam_metres':max_seam,
            'maximum_road_grade_percent':max_grade,
            'road_segments_above_15_percent_grade':steep,'runtime_tested':False,'errors':errors}
    if (folder/'timetable_manifest.json').exists():
        spec=importlib.util.spec_from_file_location('tsingyi_tt_checks',Path(__file__).with_name('Generate-TsingYi-Timetable.py'))
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        report['timetable']=module.validate_generated(root)
        errors.extend(report['timetable']['errors'])
        report['passed']=not errors
    if 'road_contact_repair' in manifest:
        spec=importlib.util.spec_from_file_location('tsingyi_road_checks',Path(__file__).with_name('Repair-TsingYi-Roads.py'))
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        contact=module.repair(root,audit_only=True)
        report['road_contact']={k:v for k,v in contact.items() if k!='surface_object_ids'}
        if contact['terrain_vertices_lowered']:
            errors.append('Terrain still intrudes into the required road clearance envelope')
        for key,oid in contact['surface_object_ids'].items():
            sco=root/'Sceneryobjects/HK_TsingYi'/f'road_join_{key}.sco'
            if oid not in ids or not sco.exists() or '[surface]' not in read(sco) or '[collision_mesh]' not in read(sco):
                errors.append(f'Missing drivable joining surface at {key}')
        report['passed']=not errors
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--report',type=Path)
    args=parser.parse_args(); result=validate(args.root)
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['passed'] else 1)
