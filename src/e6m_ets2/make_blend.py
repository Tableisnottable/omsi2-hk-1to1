from pathlib import Path
import bpy, pickle, math, numpy as np
from mathutils import Vector

from settings import ROOT
OUT=ROOT/'outputs/E6M_ETS2'
data=pickle.loads((ROOT/'work/e6m_scene.pkl').read_bytes())
bpy.ops.wm.read_factory_settings(use_empty=True)
materials=[]
for m in data['materials']:
    mat=bpy.data.materials.new(m['alias']+'_'+m['source'])
    mat.use_nodes=True
    nt=mat.node_tree
    bs=nt.nodes.get('Principled BSDF')
    bs.inputs['Roughness'].default_value=0.6
    img=bpy.data.images.load(m['texture']['file'],check_existing=True)
    tex=nt.nodes.new('ShaderNodeTexImage')
    tex.image=img
    nt.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    if m['effect'].endswith(('.a','.over')):
        nt.links.new(tex.outputs['Alpha'],bs.inputs['Alpha'])
        mat.surface_render_method='DITHERED'
    mat['scs_effect']=m['effect']
    mat['source_texture']=m['source']
    materials.append(mat)
bus=bpy.data.collections.new('E6M - converted source')
bpy.context.scene.collection.children.link(bus)
for i,m in enumerate(data['meshes']):
    verts=[(p[0],-p[2],p[1]) for p in m['positions']]
    # Official SCS-to-Blender conversion is a +90-degree rotation around X.
    faces=[tuple(f) for f in m['faces']]
    mesh=bpy.data.meshes.new(m['name'])
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    used=sorted(set(map(int,m['mat_ids'])))
    mapping={j:k for k,j in enumerate(used)}
    for j in used:
        mesh.materials.append(materials[j])
    mesh.polygons.foreach_set('material_index',[mapping[int(v)] for v in m['mat_ids']])
    mesh.polygons.foreach_set('use_smooth',[True]*len(mesh.polygons))
    uv=mesh.uv_layers.new(name='UVMap')
    indices=np.asarray(faces,dtype=np.int32).reshape(-1)
    uv_values=m['uv'][indices].copy()
    uv_values[:,1]=1-uv_values[:,1]
    uv.data.foreach_set('uv',uv_values.reshape(-1))
    # Let Blender rebuild normals; OMSI O3D files can contain NaNs and legacy split normals.
    ob=bpy.data.objects.new(m['name'][:-4],mesh)
    bus.objects.link(ob)
    ob['OMSI_source']=m['name']
    ob['conversion_role']='source_wheel' if m['wheel'] else 'body_and_cab'
    if i%50==0: print('MESH',i,m['name'],flush=True)

studio=bpy.data.collections.new('Preview studio - not exported')
bpy.context.scene.collection.children.link(studio)
def aim(ob,point):
    ob.rotation_euler=(Vector(point)-ob.location).to_track_quat('-Z','Y').to_euler()
def camera(name,position,target,lens=48):
    ca=bpy.data.cameras.new(name)
    ob=bpy.data.objects.new(name,ca)
    studio.objects.link(ob)
    ob.location=position
    ca.lens=lens
    aim(ob,target)
    return ob
cam=camera('Exterior front', (-12,16,9), (0,0,2.1),50)
camera('Exterior rear',(12,-16,8),(0,0,2.1),50)
camera('Driver view',(0.755,3.6,2.1),(0.755,7,1.8),20)
for name,pos,power,size in [('Key',(4,-7,11),2200,8),('Fill',(-7,-3,7),1600,7),('Rear',(1,7,10),2100,6)]:
    ld=bpy.data.lights.new(name,'AREA')
    ld.energy=power
    ld.shape='DISK'
    ld.size=size
    ob=bpy.data.objects.new(name,ld)
    studio.objects.link(ob)
    ob.location=pos
    aim(ob,(0,0,2))
bpy.ops.mesh.primitive_plane_add(size=200)
plane=bpy.context.object
plane.name='Studio floor'
for col in list(plane.users_collection): col.objects.unlink(plane)
studio.objects.link(plane)
mat=bpy.data.materials.new('Studio floor')
mat.diffuse_color=(0.13,0.15,0.18,1)
plane.data.materials.append(mat)
scene=bpy.context.scene
scene.world=bpy.data.worlds.new('Studio world')
scene.world.use_nodes=True
scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(0.25,0.28,0.32,1)
scene.world.node_tree.nodes.get('Background').inputs[1].default_value=0.6
scene.camera=cam
scene.render.engine='CYCLES'
scene.cycles.samples=24
scene.render.resolution_x=1400
scene.render.resolution_y=1000
scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
scene.render.image_settings.file_format='PNG'
bpy.ops.file.pack_all()
for a in bpy.context.screen.areas:
    if a.type=='VIEW_3D':
        a.spaces.active.region_3d.view_distance=17
        a.spaces.active.region_3d.view_location=(0,0,2)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'E6M_conversion.blend'))
scene.render.filepath=str(OUT/'E6M_preview.png')
bpy.ops.render.render(write_still=True)
scene.camera=bpy.data.objects['Driver view']
scene.render.filepath=str(OUT/'E6M_driver_preview.png')
bpy.ops.render.render(write_still=True)
print('BLEND_AND_PREVIEWS_DONE',flush=True)
