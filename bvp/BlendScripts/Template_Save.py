"""Save a group or object to an arbitray file. 
"""

import bpy
import bvp

# Parameters
grp_act = "{grp_act}"
name = "{name}"
tmpf = "{tmpf}"

# Check for existence of group/action
if name in getattr(bpy.data,grp_act):
    # Delete group / action (to be replaced with this one)

# Import group/action
bpy.ops.wm.import

# Abandoned for now - not essential for getting files.
#  More flexible / convenient, but not essential.