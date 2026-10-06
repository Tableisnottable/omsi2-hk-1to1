import bpy, os
in_dir = r'C:\Users\Table\Documents\GitHub\omsi2-hk-1to1\src\gis\11-SE-1D'
out_dir = r'C:\Users\Table\Documents\GitHub\omsi2-hk-1to1\Sceneryobjects\HK_Objects\model'
for root, dirs, files in os.walk(in_dir):
    for f in files:
        if f.lower().endswith('.fbx'):
            bpy.ops.wm.read_factory_settings(use_empty=True)
            bpy.ops.import_scene.fbx(filepath=os.path.join(root, f))
            obj_name = os.path.splitext(f)[0] + '.obj'
            bpy.ops.wm.obj_export(filepath=os.path.join(out_dir, obj_name))