# Render (all) objects in bvpLibrary

import bvp

LibDir = '/auto/k6/mark/BlenderFiles/' # Load from settings??

Lib = bvp.bvpLibrary(LibDir)

# Optional sub-category to render
SubCat = None #'animal'
rotList = [0] # List of rotations at which to render each object
Render_Pose = True # Whether to render all poses for a given object
ScaleObj = None # Object to render with all others for scale
RO = bvp.RenderOptions()
RO.filepath = '/auto/k6/mark/BlenderFiles/LibObjects/%s'

if SubCat:
	ToRender = Lib.getSCL(SubCat)
else:
	ToRender = Lib.objects # all objects

ObCt = 0
ScnL = []
for o in ToRender:
	# Get all object variations to add as separate scenes
	ObToAdd = []
	for rotZ in rotList:
		if o['nPoses']:
			for p in range(o['nPoses']):
				ObToAdd.append(bvp.Object(obID=o['name'],Lib=Lib,pos3D=(0,0,0),size3D=10,rot3D=(0,0,rotZ),pose=p))
		else:
			ObToAdd.append(bvp.Object(obID=o['name'],Lib=Lib,pos3D=(0,0,0),size3D=10,rot3D=(0,0,rotZ)))
	# Camera, Lights (Sky), Background
	Cam = bvp.Camera()
	Sky = bvp.Sky()
	BG = bvp.Background()
	# Set up list of scenes for SceneList
	
	for Obj in ObToAdd:
		# Create Scene
		ObCt+=1
		if Obj.pose or Obj.pose==0:
			pNum = Obj.pose+1
		else:
			pNum = 1
		ScnL.append(bvp.Scene(Num=ObCt,Obj=(Obj,),BG=BG,Sky=Sky,
							Shadow=None,Cam=Cam,FrameRange=(1,1),
							fpath='%s_%s_p%d_r%d_fr##'%(Obj.semantic_category[0],Obj.name,pNum,Obj.rot3D[2]),FrameRate=15))
# Convert list of scenes to SceneList	
SL = bvp.SceneList(ScnList=ScnL,RenderOptions=RO)
SL.RenderSlurm(RenderGroupSize=1)

#[12,14,15,17,18]