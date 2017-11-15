"""
Save a group or object to an arbitray file. 

This (and every other script in this directory with Template_* in its name) is a TEMPLATE 
file, intended to be read in by another function, modified, and then called.

It will not run on its own.
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

## Abandoned for now - not essential for getting files. More flexible / convenient, but not essential.