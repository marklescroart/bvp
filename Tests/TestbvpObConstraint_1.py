# Test if bvp Object constraints are working properly
# A sanity check for code, and for constraints for a particular scene.
# Code will need changing depending on 
import bvp,bpy
import mathutils as bmu
# Specific to .blend file in which you're calling this!
G = bpy.data.groups['BG_DeDust_1']
nObj = 3
ObSz = 1 # TO DO: Sample allowable object sizes from constraints!

# Define function to place sphere
uv = bpy.ops.mesh.primitive_uv_sphere_add
# Get object + Camera constriants for background
camC,obC = bvp.utils.blender.GetConstr(G)
camC.speed = None
# Set up camera for scene:
fr = [1,25]
Cam = bvp.Camera(location=camC.sampleCamPos(fr),fixPos = camC.sampleFixPos(fr),frames=fr)
Cam.PlaceCam()
# Place objects!
Obst = []
for x in range(nObj):
	pos = obC.sampleXY(ObSz,Cam,Obst,EdgeDist=.20,ObOverlap=0)
	if not pos:
		raise Exception('No position found for object %d!'%x)
	#pos = obC.sampleXYZ(ObSz,Cam,Obst,EdgeDist=20,ObOverlap=0)
	tmpOb = bvp.Object(pos3D=pos,size3D=ObSz)
	Obst.append(tmpOb)
	pos += bmu.Vector([0,0,ObSz/2.])
	uv(location=pos,size=ObSz/2.)