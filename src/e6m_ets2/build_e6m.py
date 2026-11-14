"""Local OMSI E6M -> SCS intermediate conversion. Source game is read-only."""
from pathlib import Path
import collections, hashlib, json, math, pickle, re, shutil, sys, struct
import numpy as np
from PIL import Image
from inspect_e6m import ROOT, BUS, mesh_blocks, load

BASE = ROOT/'work/scs_source'
DEST = BASE/'vehicle/truck/adl_e6m'
TEXT = DEST/'textures'
REPORT = {'missing_textures': [], 'materials': [], 'meshes': [], 'excluded': []}

def put(path, text):
    p = BASE/path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8')

def vec(values):
    return '( '+' '.join('&'+struct.pack('>f',float(v)).hex() for v in values)+' )'

def header(kind, name, version):
    return f'Header {{\n FormatVersion: {version}\n Source: "E6M local conversion"\n Type: "{kind}"\n Name: "{name}"\n}}\n'

MAT = []
MAT_MAP = {}
TEX_MAP = {}
MESHES = []

def texture(name):
    key = name.lower() if name else '_white'
    if key in TEX_MAP:
        return TEX_MAP[key]
    alias = re.sub('[^a-z0-9_]', '_', Path(key).stem)[:36]+'_'+hashlib.sha1(key.encode()).hexdigest()[:6]
    candidates = [BUS/'texture'/str(name), BUS/'texture'/str(name).replace('.dds','.tga')]
    if key == '5671_back.tga':
        candidates.append(BUS/'texture/5671L_back.tga')
    src = next((p for p in candidates if p.is_file()), None)
    if src:
        img = Image.open(src).convert('RGBA')
    else:
        if name:
            REPORT['missing_textures'].append(name)
        img = Image.new('RGBA', (4,4), (255,255,255,0 if name else 255))
    # Power-of-two assets are required by the game texture compiler.
    w,h = img.size
    # BC-compressed D3D textures need a top level of at least one 4x4 block.
    nw,nh = max(4,2**round(math.log2(w))), max(4,2**round(math.log2(h)))
    if (w,h)!=(nw,nh):
        img=img.resize((nw,nh),Image.Resampling.LANCZOS)
    alpha = img.getchannel('A').getextrema()
    img.save(TEXT/(alias+'.tga'))
    put(f'vehicle/truck/adl_e6m/textures/{alias}.tobj',f'map 2d\n /vehicle/truck/adl_e6m/textures/{alias}.tga\naddr\n repeat\n repeat\n')
    out={'path':f'/vehicle/truck/adl_e6m/textures/{alias}', 'file':str(TEXT/(alias+'.tga')), 'alpha':alpha, 'source':str(src) if src else None}
    TEX_MAP[key]=out
    return out

def material(m, block):
    name=(m[-1] or '').lower()
    if name in ('d_dreck.tga','d_drecks.tga','d_dreck2.tga','d_dreck3.tga','regen.tga','rain_static.tga','rain_anim.tga','rt_no.tga'):
        return None
    tex=texture(m[-1])
    # OMSI material override scope: each [matl] / [matl_change] starts a new material.
    section=''
    for command in re.split(r'(?=\[matl(?:\]|_change\]))',block['text']):
        lines=command.splitlines()
        if len(lines)>1 and lines[0] in ('[matl]','[matl_change]') and lines[1].lower()==name:
            section=command
            break
    am=re.search(r'\[matl_alpha\]\s*\n(\d+)',section)
    alpha_mode=int(am[1]) if am else 0
    if name in ('e6m_left.tga','e6m_right.tga','e6x_back.tga','e6x_front.tga','e6x_top.tga'):
        alpha_mode=1
    # Dynamic dirt overlays start transparent in OMSI; do not turn their opaque white RGB into panels.
    if name in ('d_dreck.tga','d_drecks.tga','d_dreck2.tga','d_dreck3.tga'):
        return None
    effect='eut2.dif.spec'
    if alpha_mode==1:
        effect += '.a'
    elif alpha_mode==2 or m[0][3]<0.98:
        effect += '.over'
    color=tuple(max(0,min(1,c)) for c in m[0][:3])
    spec=tuple(max(0,min(0.5,c)) for c in m[1])
    shin=max(1,min(250,m[3]))
    key=(tex['path'],effect,color,spec,shin)
    if key not in MAT_MAP:
        alias=f'm{len(MAT):03d}'
        MAT_MAP[key]=len(MAT)
        MAT.append({'alias':alias,'effect':effect,'texture':tex,'diffuse':color,'specular':spec,'shininess':shin,'source':name,'alpha_mode':alpha_mode})
    return MAT_MAP[key]

def read_meshes():
    for block in mesh_blocks():
        name=block['name']
        if not block['visible']:
            REPORT['excluded'].append({'name':name,'reason':'OMSI default visibility condition'})
            continue
        # Dirt, fake shadows and changeable ticket/sign overlays need game-specific replacements.
        if name.lower() in ('shadow.o3d',):
            continue
        d=load(name)
        vertices=np.asarray([v[0] for v in d[1]],dtype=np.float32)
        normals=np.asarray([v[1] for v in d[1]],dtype=np.float32)
        uv=np.asarray([v[2] for v in d[1]],dtype=np.float32)
        # O3D Y-up, +Z forward -> SCS Y-up, -Z forward.
        positions=vertices*np.array([1,1,-1],dtype=np.float32)
        normals=normals*np.array([1,1,-1],dtype=np.float32)
        normals=np.nan_to_num(normals,nan=0.0,posinf=0.0,neginf=0.0)
        lengths=np.linalg.norm(normals,axis=1)
        normals[lengths>1e-6]/=lengths[lengths>1e-6,None]
        faces=np.asarray([t[0] for t in d[2]],dtype=np.int32)
        # Select winding by the supplied vertex normals, avoiding an undocumented handedness assumption.
        a,b,c=positions[faces[:,0]],positions[faces[:,1]],positions[faces[:,2]]
        orientation=np.einsum('ij,ij->i',np.cross(b-a,c-a),normals[faces].mean(axis=1))
        if np.count_nonzero(orientation<0)>np.count_nonzero(orientation>0):
            faces=faces[:,::-1]
        mat_indices=[material(m,block) for m in d[3]]
        triangle_mats=np.asarray([mat_indices[t[1]] if mat_indices[t[1]] is not None else -1 for t in d[2]])
        keep=triangle_mats>=0
        mesh={'name':name, 'positions':positions, 'normals':normals, 'uv':uv, 'faces':faces[keep], 'mat_ids':triangle_mats[keep], 'wheel':name.lower().startswith('whl')}
        MESHES.append(mesh)
        REPORT['meshes'].append({'name':name,'triangles':int(keep.sum()),'wheel':mesh['wheel']})

def pieces_for(meshes,offset=(0,0,0)):
    pieces=[]
    for mesh in meshes:
        for mi in np.unique(mesh['mat_ids']):
            faces=mesh['faces'][mesh['mat_ids']==mi]
            # O3D source pieces are already small, retaining seams and split normals.
            used,inv=np.unique(faces.reshape(-1),return_inverse=True)
            pieces.append({'mat':int(mi),'pos':mesh['positions'][used]-offset,'nrm':mesh['normals'][used],'uv':mesh['uv'][used],'faces':inv.reshape(-1,3)})
    return pieces

def write_model(name, meshes, part='cab', offset=(0,0,0), locators=None, variants=None):
    locators=locators or []
    variants=variants or {'default': {part:1}}
    pieces=pieces_for(meshes,offset)
    parts=list(dict.fromkeys([part]+[l.get('part',part) for l in locators]+[p for v in variants.values() for p in v]))
    nv=sum(len(p['pos']) for p in pieces)
    nt=sum(len(p['faces']) for p in pieces)
    s=header('Model',name,5)+f'Global {{\n VertexCount: {nv}\n TriangleCount: {nt}\n MaterialCount: {len(MAT)}\n PieceCount: {len(pieces)}\n PartCount: {len(parts)}\n BoneCount: 0\n LocatorCount: {len(locators)}\n Skeleton: "{name}.pis"\n}}\n'
    for m in MAT:
        s+=f'Material {{\n Alias: "{m["alias"]}"\n Effect: "{m["effect"]}"\n}}\n'
    # Streaming avoids building millions of small strings in memory.
    path=DEST/(name+'.pim')
    with path.open('w',encoding='utf-8') as f:
        f.write(s)
        for i,p in enumerate(pieces):
            f.write(f'Piece {{\n Index: {i}\n Material: {p["mat"]}\n VertexCount: {len(p["pos"])}\n TriangleCount: {len(p["faces"])}\n StreamCount: 4\n')
            for tag,fmt,values in [('_POSITION','FLOAT3',p['pos']),('_NORMAL','FLOAT3',p['nrm']),('_UV0','FLOAT2',p['uv']),('_RGBA','FLOAT4',np.ones((len(p['pos']),4)))]:
                f.write(f' Stream {{\n  Format: {fmt}\n  Tag: "{tag}"\n')
                if tag=='_UV0':
                    f.write('  AliasCount: 1\n  Aliases: "_TEXCOORD0"\n')
                for j,v in enumerate(values):
                    f.write(f'  {j} {vec(v)}\n')
                f.write(' }\n')
            f.write(' Triangles {\n')
            for j,t in enumerate(p['faces']):
                f.write(f'  {j} ( {t[0]} {t[1]} {t[2]} )\n')
            f.write(' }\n}\n')
        for p in parts:
            pcs=list(range(len(pieces))) if p==part else []
            loc=[i for i,l in enumerate(locators) if l.get('part',part)==p]
            f.write(f'Part {{\n Name: "{p}"\n PieceCount: {len(pcs)}\n LocatorCount: {len(loc)}\n Pieces: '+ ' '.join(map(str,pcs))+'\n Locators: '+' '.join(map(str,loc))+'\n}\n')
        for i,l in enumerate(locators):
            f.write(f'Locator {{\n Name: "{l["name"]}"\n')
            if 'hookup' in l:
                f.write(f' Hookup: "{l["hookup"]}"\n')
            f.write(f' Index: {i}\n Position: {vec(l["pos"])}\n Rotation: {vec(l.get("rot",(1,0,0,0)))}\n Scale: {vec((1,1,1))}\n')
            f.write('}\n')
    pit=header('Trait',name,1)+f'Global {{\n LookCount: 1\n VariantCount: {len(variants)}\n PartCount: {len(parts)}\n MaterialCount: {len(MAT)}\n}}\nLook {{\n Name: "default"\n'
    for m in MAT:
        attrs=[('FLOAT3','diffuse',m['diffuse']),('FLOAT3','specular',m['specular']),('FLOAT','shininess',(m['shininess'],)),('FLOAT','add_ambient',(0,)),('FLOAT','reflection',(0,))]
        pit+=f' Material {{\n Alias: "{m["alias"]}"\n Effect: "{m["effect"]}"\n Flags: 0\n AttributeCount: {len(attrs)}\n TextureCount: 1\n'
        for fmt,tag,value in attrs:
            pit+=f' Attribute {{\n Format: {fmt}\n Tag: "{tag}"\n Value: {vec(value)}\n }}\n'
        pit+=f' Texture {{\n Tag: "texture[0]:texture_base"\n Value: "{m["texture"]["path"]}"\n }}\n }}\n'
    pit+='}\n'
    for v,states in variants.items():
        pit+=f'Variant {{\n Name: "{v}"\n'
        for p in parts:
            pit+=f' Part {{\n Name: "{p}"\n AttributeCount: 1\n Attribute {{\n Format: INT\n Tag: "visible"\n Value: ( {states.get(p,0)} )\n }}\n }}\n'
        pit+='}\n'
    (DEST/(name+'.pit')).write_text(pit)
    return {'name':name,'vertices':nv,'triangles':nt,'pieces':len(pieces)}

def write_collision(name='truck'):
    s=header('Collision',name,2)+'Global {\n VertexCount: 0\n TriangleCount: 0\n MaterialCount: 0\n PieceCount: 0\n PartCount: 2\n LocatorCount: 1\n}\n'
    for part in ('cab','chs'):
        s+=f'Part {{\n Name: "{part}"\n PieceCount: 0\n LocatorCount: {int(part=="chs")}\n Pieces:\n Locators: '+('0' if part=='chs' else '')+'\n}\n'
    s+=f'Locator {{\n Name: "collision"\n Index: 0\n Position: {vec((0,2.4,0.54))}\n Rotation: {vec((1,0,0,0))}\n Alias: ""\n Weight: 1\n Type: "Box"\n Parameters: {vec((2.48,4.14,11.1,0))}\n}}\n'
    (DEST/(name+'.pic')).write_text(s)

def main():
    TEXT.mkdir(parents=True,exist_ok=True)
    read_meshes()
    body=[m for m in MESHES if not m['wheel']]
    wheel=[m for m in MESHES if m['wheel']]
    loc=[]
    def add(name,pos,part='cab',rot=(1,0,0,0),hookup=None):
        l={'name':name,'pos':pos,'part':part,'rot':rot}
        if hookup: l['hookup']=hookup
        loc.append(l)
    add('cabin',(0,0,0),'chs')
    eye=(0.755,2.1,-3.6)
    add('interior',eye)
    add('interior_uk',eye)
    add('cam_cabin',(0,4.8,-3.5))
    add('cam_cabin2',(0,4.8,2.5))
    add('hook_t',(0,0.85,5.8),'chs')
    # Wheel locator rotations follow the official SCS sample truck axes.
    for ax,z in enumerate((-2.5979,2.1633,3.6691)):
        typ='f' if ax==0 else 'r'
        for side,x in enumerate((-1.07,1.07)):
            rot=(1,0,0,0) if side==0 else (math.sqrt(0.5),0,-math.sqrt(0.5),0)
            wheel_index=side if ax==0 else (ax-1)*2+side
            add(f'wheel_{typ}_{wheel_index}_0',(x,0.5005,z),'chs',rot)
    for side,x in enumerate((-0.98,0.98)):
        for stem,hook,y in [('lh','headl',0.83),('lhi','high_beam',0.83),('lp','parkl',0.96)]:
            add(f'{stem}_{side}',(x,y,-5.06),hookup='flare.vehicle.'+hook)
        for stem,hook,y in [('lr','rearl',0.85),('lb','brakel',1.12),('lv','reversel',0.65)]:
            add(f'{stem}_{side}',(x,y,6.14),rot=(0,0,1,0),hookup='flare.vehicle.'+hook)
        for where,z,rot in [('f',-5.06,(1,0,0,0)),('r',6.14,(0,0,1,0))]:
            add(f'bl_{where}_{side}',(x,1.05,z),rot=rot,hookup='flare.vehicle.'+('lblinkerl' if side==0 else 'rblinkerl'))
    REPORT['models']=[write_model('truck',body,locators=loc,variants={'chs_6x2':{'cab':0,'chs':1},'e6m_cab':{'cab':1,'chs':0}})]
    # Confirmed against installed SCS Scania Touring PMG v0x15. Native
    # coaches use wheel_a_0..3 and wheel_b_0..1, with identity rotations.
    # Keep truck wheel locators out of this model to avoid extra wheel groups.
    coach_loc=[l.copy() for l in loc if not l['name'].startswith('wheel_')]
    for group,axles in (('a',(0,2)),('b',(1,))):
        for group_axle,axle in enumerate(axles):
            for side,x in enumerate((-1.07,1.07)):
                coach_loc.append({'name':f'wheel_{group}_{group_axle*2+side}',
                                  'pos':(x,0.5005,(-2.5979,2.1633,3.6691)[axle]),
                                  'part':'chs','rot':(1,0,0,0)})
    REPORT['models'].append(write_model('coach',body,locators=coach_loc,variants={'chs_6x2':{'cab':0,'chs':1},'e6m_cab':{'cab':1,'chs':0}}))
    REPORT['models'].append(write_model('interior',body,part='base',offset=np.array(eye)))
    write_collision()
    write_collision('coach')
    # Keep every selected source object for editing; source wheel geometry is retained in this scene.
    with (ROOT/'work/e6m_scene.pkl').open('wb') as f:
        pickle.dump({'meshes':MESHES,'materials':MAT,'eye':eye},f)
    REPORT['materials']=[{k:v for k,v in m.items() if k!='texture'} for m in MAT]
    REPORT['texture_count']=len(TEX_MAP)
    REPORT['mesh_count']=len(MESHES)
    REPORT['missing_textures']=sorted(set(REPORT['missing_textures']))
    (ROOT/'work/conversion_report.json').write_text(json.dumps(REPORT,indent=2))
    print(json.dumps({k:v for k,v in REPORT.items() if k not in ('meshes','materials','excluded')},indent=2))

if __name__=='__main__':
    main()
