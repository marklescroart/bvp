'''
Creating scenes for BVP (Blender Vision Project) pilot experiments

'''
try:
	import cPickle as pickle
except ImportError:
	print('NO CPICKLE FOR YOU!')
	import pickle
import imp
#import mlBPY_Utils as bvp
#import bvp_Classes as bvpC # classes for Object,Scene,SceneList
import bvp
from bvp.utils import GetGroups
from bvp.RenderOptions import RenderOptions

### --- Library file directories --- ###
obLibDir ='/auto/k6/mark/BlenderFiles/Objects/'
bgLibDir='/auto/k6/mark/BlenderFiles/Scenes/'
skyLibDir = '/auto/k6/mark/BlenderFiles/Scenes/'
ScnList_fName = '/auto/k6/mark/BVPpilot2_Stimuli/SceneList_Temp1.pik'

def TestSkies():
	'''
	Create Test images of all skies with scenes of random objects
	'''
	''' 
	Creation of stimuli for BVP pilot experiment 2
	'''
	# Specify scene parameters
	# Load library lists
	fNm = '/auto/k6/mark/BVPpilot2_Stimuli/SkyTest.pik'
	with open(fNm,'rb') as fid:
		ScnParamsTmp = pickle.load(fid)
	# Specify render options: first frame only, masks/z/etc, 
	ScnParams = {
		"nScenes":10,
		# Library files
		### --- Library file directories --- ###
		'obLibDir':'/auto/k6/mark/BlenderFiles/Objects/',
		'bgLibDir':'/auto/k6/mark/BlenderFiles/Scenes/',
		'skyLibDir':'/auto/k6/mark/BlenderFiles/Scenes/',
		# (Lists loaded above)
		#'skyIdx':[0,1,2,3,4,5,6,7,8,9]
		# Object count
		"nObj_mean":2.5, # These will be rounded to integers (obviously)
		"nObj_std":.5,
		"nObj_min":1,
		"nObj_max":4,
		# Timing
		"sPerScene_mean":2., # we will only render the first frame anyway
		"sPerScene_std":.33,
		"sPerScene_min":1.,
		"sPerScene_max":3.,
		"Minutes":None, # Minutes of video @ 15 fps -- 3 (1?) for val, 40 for trn
		"Seconds":None,
		"FrameRate":15.,
		# Other??
		
		### --- Object count, position, size --- ###
		"nObj_mean":2.5,
		"nObj_std":.8,
		"nObj_min":1,
		"nObj_max":4,
		"ObjSz_mean":9.5,
		"ObjSz_std":1.33,
		"ObjSz_min":7.,
		"ObjSz_max":12.,

		# Camera Params (general)
		"cParams":{
			
			"CamSpeedMean":5, # Meaningless for now 2011.10.26 - use 
			"CamSpeedStd":2,
			"CamSpeedMax":10,
			"CamSpeedMin":0

			},
		# Rendering options
		"rParams":{"resolution_x":250,	"resolution_y":250},
		# (Camera position is determined by individual backgrounds)
		# Backgrounds / skies
		# Assure that all combinations will be used equally?? 
		# Create all combinations of BGs, skies

		}
	

	ScnParams.update(ScnParamsTmp)
	#ScnParams['']
	# Create "SceneList" from parameters
	ScnList = bvp.SceneList(ScnParams)
	sName = '/Users/Work/Desktop/TempSkyScnList.pik'
	with open(sName,'wb') as fOut:
		pickle.dump(ScnList,fOut,protocol=2)
	print('saved %s'%sName)
	# Export design matrices, etc.
	
	#ScnList.Render(RenderOpts)
	# Render w/ intelligent checking for already-rendered files
	return ScnList
	
	
def ObjectBGSkyImages():
	'''
	Create individual images of all objects, backgrounds, and skies in library
	'''
	# Background: Get objects, backgrounds, skies from library:
	ObF,ObGrpList = bvpC.GetGroups(obLibDir,'Object')
	BGF,BGGrpList = bvpC.GetGroups(obLibDir,'BG')
	SkyF,SkyGrpList = bvpC.GetGroups(obLibDir,'Sky')
	
	nObjects = sum([len(x) for x in ObGrpList])
	nBGs = sum([len(x) for x in BGGrpList])
	nSkies = sum([len(x) for x in SkyGrpList])
	# Specify scene parameters
	ScnParams = {
		"nScenes":nObjects+nBGs+nSkies,
		# Object count
		"ObPerScene_mean":1,
		"ObPerScene_max":1,
		"ObPerScene_min":1,
		# Camera Params (general)
		"CamSpeed_mean":5, # Meaningless for now 2011.10.26
		"CamSpeed_max":10,
		"CamSpeed_min":0
		# (Camera position is determined by individual backgrounds)
		}
	# Create "SceneList" from parameters
	
	# Export design matrices, etc.
	
	# Specify render options: first frame only, masks/z/etc, 
	
	# Render w/ intelligent checking for already-rendered files
	
	
def BVPpilot2():
	''' 
	Creation of stimuli for BVP pilot experiment 2
	'''
	# Specify scene parameters
	# Load library lists
	fNm = '/Users/Work/Desktop/TempLibFiles.pik'
	with open(fNm,'rb') as fid:
		ScnParamsTmp = pickle.load(fid)
	#'/Users/Work/Desktop/BlenderTests/' '/Users/Work/MyCode/BlenderPython/bvp/Scripts/Test_Render.py'
	ScnParams = {
		#"nScenes":10,
		# Library files
		### --- Library file directories --- ###
		'obLibDir':'/auto/k6/mark/BlenderFiles/Objects/',
		'bgLibDir':'/auto/k6/mark/BlenderFiles/Scenes/',
		'skyLibDir':'/auto/k6/mark/BlenderFiles/Scenes/',
		# (Lists loaded above)
		
		# Object count
		"nObj_mean":2.5, # These will be rounded to integers (obviously)
		"nObj_std":.5,
		"nObj_min":1,
		"nObj_max":4,
		# Timing
		"sPerScene_mean":2.,
		"sPerScene_std":.33,
		"sPerScene_min":1.,
		"sPerScene_max":3.,
		"Minutes":1., # Minutes of video @ 15 fps -- 3 (1?) for val, 40 for trn
		"Seconds":None,
		"FrameRate":15.,
		# Other??
		
		### --- Object count, position, size --- ###
		"nObj_mean":2.5,
		"nObj_std":.8,
		"nObj_min":1,
		"nObj_max":4,
		"ObjSz_mean":9.5,
		"ObjSz_std":1.33,
		"ObjSz_min":7.,
		"ObjSz_max":12.,

		# Camera Params (general)
		"cParams":{
			
			"CamSpeedMean":5, # Meaningless for now 2011.10.26 - use 
			"CamSpeedStd":2,
			"CamSpeedMax":10,
			"CamSpeedMin":0

			}
		# (Camera position is determined by individual backgrounds)
		# Backgrounds / skies
		# Assure that all combinations will be used equally?? 
		# Create all combinations of BGs, skies

		}
	ScnParams.update(ScnParamsTmp)
	# Create "SceneList" from parameters
	ScnList = bvp.SceneList(ScnParams)
	sName = '/Users/Work/Desktop/TempScnList.pik'
	with open(sName,'wb') as fOut:
		pickle.dump(ScnList,fOut,protocol=2)
	print('saved %s'%sName)
	# Export design matrices, etc.
	
	# Specify render options: first frame only, masks/z/etc, 
	rOptDict = {
		"resolution_x":500,
		"resolution_y":500,
		
		}
	#RenderOpts = RenderOptions()
	#ScnList.Render(RenderOpts)
	# Render w/ intelligent checking for already-rendered files
	return ScnParams,ScnList
