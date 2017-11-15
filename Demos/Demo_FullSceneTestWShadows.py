# Render (all) objects in bvpLibrary

import bvp,random,os
bvp.Verbosity_Level = 2
# Library
LibDir = '/auto/k6/mark/BlenderFiles/' # Load from settings??
Lib = bvp.bvpLibrary(LibDir)

nCamLoc = 1
nObjects = 2 # Randomize?
RO = bvp.RenderOptions()
RO.BVPopts['BasePath'] = '/auto/k6/mark/BVPpilot3_StaticTest/Scenes/%s'
RO.BVPopts["Type"] = "All" #'FirstFrame' # other options: ,"FirstAndLastFrame"
RO.resolution_x = 256
RO.resolution_y = 256
frames = (1,15)

# Misc setup
Is_Overwrite = False
DummyObjects = lambda x: [random.randint(0,Lib.nObjects-1) for a in range(x)]
ScCt = 0;
ScnL = []
for sky in Lib.getGrpNames(ComponentType='skies'):
	for bg in ['BG_001_Floor','BG_005_Floor','BG_100_BasketballCt','BG_102_Spaceport','BG_011_BrownHills']: # #Lib.getGrpNames(ComponentType='backgrounds'):
		for sh in Lib.getGrpNames(ComponentType='shadows'):
			ScCt+=1
			Sky = bvp.Sky(sky,Lib)
			BG = bvp.Background(bg,Lib)
			Shad = bvp.Shadow(sh,Lib)
			# Get dummy objects to put in scenes:
			ObL = []
			for o in DummyObjects(nObjects):
				ObL.append(bvp.Object(Lib.objects[o]['name'],Lib,size3D=None))
			# Camera variation
			for p in range(nCamLoc):
				cNum = p+1
				cPos = BG.CamConstraint.sampleCamPos(frames)
				fPos = BG.CamConstraint.sampleFixPos(frames)
				Cam = bvp.Camera(cPos,fPos,frames=frames,lens=BG.lens)
				fPath = '%s_%s_%s_%s_cp%d_fr##'%(BG.semantic_category[0],BG.name,Sky.name,Shad.name,cNum)
				fChk = RO.BVPopts['BasePath']%(fPath.replace('##','02.'+RO.file_format.lower()))
				if bvp.Verbosity_Level > 1:
					print('Checking for file: %s'%(fChk))
				if os.path.exists(fChk) and not Is_Overwrite:
					if bvp.Verbosity_Level > 1:
						print('Found it!')
					# Only append scenes to render that DO NOT have previews already rendered!
					continue				
				S = bvp.Scene(Num=ScCt,BG=BG,Sky=Sky,Obj=None,
								Shadow=Shad,Cam=Cam,FrameRange=frames,
								fPath=fPath,
								FrameRate=15)
				try:
					# Allow re-set of camera position with each attempt to populate scene
					S.PopulateScene(ObL,ResetCam=True)
				except:
					print('Unable to populate scene %s!'%S.fPath)
				ScnL.append(S)
# Convert list of scenes to SceneList	
SL = bvp.SceneList(ScnList=ScnL,RenderOptions=RO)
#SL.ScnList[0].Create(RO)
SL.RenderSlurm(RenderGroupSize=nCamLoc)
