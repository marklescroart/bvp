"""
.B.lender .V.ision .P.roject database class


FOR THIS CLASS: 

Unclear what to do about rendering different chunks of this as simple demos. 

Impression is that that should all be cleared out to scripts, that wrap the database. 

Voxelize, e.g., should be a method of the object. 
As should Point Cloud,
as should desaturate,
as should (noisify), 
as should ... ? 



Game plan: 

Each item stored in the database will map to a particular bvp class:

- Scene elements -
bvp_object
bvp_bg
bvp_sky
bvp_camera
bvp_shadow

- Actions - 
bvp_action - must be linked to an object or group of objects
bvp_armature - armature??

- Scenes - 
bvp_scene
bvp_scene_list


-> What to do about constraints? store as db objects as well? (linked to other )

-> Add armature field to objects
-> All animations must be based on armatures, and we should be able to flexibly define classes of armatures.
-> All positioning should probably be done with armatures, too. Or maybe no. Because bounding boxes 
	will still be unique to individual meshes, and not all meshes will deform. 

Fields for objects: 
semantic_labels # loose; whatever hierarchy you feel like labeling. Useful for pulling specific classes of STUFF.
wordnet_cat # precise(ish); wordnet label + all hypernyms.
real_world_size # 
grp_name # Name of group in .blend file. Should be unique. Meh. Maybe not. Has to at least be unique in file.

-> Kill BVP library. 

"""

# Imports
import pymongo
import subprocess,bvp,math,os,re,random,shutil,time
from bvp.utils.blender import GetGroups
from bvp.utils.basics import GetHostName,unique,loadPik,RunScriptForAllFiles#,dotDict
from bvp.bvpObject import bvpObject as bvpObj
if bvp.Is_Blender:
	import bpy



# Make sure that all files in these directories contain objects / backgrounds / skies that you want to use. Otherwise, modify the lists of objects / bgs / skies below.
class bvpDB(object):
	'''
	Class to interact with (mongo) database 
	'''
	def __init__(self,dbname=bvp.Settings['db']['name'],dbhost=bvp.Settings['db']['host'],
				port=bvp.Settings['db']['port']):
		'''Class to interface with bvp elements stored in mongo db
		
		Separate collections for objects, bgs, 
		
		Files in the library directory must be stored according to bvp directory structure: 
		
		BaseDirectory/ Objects/ <Category_*.blend and Category_*.pik>
			           Backgrounds/ <Category_*.blend and Category_*.pik>
			           Skies/ <Category_*.blend and Category_*.pik>
					   Shadows/ <Category_*.blend and Category_*.pik>
		Parameters
		----------
		dbhost : string
			Name for host server. Read from config file. Config default is intialized to be 'localhost'
		dbname : string
			Database name. Read from config file. Config default is intialized to be 'bvp_1.0'
		port : scalar
			Port number for database. 
		Notes
		-----
		start mongodb with "mongod --port 9194" or, if you are not using the 
		default db directory, "mongod --dbpath /Users/mark/Projects/BVP_mongodb/ --port 9194"
		'''		
		#self.LibDir = LibDir
		self.dbi = pymongo.MongoClient(host=dbhost,port=port)[dbname]
		# Make bvpDB fields (objects, backgrounds, skies, etc) the actual database collections (?)
		for sc in ['objects','backgrounds','skies','shadows']: # More? Better not to enumerate? 
			setattr(self,sc,self.dbi[sc])
	def query(self,sctype,**query_dict):
		'''Query the database for particular scene elements (objects, backgrounds, skies, etc)
		
		dict for query is in... mongodb language? (commit hard? or back off with some abstraction?)

		Parameters
		----------

		Returns
		-------

		'''
		wtf = self[sctype].find(query_dict) 
		# Need indices
		# Convert to class

		return wtf

	def print_list(self,fname,params,sctype=('objects',),qdict=None):
		'''Prints a semicolon-separated list of all groups (and parameters??) to a text file
		
		Gets grp Names (unique ids for each object / background / etc). By default, gets ALL names, but can be filtered
		(as in getSceneComponentList)

		Parameters
		----------
		fname : string file name
			File name for file to which to write. Extant files will be overwritten.
		params : list|tuple
			List of parameters to print. 
		sctype : list|tuple
			List of scene component types for which to print items.
		
		Returns
		-------
		(nothing - writes to file)
		'''
		if qdict is None:
			# Return all objects
			qdict = {}
		fid = open(fname,'w')
		for sct in sctype:
			ob = self.dbi[sct].find(qdict)
			for o in ob:
				ss = o['grpName'] + ("; %s"*len(params))%tuple([repr(o[p]) for p in params])
				fid.write(ss+'\n')
		fid.close()
	def read_list(self,fname):
		"""Reads in a list in the same format as print_list, uses it to update many database fields

		Optionally print list of stuff to be updated before running update? 
		"""
		pass

	def add_file(self,fname,sctype): 
		'''Adds groups in file to database, moves file?
		
		NOT UPDATED YET. STILL WORKING.
		.blend files -> *Props.txt files

		Update text files (objectProps.txt,backgroundProps.txt,etc) that 
		store meta-information about objects / backgrounds / etc. in 
		archival .blend files. This file READS the .blend files and WRITES
		to the text files. 

		Input ClassToUpdate specifies which class(es) to update. It is a tuple;
		default is all classes ('object','background','sky','shadow')
		
		** USE WITH CAUTION - this makes changes to your archival file info! ** 
		(as a precaution, this renames old *Props.txt' files to *Props_<date+time>.txt)
		'''
		if bvp.Verbosity_Level > 1:
			print('Updating *Props.txt files!')
		for cls in ClassToUpdate:
			# One: move old prop files to new file names:
			PropfNm = os.path.join(self.LibDir,cls+'Props.txt')
			if os.path.exists(PropfNm):
				os.rename(PropfNm,PropfNm.replace('.txt',time.strftime('_%Y%m%d_%H%M.txt')))
			# Two: get all files on which to operate and script
			fDir = os.path.join(self.LibDir,cls.capitalize().replace('y','ie')+'s')
			fList = [os.path.join(fDir,f) for f in os.listdir(fDir) if f[-3:]=='end' and 'Category_' in f]
			fList.sort()
			scriptF = os.path.join(bvp.__path__[0],'Scripts','List'+cls.capitalize()+'Props.py')
			# Three: Run script
			RunScriptForAllFiles(scriptF,fList,Inpts=[self.LibDir])

	##########################################################
	### --- FROM HERE: OLD FUNCTIONS. Replace? Update? --- ###
	##########################################################
	def UpdateBlendFiles(self,ClassToUpdate=('object','background','sky','shadow')):
		'''
		NOTES:
		For maximum portability of files, it should be possible to 
		store within each .blend file all the necessary information to
		upload it to another database. Thus this function should be 
		converted to something like a pack_blends file, that would 
		write all database information to blender-defined properties
		of each group in each .blend file.

		*Props.txt files -> .blend files

		Update .blend files based on information in *Props.txt files 
		(objectProps.txt,backgroundProps.txt,etc) that store meta-information 
		about objects / backgrounds / etc. in the archival .blend files. 
		This file READS the *Props.txt files and WRITES	to the blend files. 
		
		Input ClassToUpdate specifies which class(es) to update. It is a tuple;
		default is all classes ('object','background','sky','shadow')

		** USE WITH CAUTION - this makes changes to your archival files! ** 
		** THESE CHANGES ARE NOT REVERSIBLE without considerable effort! **
		** (depending on the size of your library, of course) **
		'''
		if bvp.Verbosity_Level > 1:
			print('Updating .blend files!')
		for cls in ClassToUpdate:
			fDir = os.path.join(self.LibDir,cls.capitalize().replace('y','ie')+'s')
			fList = [os.path.join(fDir,f) for f in os.listdir(fDir) if f[-3:]=='end' and 'Category_' in f]
			fList.sort()
			if bvp.Verbosity_Level > 1:
				print('%s files to update:'%cls.capitalize())
				print(fList)
			scriptF = os.path.join(bvp.__path__[0],'Scripts','Set'+cls.capitalize()+'Props.py')
			RunScriptForAllFiles(scriptF,fList,Inpts=[self.LibDir])


	def UpdateLibrary(self,ClassToUpdate=('object','background','sky','shadow')):
		'''
		.blend files -> .pik files

		Update all .pik files that store properties for all object, background, 
		sky, and shadow properties in the library directory

		Input ClassToUpdate specifies which class(es) to update. It is a tuple;
		default is to update all classes ('object','background','sky','shadow')
		
		** USE WITH CAUTION - this makes changes to your archival file info! ** 		
		'''
		if bvp.Verbosity_Level > 1:
			print('Updating library .pik files!')
		for cls in ClassToUpdate:
			fDir = os.path.join(self.LibDir,cls.capitalize().replace('y','ie')+'s')
			fList = [os.path.join(fDir,f) for f in os.listdir(fDir) if f[-3:]=='end' and 'Category_' in f]
			if bvp.Verbosity_Level > 1:
				print('%s files to update:'%cls.capitalize())
				print(fList)
			scriptF = os.path.join(bvp.__path__[0],'Scripts','Get'+cls.capitalize()+'Props.py')
			RunScriptForAllFiles(scriptF,fList)
	def UpdateAll(self,ClassToUpdate=('object','background','sky','shadow')):
		'''
		Updates (1) Blend files from Prop files
				(2) Prop files from Blend files (to remove any instructions to change semantic categories / names, e.g.)
				(3) .py (lib) files from Blend files

		NOTE: if you add objects to the archival .blend files, you should first call "UpdatePropFiles" (if there is nothing
				else to update), and THEN call UpdateAll()
		'''
		# First: Apply any changes in Prop files to Blend files 
		# (This will ignore any new objects in Blend files)
		self.UpdateBlendFiles(ClassToUpdate)
		# Second: Re-apply committed changes to prop files. This re-creates
		# the Prop files, with changes applied and any new objects added.
		self.UpdatePropFiles(ClassToUpdate)
		# Third: Update library file from newly-updated .blend files.
		self.UpdateLibrary(ClassToUpdate)
		
	def PosedObList(self):
		'''
		Get a list of posed objects as bvpObjects - duplicate each object for however many poses it has
		'''
		ObList = []
		for o in self.objects:
			if o['nPoses']:
				for p in range(o['nPoses']):
					ObList.append(bvpObj(o['grpName'],self,size3D=None,pose=p))
			else:
				ObList.append(bvpObj(o['grpName'],self,size3D=None,pose=None))
		return ObList

	def render_objects(self,query_dict,rtype=('Image',),rot_list=(0,),render_pose=True,render_group_size=1,is_overwrite=False,scale_obj=None):

	#def RenderObjects(self,Type=('Image',),subCat=None,rotList=(0,),render_Pose=True,renderGroupSize=1,Is_Overwrite=False,scaleObj=None):
		'''
		Render (all) objects in bvpLibrary

		IS THIS NECESSARY? maybe. More flexible render class for simple renders: 
		define scene, diff camera angles, put objects into it? 
		or: rotate objects? (define armature?)
		or: render all actions? 

		ScaleObj = optional scale object to render along with this object (NOT FINISHED!)
		'''
		
		RO = bvp.RenderOptions() # Should be an input, as should scene
		RO.BVPopts['BasePath'] = os.path.join(self.LibDir,'Images','Objects','Scenes','%s')
		RO.resolution_x = RO.resolution_y = 256 # smaller images
		
		if subCat:
			ToRender = self.getSCL(subCat,'objects')
		else:
			ToRender = self.objects # all objects
		
		ObCt = 0
		ScnL = []
		for o in ToRender:
			# Get all object variations to add as separate scenes
			ObToAdd = []
			for rotZ in rotList:
				if o['nPoses'] and render_Pose:
					for p in range(o['nPoses']):
						O = bvp.bvpObject(obID=o['grpName'],Lib=self,pos3D=(0,0,0),size3D=10,rot3D=(0,0,rotZ),pose=p)
						ObToAdd.append(O)
						if scaleObj:
							ScObSz = 10.*scaleObj.size3D/O.size3D
							ScObToAdd.append
				else:
					O = bvp.bvpObject(obID=o['grpName'],Lib=self,pos3D=(0,0,0),size3D=10,rot3D=(0,0,rotZ))
					ObToAdd.append(O)
					# Add scale object in here somehwhere... Scale for each object!
					if scaleObj:
						ScObSz = 10.*scaleObj.size3D/O.size3D
						ScObToAdd.append
			# Camera, Lights (Sky), Background
			Cam = bvp.bvpCamera()
			Sky = bvp.bvpSky()
			BG = bvp.bvpBG()
			# Objects
			for Obj in ObToAdd:
				# Create Scene
				ObCt+=1
				if Obj.pose or Obj.pose==0:
					pNum = Obj.pose+1
				else:
					pNum = 1
				fPath = '%s_%s_p%d_r%d_fr##'%(Obj.semanticCat[0],Obj.grpName,pNum,Obj.rot3D[2])
				ScnL.append(bvp.bvpScene(Num=ObCt,Obj=(Obj,),BG=BG,Sky=Sky,
									Shadow=None,Cam=Cam,FrameRange=(1,1),
									fPath=fPath,FrameRate=15))
		# Convert list of scenes to SceneList	
		SL = bvp.bvpSceneList(ScnList=ScnL,RenderOptions=RO)
		SL.RenderSlurm(RenderGroupSize=renderGroupSize,RenderType=Type)
		#SL.Render(RenderGroupSize=renderGroupSize,RenderType=Type)

	def RenderObjectVox(self,nGrid=10,xL=(-5,5),yL=(-5,5),zL=(0,10),maxFilesPerDir=5000,
						subCat=None,render_Pose=True,Is_Overwrite=False):
		'''
		Render (all) objects in bvpLibrary in voxelized 3D form

		TODO: longer help!
		ScaleObj = optional scale object to render along with this object (NOT FINISHED!)
		'''
		if bvp.Is_Blender:
			print('Sorry, this won''t run inside Blender; it requires access to slurm!')
			return
		RO = bvp.RenderOptions()
		RO.BVPopts['Voxels'] = True # This will over-ride all other options...
		RO.BVPopts['BasePath'] = os.path.join(self.LibDir,'Images','Objects','Voxels','%s')
		RO.BVPopts['Type'] = 'all'
		RO.resolution_x = RO.resolution_y = 5 # itty-bitty images for inside/outside test
		
		if subCat:
			ToRender = self.getSCL(subCat,'objects')
		else:
			ToRender = self.objects # all objects
		
		ObCt = 0
		for o in ToRender:
			ScnL = []
			# Get all object variations to add as separate scenes
			ObToAdd = []
			if o['nPoses'] and render_Pose:
				for p in range(o['nPoses']):
					O = bvp.bvpObject(obID=o['grpName'],Lib=self,pos3D=(0,0,0),size3D=10,pose=p)
					ObToAdd.append(O)
			else:
				O = bvp.bvpObject(obID=o['grpName'],Lib=self,pos3D=(0,0,0),size3D=10)
				ObToAdd.append(O)
			# Lights (Sky) & Background
			Sky = bvp.bvpSky()
			Sky.WorldParams['horizon_color'] = (0,0,0)
			BG = bvp.bvpBG()
			# Get all (nGrid**3) camera positions
			cPos = bvp.utils.basics.gridPos(nGrid,xL,yL,zL)
			# Center (fixation) Position
			fPos = [[0,0,0] for x in range(len(cPos))]
			fr = range(1,nGrid**3+1)
			# break up into multiple directories with <maxFilesPerDir> files each
			nDirs = int(math.ceil((nGrid**3)/float(maxFilesPerDir)))
			# Loop over objects to render each <maxFilesPerDir> files
			for Obj in ObToAdd:
				# Loop to create a separate scene for each <maxFilesPerDir> files
				for d in range(nDirs):
					# Create Scene
					ObCt+=1
					if Obj.pose or Obj.pose==0:
						pNum = Obj.pose+1
					else:
						pNum = 1
					# Frame range
					FR = (d*maxFilesPerDir+1,min(nGrid**3,maxFilesPerDir*(d+1)))
					Cam = bvp.bvpCamera(location=cPos[FR[0]-1:FR[1]],fixPos=fPos[FR[0]-1:FR[1]],frames=fr[FR[0]-1:FR[1]])
					fPath = '%s_%s_p%d_res%d_f%09d/vox%s'%(Obj.semanticCat[0],Obj.grpName,pNum,nGrid,d*maxFilesPerDir,'#'*len(str(nGrid**3)))
					ScnL.append(bvp.bvpScene(Num=ObCt,Obj=(Obj,),BG=BG,Sky=Sky,
										Shadow=None,Cam=Cam,FrameRange=FR,
										fPath=fPath))
			# Convert list of scenes to SceneList	
			SL = bvp.bvpSceneList(ScnList=ScnL,RenderOptions=RO)
			#return SL
			jIDs = SL.RenderSlurm(RenderGroupSize=1,RenderType=('Voxels',),Is_Overwrite=True)
			ConcatCmd = """import bvp,pickle,os
fD = '{fD}'
vox = bvp.utils.math.concatVoxels(fD)
sName = fD+'.pik'
bvp.utils.basics.savePik(vox,sName)
for f in os.listdir(fD): os.unlink(os.path.join(fD,f))
os.rmdir(fD)
			"""
			cjIDs = []
			for jID,S in zip(jIDs,ScnL):
				DepStr = 'afterok:%s'%jID # Dependencies for job
				fD,xx = S.fPath.split('/') # last part of filepath from scene
				fD = RO.BVPopts['BasePath']%fD
				cjID = bvp.utils.basics.pySlurm(ConcatCmd.format(fD=fD),dep=DepStr,memory=2000,)
				cjIDs.append(cjID)
				# Up priority... (base is 5000 as of 2012.12.31)
				subprocess.call(['sudo','scontrol','update','jobID='+jID,'Priority=5010'])
			# Final concatenation and clean-up
			ConcatAllCmd = """import bvp,os
import numpy as np
I = np.zeros({res}**3)
fD = "{fD}"
fNm = sorted([os.path.join(fD,f) for f in os.listdir(fD) if 'pik' in f and "{key}" in f])
for f in fNm:
	I+=np.array(bvp.utils.basics.loadPik(f))
I = bvp.utils.basics.MakeBlenderSafe(I,'float')
sName = os.path.join(fD,"{key}"+".pik")
bvp.utils.basics.savePik(I,sName)
for f in fNm:
	os.unlink(f)
"""
			DepStr = ('afterok'+':%s'*len(cjIDs))%tuple(cjIDs) # Depends on all other concat jobs
			fD,key = os.path.split(fD)
			key = key[:-11] # Cut "_f000000000" part
			bvp.utils.basics.pySlurm(ConcatAllCmd.format(res=nGrid,fD=fD,key=key),dep=DepStr,memory=2000,)
		#SL.Render(RenderGroupSize=1,RenderType=Type)
		# Set up secondary slurm job to concatenate all voxelization images to t/f voxels.

	def RenderBGs(self,subCat=None,dummyObjects=(),nCamLoc=5,Is_Overwrite=False):
		'''
		Render (all) backgrounds in bvpLibrary to folder <LibDir>/Images/Backgrounds/<category>_<grpName>.png

		subCat = None #lambda x: x['grpName']=='BG_201_mHouse_1fl_1' #None #'outdoor'		
		dummyObjects = ['*human','*artifact','*vehicle']
		'''
		RO = bvp.RenderOptions()
		RO.BVPopts['BasePath'] = os.path.join(self.LibDir,'Images','Backgrounds','%s')
		RO.resolution_x = RO.resolution_y = 256 # smaller images
		if subCat:
			ToRender = self.getSCL(subCat,'backgrounds')
		else:
			ToRender = self.backgrounds # all backgrounds
		# Frame count
		frames = (1,1)
		# Get dummy objects to put in scenes:
		# Misc Setup
		BGCt = 0;
		ScnL = []
		for bg in ToRender:
			BGCt+=1
			# Create Scene
			BG = bvp.bvpBG(bgID=bg['grpName'],Lib=self)
			ObL = []
			for o in dummyObjects:
				ObL.append(bvp.bvpObject(obID=o,Lib=self,size3D=None))

			for p in range(nCamLoc):
				cNum = p+1
				fPath = '%s_%s_cp%02d_fr##'%(BG.semanticCat[0],BG.grpName,cNum)
				fChk = RO.BVPopts['BasePath']%fPath.replace('##','01.'+RO.image_settings['file_format'].lower())
				print('Checking for file: %s'%(fChk))
				if os.path.exists(fChk) and not Is_Overwrite:
					print('Found it!')
					# Only append scenes to render that DO NOT have previews already rendered!
					continue				
				Cam = bvp.bvpCamera(location=BG.camConstraints.sampleCamPos(frames),fixPos=BG.camConstraints.sampleFixPos(frames),frames=frames)
				Sky = bvp.bvpSky('*'+BG.skySemanticCat[0],Lib=self)
				if Sky.semanticCat:
					if 'dome' in Sky.semanticCat:
						if len(Sky.lightLoc)>1:
							Shad=None
						elif len(Sky.lightLoc)==1:
							if 'sunset' in Sky.semanticCat:
								Shad = bvp.bvpShadow('*west',self)
							else:
								fn = lambda x: 'clouds' in x['semanticCat'] and not 'west' in x['semanticCat']
								Shad = bvp.bvpShadow(fn,self)
						else:
							Shad=None
				else:
					Shad = None

				S = bvp.bvpScene(Num=BGCt,BG=BG,Sky=Sky,Obj=None,
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
		SL = bvp.bvpSceneList(ScnList=ScnL,RenderOptions=RO)
		SL.RenderSlurm(RenderGroupSize=nCamLoc)
	def RenderSkies(self,subCat=None,Is_Overwrite=False):
		'''
		Render (all) skies in bvpLibrary to folder <LibDir>/LibBackgrounds/<category>_<grpName>.png

		subCat = None # lambda x: 'dome' in x['semanticCat']
		'''
		raise Exception('Not done yet!')
		RO = bvp.RenderOptions()
		RO.BVPopts['BasePath'] = os.path.join(self.LibDir,'Images','Skies','%s')
		RO.resolution_x = RO.resolution_y = 256 # smaller images
		if subCat:
			ToRender = self.getSCL(subCat,'backgrounds')
		else:
			ToRender = self.backgrounds # all backgrounds
		# Frame count
		frames = (1,1)
		# set standard lights (Sky)
		Sky = bvp.bvpSky()
		# Get dummy objects to put in scenes:
		ObL = []
		for o in dummyObjects:
			ObL.append(bvp.bvpObject(obID=o,Lib=self,size3D=None))
		# Misc Setup
		BGCt = 0;
		ScnL = []
		for bg in ToRender:
			BGCt+=1
			# Create Scene
			BG = bvp.bvpBG(bgID=bg['grpName'],Lib=self)
			for p in range(nCamLoc):
				cNum = p+1
				fPath = '%s_%s_cp%d_fr##'%(BG.semanticCat[0],BG.grpName,cNum)
				fChk = RO.BVPopts['BasePath']%fPath.replace('##','01.'+RO.file_format.lower())
				print('Checking for file: %s'%(fChk))
				if os.path.exists(fChk) and not Is_Overwrite:
					print('Found it!')
					# Only append scenes to render that DO NOT have previews already rendered!
					continue				
				Cam = bvp.bvpCamera(location=BG.camConstraints.sampleCamPos(frames),fixPos=BG.camConstraints.sampleFixPos(frames),frames=frames)
				S = bvp.bvpScene(Num=BGCt,BG=BG,Sky=Sky,Obj=None,
									Shadow=None,Cam=Cam,FrameRange=(1,1),
									fPath=fPath,
									FrameRate=15)
				#try:
					# Allow re-set of camera position with each attempt to populate scene
				S.PopulateScene(ObL,ResetCam=True)
				#except:
				#	print('Unable to populate scene %s!'%S.fPath)
				ScnL.append(S)
		# Convert list of scenes to SceneList	
		SL = bvp.bvpSceneList(ScnList=ScnL,RenderOptions=RO)
		SL.RenderSlurm(RenderGroupSize=nCamLoc)
	def CreateSolidVol(self,obj=None,vRes=96,buf=4):
		'''
		Searches for extant .voxverts files in <LibDir>/Objects/VOL_Files/, and from them creates 
		3D, filled object mask matrices
		Saves this voxelized verison of an object as a .vol file in the <LibDir>/Objects/VOL_Files/ directory.

		Can not be called from inside Blender, since it relies on numpy

		Volume for voxelized object mask is vRes+4 (usually 96+4=100) to allow for a couple voxels' worth
		of "wiggle room" for imprecise scalings of objects (not all will be exactly 10 units - that part
		of object creation is manual and can be difficult to get exactly right)
		
		Voxelizations are used to create shape skeletons in subsequent processing. 

		Since the voxelized mesh surfaces of objects qualifies as meta-data about the objects, 
		this function might be expected to be a method of the RenderOptions class. However, this 
		isn't directly used by any models (yet); thus it has been saved in a separate place, as 
		the data about real-world size, number of mesh vertices, etc.

		'''
		# Imports
		import re,os
		from scipy.ndimage.morphology import binary_fill_holes as imfill # Fills holes in multi-dim images
		
		if not obj:
			obj = self.objects
		for o in obj:
			# Check for existence of .verts file:
			ff = '%s_%s.%dx%dx%d.verts'%(o['semanticCat'][0].capitalize(),o['grpName'],vRes+buf,vRes+buf,vRes+buf*2)
			fNm = os.path.join(bvp.Settings['Paths']['LibDir'],'Objects','VOL_Files',ff)
			if not os.path.exists(fNm):
				if bvp.Verbosity_Level>3:
					print('Could not find .verts file for %s'%o['grpName'])
					print('(Searched for %s'%fNm)
				continue
			# Get voxelized vert list
			with open(fNm,'r') as fid:
				Pt = fid.readlines()
			vL = bvp.np.array([[float(x) for x in k.split(',')] for k in Pt])
			# Get dimensions 
			dim = [len(bvp.np.unique(vL.T[i])) for i in range(3)]
			# Create blank matrix
			z = bvp.np.zeros((vRes+buf,vRes+buf,vRes+buf*2),dtype=bool)
			# Normalize matrix to indices for volume
			vLn = vL/(10./vRes) -.5 + buf/2. # .5 is a half-voxel shift down
			vLn.T[0:2]+= vRes/2. # Move X,Y to center
			vLn.T[2] += buf/2. # Move Z up (off floor) by "buf"/2 again
			# Check for closeness of values to rounded values
			S = bvp.np.sqrt(bvp.np.sum((bvp.np.round(vLn)-vLn)**2))/len(vLn.flatten())
			if S>.001:
				raise Exception('Your voxelized coordinates do not round to whole number indices!')
			# Index into volume
			idx = bvp.np.cast['int'](bvp.np.round(vLn))
			z[tuple(idx.T)] = True
			# Fill holes w/ python 
			# May need fancier strel (structure element - 2nd argumnet) for some objects 
			hh = imfill(z)
			# Trim?? for more efficient computation? 
			# ?
			# Save volume in binary format for pfSkel (or other) code:
			PF = o['parentFile']
			fDir = os.path.split(PF)[0]
			Cat = re.search('(?<=Category_)[^_^.]*',PF).group()
			Res = '%dx%dx%d'%(vRes+buf,vRes+buf,vRes+buf+buf)
			fName = os.path.join(fDir,'VOL_Files',Cat+'_'+o['grpName']+'.'+Res+'.vol')
			# Write to binary file
			print('Saving %s'%fName)
			with open(fName,'wb') as fid:
				hh.T.tofile(fid) # Transpose to put it in column-major form...
			# Done with this object!
	# # shortcut names
	# getSCL = getSceneComponentList
	# getSC = getSceneComponent

	# @property
	# def nObjects(self):
	# 	return len(self.objects)
	# @property
	# def nObjectsCountPoses(self):
	# 	nOb = 0
	# 	for o in self.objects:
	# 		if o['nPoses']:
	# 			nOb+=o['nPoses']
	# 		else:
	# 			nOb+=1
	# 	return nOb
	# @property
	# def nBGs(self):
	# 	return len(self.backgrounds)
	# @property
	# def nSkies(self):
	# 	return len(self.skies)
	# @property
	# def nShadows(self):
	# 	return len(self.shadows)
