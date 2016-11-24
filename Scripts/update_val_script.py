#  Test

import bvp
dbi = bvp.DBInterface()

db_update_script = """
import bvp
import bpy
import numpy as np

# Parameters
n_samples = 5

# Set scene to particular action
scn = bpy.data.scenes["{act_name}"]
bvp.utils.blender.set_scene(scn.name)
# Make sure armature object for action is selected
grp = bpy.data.groups["{act_name}"]
bvp.utils.blender.grab_only(grp)
ob = bpy.context.object

# Following is mostly lifted from modifications we made to Action.from_blender()

# Get action
act = ob.animation_data.action
ob_list = [ob] + list(ob.children)
st = int(np.floor(act.frame_range[0]))
fin = int(np.ceil(act.frame_range[1]))
# Loop over all frames in action
mn = []
mx = []
for fr in range(st, fin):
    # Update scene frame 
    scn.frame_set(fr)
    scn.update()
    # Re-visit me
    mntmp, mxtmp = bvp.utils.blender.get_group_bounding_box(ob_list)
    mn.append(mntmp)
    mx.append(mxtmp)
min_xyz = np.min(np.vstack(mn), axis=0).tolist()
max_xyz = np.max(np.vstack(mx), axis=0).tolist()
# Select specific frames
idx = np.floor(np.linspace(st, fin, n_samples)).astype(np.int)
idx[-1] -= 1 
min_xyz_trajectory = [mn[ii] for ii in idx]
max_xyz_trajectory = [mx[ii] for ii in idx]

# Get database interface object
dbi = bvp.DBInterface()
# Update the document in the database for this action with the new fields we need
# This is sufficient information to identify an action in the database
act_doc = dict(name="{act_name}")

# Check on what you're about to do
print(dbi.query(**act_doc))
print(min_xyz_trajectory)
print(max_xyz_trajectory)

# Uncomment these lines to make update for real
#dbi._update_value(act_doc, "min_xyz_trajectory", min_xyz_trajectory)
#dbi._update_value(act_doc, "max_xyz_trajectory", max_xyz_trajectory)
"""


act_list = dbi.query(type='Action')
for act in act_list[:1]: # This is the pythonic way to iterate over a list
    #act = act_list[i] # This is a very matlab / C way to program =-)
    script = db_update_script.format(act_name=act.name)
    stdout, stderr = bvp.blend(script, blend_file=act.fpath)
    try:
        # python 3
        print(str(stdout,'utf-8'))
        print(str(stderr,'utf-8'))
    except:
        # python 2
        print(stdout)
        print(stderr)