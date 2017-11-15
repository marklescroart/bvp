# Test bvpObConstraint's samplexy method 
# (Sampling in image plane)

import bvp
from bvp.utils.bvpMath import VectorFn,lst,vec2eulerXYZ,PerspectiveProj_Inv,linePlaneInt
if bvp.Is_Blender:
	import bpy
	uv = bpy.ops.mesh.primitive_uv_sphere_add

ImPos = [.5,.2] # i.e., (50,20) in a 100x100 image, or (250,100) in a 500x500 image
ObSz = 2.
camPos = [-5.,-5.,3.]
fixPos = [0.,0.,1.]
Cam = bvp.Camera(location=[camPos],fixPos=[fixPos],frames=[1])
#v = VectorFn(fixPos)-VectorFn(camPos)
#cTheta = vec2eulerXYZ(lst(v))

#oPos = PerspectiveProj_Inv(ImPos,camPos,cTheta,Z=10)
oPos = PerspectiveProj_Inv(ImPos,Cam,Z=10)
oPosZ = linePlaneInt(lst(camPos),oPos,P0=(0,0,ObSz/2))

print(oPos)
print(oPosZ)
if bvp.Is_Blender:
	uv(location=oPos)
	uv(location=oPosZ)