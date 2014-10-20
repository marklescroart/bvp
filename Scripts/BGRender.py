# Render (all) objects in bvpLibrary

import bvp

LibDir = '/auto/k6/mark/BlenderFiles/' # Load from settings??

Lib = bvp.bvpLibrary(LibDir)

# Optional sub-category to render
SubCat = None #lambda x: x['grpName']=='BG_201_mHouse_1fl_1' #None #'outdoor'
nCamLoc = 5
RO = bvp.RenderOptions()
RO.filepath = '/auto/k6/mark/BlenderFiles/LibBackgrounds/%s'
DummyObjects = ['*soccer ball','*fire extinguisher','002_CartoonGuy']
if SubCat:
	ToRender = Lib.getSCL(SubCat,'backgrounds')
else:
	ToRender = Lib.backgrounds # all backgrounds

# Frame count
frames = (1,1)
# set standard lights (Sky)
Sky = bvp.bvpSky()
# Get dummy objects to put in scenes:
ObL = []
for o in DummyObjects:
	ObL.append(bvp.bvpObject(obID=o,Lib=Lib,size3D=None)
# Misc Setup
BGCt = 0;
ScnL = []
for bg in ToRender:
	BGCt+=1
	# Create Scene
	BG = bvp.bvpBG(bgID=bg['grpName'],Lib=Lib)
	for p in range(nCamLoc):
		cNum = p+1
		Cam = bvp.bvpCamera(location=BG.camConstraints.sampleCamPos(frames),fixPos=BG.camConstraints.sampleFixPos(frames),frames=frames)
		S = bvp.bvpScene(Num=BGCt,BG=BG,Sky=Sky,Obj=None,
							Shadow=None,Cam=Cam,FrameRange=(1,1),
							fPath='%s_%s_cp%d_fr##'%(BG.semanticCat[0],BG.grpName,cNum),
							FrameRate=15)
		try:
			# Allow re-set of camera position with each attempt to populate scene
			S.populate_scene(ObL,ResetCam=True)
		except:
			print('Unable to populate scene %s!'%S.fPath)
		ScnL.append(S)
# Convert list of scenes to SceneList	
SL = bvp.bvpSceneList(ScnList=ScnL,RenderOptions=RO)
#SL.ScnList[0].Create(RO)
#SL.RenderSlurm(RenderGroupSize=nCamLoc)
