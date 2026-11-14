from pathlib import Path
import sys, importlib.util, json, math, collections, struct

from settings import ROOT, BUS
spec = importlib.util.spec_from_file_location('o3dconvert', ROOT/'work/vendor/Blender-O3D-IO-Public/o3d_io/o3dconvert.py')
o3d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(o3d)

def mesh_blocks():
    text = (BUS/'model/model_E6M_Grey_RAS.cfg').read_text(encoding='cp1252')
    blocks = []
    for part in text.split('[mesh]\n')[1:]:
        lines = part.splitlines()
        name = lines[0].strip()
        if not name.lower().endswith('.o3d'):
            continue
        conditions = []
        for i, line in enumerate(lines):
            if line == '[visible]':
                conditions.append((lines[i+1], float(lines[i+2])))
        visible = all(value == (1 if key == 'cp_lenkrad_visible' else 0) for key, value in conditions)
        blocks.append({'name': name, 'text': part, 'conditions': conditions, 'visible': visible})
    return blocks

def load(name):
    data = (BUS/'model'/name).read_bytes()
    if data[2] > 3 and struct.unpack_from('<I', data, 4)[0] != 0xffffffff:
        raise ValueError('Encrypted mesh; author source required: '+name)
    result = o3d.import_o3d(data)
    if not result[1] or not result[2] or result[-1]:
        raise ValueError('Invalid or encrypted mesh: '+name)
    return result

def main():
    report = {'source': str(BUS), 'variant': 'E6M_Grey_White.bus', 'target': 'ETS2 1.62.3.3', 'meshes': [], 'missing': []}
    textures = set()
    for b in mesh_blocks():
        if not (BUS/'model'/b['name']).exists():
            report['missing'].append(b['name'])
            continue
        d = load(b['name'])
        positions = [v[0] for v in d[1]]
        bnd = [[min(v[i] for v in positions), max(v[i] for v in positions)] for i in range(3)]
        mats = [m[-1] for m in d[3]]
        textures.update(mats)
        report['meshes'].append({k:b[k] for k in ('name','conditions','visible')} | {'vertices':len(positions),'triangles':len(d[2]),'raw_bounds':bnd,'textures':mats})
    report['texture_names'] = sorted(t for t in textures if t)
    report['visible_meshes'] = sum(m['visible'] for m in report['meshes'])
    report['visible_triangles'] = sum(m['triangles'] for m in report['meshes'] if m['visible'])
    path = ROOT/'work/e6m_audit.json'
    path.write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k not in ('meshes','texture_names')},indent=2))
    for m in report['meshes']:
        if m['name'] in ('body_E6M.o3d','whl0.o3d','dash.o3d','whl2_w.o3d','whl3.o3d','lenkrad.o3d'):
            print(json.dumps(m))

if __name__ == '__main__':
    main()
