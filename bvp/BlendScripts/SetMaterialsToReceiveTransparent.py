"""
Script to change all materials to receive transparent shadows.

ML 2012.01.26
"""

import bpy
M = bpy.data.materials
print('I think there are %d materials!'%len(M))
for m in M:
	m.use_transparent_shadows = True
print('Done with switcheroo! saving...')
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)