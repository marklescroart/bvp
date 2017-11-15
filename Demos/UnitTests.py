# Test if bvp Object constraints are working properly
# A sanity check for code, and for constraints for a particular scene.
# Code will need changing depending on 
import bvp
import copy
import numpy as np
import matplotlib.pyplot as plt
# Define function to place sphere
# import bpy
# uv = bpy.ops.mesh.primitive_uv_sphere_add
# Bias = np.array([[ 0.,  0.,  25.,  25.,  25.],
# 				[  0.,  0.,  25.,  25.,  25.],
# 				[  0.,  0.,  25.,  25.,  25.],
# 				[  0.,  0.,  25.,  25.,  25.],
# 				[  0.,  0.,  25.,  25.,  25.]])
def ImPosTest(Bias=None,nReps=250):
	ImC = bvp.utils.math.ImPosCount(0,0,1.,5,e=5) # 5 x 5 bins, 0-1 evenly spaced
	if Bias is not None:
		ImC.hst = copy.deepcopy(Bias)
	print('Original 2D histogram:')
	print(ImC.hst)
	XY = []
	for r in range(nReps):
		x,y = ImC.sampleXY()
		ImC.updateXY(x,y)
		XY.append([x,y])
	x,y = np.array(XY).T
	plt.figure()
	plt.plot(x,y,'ko',alpha=.5)
	plt.title('Sampled positions')
	plt.show()
	print('New 2D histogram:')
	print(ImC.hst)
	return ImC

def BGshow(BGname,nObj=4,frames=(1,45),Lib=None,nIter_Scenes=100):
	'''
	Tests whether constraints are working properly in a (newly-added) background
	RUN THIS TEST BEFORE TRYING TO USE A BG IN A RENDER.

	ML 2012.07.25
	'''
	# Misc
	fps = 15
	RO = bvp.RenderOptions()
	RO.BVPopts['BasePath'] = '/auto/k1/mark/Desktop/TestRenders/%s'
	RO.BVPopts["Type"] = "FirstAndLastFrame" # 'All' # FirstFrame' # "FirstAndLastFrame"
	if Lib is None:
		# Get library:
		Lib = bvp.bvpLibrary()
	BG = bvp.Background(BGname,Lib)
	cPos = BG.CamConstraint.sampleCamPos(frames)
	fPos = BG.CamConstraint.sampleFixPos(frames)
	Cam = bvp.Camera(cPos,fPos,frames=frames,lens=BG.lens)
	Sky = bvp.Sky('*'+BG.sky_semantic_category[0],Lib)
	ObSz = [BG.obConstraints.sampleSize() for o in range(nObj)]
	ObList = [bvp.Object(size3D=None) for sz in ObSz]
	# File path
	fPath = 'ScTest_##'
	# Create scene
	S = bvp.Scene(Num=1,BG=BG,Sky=Sky,Obj=None,
					Shadow=None,Cam=Cam,FrameRange=frames,
					fPath=fPath,
					FrameRate=fps)
	try:
		S.PopulateScene(ObList,ResetCam=True,RaiseError=True,ImPosCt=None,ObOverlap=.25,EdgeDist=0.,nIter=nIter_Scenes)
	except:
		try:
			# Resort to more overlap for problematic scenes
			S.PopulateScene(ObList,ResetCam=True,RaiseError=True,ImPosCt=None,ObOverlap=.35,EdgeDist=.15,nIter=nIter_Scenes)
		except:
			print('Failed to populate scene after %d tries!'%nIter_Scenes)
			return
	if bvp.Is_Blender:
		print('Calling Scene.Create()')
		S.Create(rOpts=RO)
	return S

def BGtest(BGname,nObj=4,frames=(1,45),Lib=None,nReps=5,Is_Render=True):
	'''
	Tests whether constraints are working properly in a (newly-added) background
	RUN THIS TEST BEFORE TRYING TO USE A BG IN A BIG RENDER.

	ML 2012.07.25
	'''
	# Misc
	fps = 15
	nIter_Scenes = 100
	RO = bvp.RenderOptions()
	RO.BVPopts['BasePath'] = '/auto/k1/mark/Desktop/TestRenders/%s'
	#RO.BVPopts["Type"] = "FirstAndLastFrame" # 'All' # FirstFrame' # "FirstAndLastFrame"
	if Lib is None:
		# Get library:
		Lib = bvp.bvpLibrary()
	ScnList = []
	for iRep in range(nReps):
		BG = bvp.Background(BGname,Lib)
		cPos = BG.CamConstraint.sampleCamPos(frames)
		fPos = BG.CamConstraint.sampleFixPos(frames)
		Cam = bvp.Camera(cPos,fPos,frames=frames,lens=BG.lens)
		Sky = bvp.Sky('*'+BG.sky_semantic_category[0],Lib)
		ObSz = [BG.obConstraints.sampleSize() for o in range(nObj)]
		ObList = [bvp.Object(size3D=None) for sz in ObSz]
		# File path
		fPath = 'ScTest%d_##'%iRep
		# Create scene
		S = bvp.Scene(Num=1,BG=BG,Sky=Sky,Obj=None,
						Shadow=None,Cam=Cam,FrameRange=frames,
						fPath=fPath,
						FrameRate=fps)
		try:
			S.PopulateScene(ObList,ResetCam=True,RaiseError=True,ImPosCt=None,ObOverlap=.25,EdgeDist=0.,nIter=nIter_Scenes)
		except:
			try:
				# Resort to more overlap for problematic scenes
				S.PopulateScene(ObList,ResetCam=True,RaiseError=True,ImPosCt=None,ObOverlap=.35,EdgeDist=.15,nIter=nIter_Scenes)
			except:
				print('Failed to populate scene after %d tries!'%nIter_Scenes)
		ScnList.append(S)
	SL = bvp.SceneList(ScnList=ScnList,RenderOptions=RO)
	if Is_Render:
		SL.RenderSlurm(RenderType=('Image','Test'),RenderGroupSize=1)
	else:
		return SL


# Script to test getting voxelized point representation of meshes for bvpLibrary:
def TestGetObjProps():
	from bvp.utils.basics import RunScriptForAllFiles
	Scr = '/auto/k1/mark/MyCode/BlenderPython/bvp/Scripts/GetObjectProps.py'
	bvp.Verbosity_Level = 5
	RunScriptForAllFiles(Scr,['/auto/k6/mark/BlenderFiles/Objects/Category_Geometrical.blend']) #Vehicles_04.blend'])