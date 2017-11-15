# Perspective projection test

import bvp

# Default camera
cam = bvp.Camera()
# Simple sphere object
Lib = bvp.bvpLibrary()
Pos3D = (5,2,0)
Sz3D = 2.2
ob = bvp.Object([],Lib,pos3D=Pos3D,size3D=Sz3D)
if bvp.Is_Blender:
    # Set render settings:
    RO = bvp.RenderOptions()
    RO.ApplyOpts()
    ob.PlaceObj()
    cam.PlaceCam()

# Easier handle for function
pp = bvp.utils.bvpMath.PerspectiveProj
# Test
if bvp.Is_Blender:
    imPos = pp(ob,cam)
else:
    imPos = pp(ob,cam) # ,d,CamMat
print('imPos = ')
print(imPos)
#print('d = ')
#print(d)
#print('Camera matrix = ')
#print(CamMat)