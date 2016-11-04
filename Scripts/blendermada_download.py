# Download all materials from blendermada online material library (www.blendermada.com)

# First install blendermada plugin (v 0.9.8-b, downloaded 2016/10/04)

# Before calling: Open a blank .blend file

import os
import bpy
import bvp

scn = bpy.context.scene

# Get all latest materials
scn.render.engine = 'CYCLES'
bpy.ops.bmd.update()

# Clear scene
for o in scn.objects:
    scn.objects.unlink(o)

# Add single cube
bpy.ops.mesh.primitive_cube_add(location=(0,0,0))
ob = bpy.context.object

# Loop over categories (e.g. Cloth, Nature, etc)
for cat_idx in range(len(scn.bmd_category_list)):
    scn.bmd_category_list_idx = cat_idx
    cat_name = scn.bmd_category_list[cat_idx].name
    print("Importing {} materials...".format(cat_name.lower()))
    # Loop over specific materials
    for mat_idx in range(len(scn.bmd_material_list)):
        scn.bmd_material_list_idx = mat_idx
        mat_name = scn.bmd_material_list[mat_idx].name
        # Import material
        bpy.ops.bmd.importmat()
        scn.update()
        mat = ob.material_slots[0].material
        # Incorporate category into name, set up fake user to keep material through close of file
        mat.name = '{}_{}'.format(cat_name.lower(), mat_name.lower())
        mat.use_fake_user = True

# Clear scene
for o in scn.objects:
    scn.objects.unlink(o)
sfile = os.path.expanduser(bvp.config.get('path','db_dir'))
fname = 'Blendermada_Materials.blend'
sfile = os.path.join(sfile, 'Material', fname)
bpy.ops.wm.save_mainfile(filepath=sfile)


dbi = bvp.DBInterface()

for mat in bpy.data.materials:
    m = bvp.Material(name=mat.name, fname=fname, _id=dbi.get_uuid(), dbi=dbi)
    m.save()