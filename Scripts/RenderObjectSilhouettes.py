# Script to render (all) single objects in a library in a wide variety of poses, positions, and sizes
import bvp,os
import numpy as np

LibDir = '/auto/k6/mark/SilhouettePrior/'
#os.path.join(LibDir,'SilhouetteSceneList.pik')
Lib = bvp.bvpLibrary(LibDir)
Type = ('ObjectMasks',)
### --- Parameters --- ### 
# Timing
nFrames = 30 # = 1 second. 30 for 1 TR? 1? 
# Image size
Res = 128 # pixels
nCamPos = 5 # for starters... 5 trajectories? x 5 positions, x 5 rotations; rotations and z
render_Pose = False # Render all separate poses; don't do it, we're going to be working with non-real-objects
# Rotations
nRot = 5 # -90,-45,0,45,90
oRot = [float(np.radians(d)) for d in np.linspace(-90,90,nRot)]
# Sizes
oSz = [1,2,3,4]
scaleObj = False # Do resize from 10
# Positions
# Positions are all at z=0 on a horizontal plane, spaced on a grid from -5 to 5 in both 
# x and y dimensions (Camera has been set up to see only these locations)
nPos = 5 # Grid of positions will be nPos x nPos, overlapping 
x,y = [p.flatten() for p in np.meshgrid(np.linspace(-5,5,nPos),np.linspace(-5,5,nPos))]
oPos = [(float(xx),float(yy),0) for xx,yy in zip(x,y)]

# Cameras w/ motion (currently (2012.09.29) there are *8*)
SLc = bvp.utils.basics.loadPik('/auto/k6/mark/SilhouettePrior/CamList.pik')
SceneCam = [s.Cam for s in SLc.ScnList]

sPath = '/auto/k6/mark/SilhouettePrior/Scenes/' # Must have "Scenes/" at the end

# Further subdivision of silhouettes? 
subCat = None # Specify more info for prior?? Different semantic category outlines??


### --- Down to business --- ###
RO = bvp.RenderOptions()
RO.BVPopts['BasePath'] = sPath
RO.resolution_x = RO.resolution_y = Res # smaller images
RO.BVPopts['Type'] = 'All' # 'FirstFrame' # 'FirstAndLastFrame' # 

if subCat:
	ToRender = Lib.getSCL(subCat,'objects')
else:
	ToRender = Lib.objects # all objects

ScCt = 0
ScnL = []
for o in ToRender:
	# Get all object variations to add as separate scenes
	ObToAdd = []
	for s in oSz:
		for pos in oPos:
			for rotZ in oRot:
				if o['nPoses'] and render_Pose:
					for p in range(o['nPoses']):
						O = bvp.bvpObject(obID=o['grpName'],Lib=Lib,pos3D=pos,size3D=s,rot3D=(0,0,rotZ),pose=p)
						ObToAdd.append(O)
						if scaleObj:
							ScObSz = 10.*scaleObj.size3D/O.size3D
							ScObToAdd.append
				else:
					O = bvp.bvpObject(obID=o['grpName'],Lib=Lib,pos3D=pos,size3D=s,rot3D=(0,0,rotZ))
					ObToAdd.append(O)
					# Add scale object in here somehwhere... Scale for each object!
					if scaleObj:
						ScObSz = 10.*scaleObj.size3D/O.size3D
						ScObToAdd.append
	# Lights (Sky), Background
	Sky = bvp.bvpSky()
	BG = bvp.bvpBG()
	# Objects
	for Obj in ObToAdd:
		# Camera
		for c in SceneCam:
			#Cam = bvp.bvpCamera() # w/ some parameters...
			# Create Scene
			ScCt+=1
			fPath = 'Sc%04d_##'%(ScCt)
			ScnL.append(bvp.bvpScene(Num=ScCt,Obj=(Obj,),BG=BG,Sky=Sky,
								Shadow=None,Cam=c,FrameRange=(1,nFrames),
								fPath=fPath,FrameRate=15))
# Convert list of scenes to SceneList	
SL = bvp.bvpSceneList(ScnList=ScnL,RenderOptions=RO)
# Save
SL.Save(os.path.join(LibDir,'SilhouetteSceneList.pik'))
SL.RenderSlurm(RenderGroupSize=5,RenderType=Type,Is_Overwrite=False)
