'''
Testing placement and posing of humans
''' 


# BROKEN.

import bvp
import bpy
scn = bpy.context.scene
# Get database
dbi = bvp.DBInterface()
humans = dbi.query(type='Object', semantic_category='human')
#Lib = bvp.bvpLibrary()
#hNm = Lib.getGrpNames('human')
# Put three different humans from the library in three positions, in three poses
cpos = bvp.utils.math.circle_pos(4, 5)
# Simple MakeHuman person
h1 = bvp.Object('006_F_AsianGirl',Lib, pose=2, pos3D=cpos[0] + [0], size3D=1.6)
h1.PlaceObj()
h2 = bvp.Object('sintel', Lib, pos3D=cpos[2] + [0], size3D=1.8)
h2.PlaceObj()
h3 = bvp.Object('002_M_IronMan', Lib, pose=3, pos3D=cpos[4] + [0], size3D=2.)
h3.PlaceObj()
scn.update()
scn.frame_current+=1
scn.update()
scn.frame_current-=1
scn.update()