'''
NOTES: 
TO DO 
* See http://western-skies.blogspot.com/2008/02/simple-complete-example-of-python.html for __getstate__() and __setstate__() methods
* ADD PRINT METHOD TO SHOW ALL OPTIONS
* BETTER HELP
* Implement choosing objects per scene as a matrix (This whole process is rather shoddy - still not general enough)

For now, each different pose of an object is treated as a different object. Thus object poses will have to be redone if/when we decide to animate things. For now (2011.12.01), only humans have poses (though there are some animals / small artifacts with armatures). Each human must have a pose library with the same number of poses, for now (see "nPoses" variable below)

There is an annoying tradeoff between which parameters can be specified a priori, and which must depend on the other elements in a scene. 


'''

# Imports
import subprocess,bvp,math,os,pickle,copy,time,re
from bvp.utils.blender import GetGroups
from bvp.utils.basics import GetHostName,MakeBlenderSafe,loadPik,savePik,fixedKeyDict
# For convenience
np = bvp.np
pickle = bvp.pickle
# If we're working in Blender
if not bvp.Is_Blender:
	from matplotlib import pyplot as plt

class bvpSceneList(object):
	'''
	List of scenes. Potentially, a stimulus set for an experiment,  a few scenes for a demo, etc.
	'''
	def __init__(self,ScnList=None,ScnConstr=None,FrameRate=15.,RenderOptions=None,Name='SceneList'):
		'''
		Usage: ScnList = bvpSceneList(ScnListParams)
		
		A list of class "bvpScene" instances. Potentially, a stimulus set for an experiment,  a few scenes for a demo, etc.
		
		Fields to set:
		Minutes
		Seconds
		nScenes *NOT a property!
		sPerScene
		FrameRate *Overrides scene frame rates

		'''
		# Process inputs:
		if not ScnList:
			self.ScnList = []
		else:
			self.ScnList = ScnList
		self.Name = Name
		self.ScnConstr = ScnConstr # Un-used!
		self.RenderOptions=RenderOptions
		# Timing
		self.FrameRate = 15.
		# Other??		
	def __repr__(self):
		S = '<Class BVP scene list: > \n' # Add name??
		S += '%s:\n%d scenes, %d min, %.2f s \n'%(self.Name,self.nScenes,self.MinSec[0],self.MinSec[1])
		return S
	def __add__(self,ScnOrList):
		'''
		Addition method for lists. Adds on new scenes (either a bvpSceneList or a single bvpScene).
		Name and render options of the FIRST argument are kept 
		'''
		if type(ScnOrList) is bvp.bvpScene:
			self.ScnList+=[ScnOrList]
			return self
		elif type(ScnOrList) is bvp.bvpSceneList:
			self.ScnList+=ScnOrList.ScnList
			return self
	@property
	def nScenes(self):
		return(len(self.ScnList))
	@property
	def Seconds(self):
		return sum(self.nFramesPerScene) / float(self.FrameRate)
	@property
	def Minutes(self):
		return self.Seconds/60.
	@property
	def MinSec(self):
		return divmod(self.Seconds,60)
	@property
	def sPerScene(self):
		return [s/self.FrameRate for s in self.nFramesPerScene]
	@property
	def nObjPerScene(self):
		return [s.nObjects for s in self.ScnList]
	@property
	def nFramesPerScene(self):
		return [s.ScnParams['frame_end']-s.ScnParams['frame_start']+1 for s in self.ScnList]
	@property
	def IncompleteScenes(self):
		try:
			Inc = [iS for iS,s in enumerate(self.ScnList) if not s.Obj[0].pos3D]
		except IndexError:
			print('your scene list is wonky... no objects!')
			Inc = []
		if any(Inc):
			return Inc
		else:
			print('All scenes are complete!')
			return None
	def Save(self,fName=None):
		"""
		Save scenelist to fName (pickle file, usu. "SceneList.pik") 
		Defaults to <SceneList>.RenderOptions.BVPopts['BasePath'].replace('Scenes/%s','SceneList.pik')
		"""
		if not fName:
			fName = self.RenderOptions.BVPopts['BasePath'].replace('Scenes/%s','SceneList.pik')
		savePik(self,fName)
	def getCamVector(self):
		"""
		Return a list of 3-tuples of Camera -> Fixation vectors
		"""
		CamVec = []
		for S in self.ScnList:
			for fr in Cam.frames():
				cVec = [c-f for c,f in zip(Cam.fixation,Cam.location)]
				
			CatMat += [ScCat for x in range(int((S.ScnParams['frame_end']-S.ScnParams['frame_start']+1)))]

	def getSemanticCatMatrix(self,CatType='8',Leaves=None):
		'''
		Return a matrix of categories
		CatType can be "8" or "BasicLevel" as of 2012.08.24
		'''
		C = []
		if CatType=='8':
			for S in self.ScnList:
				for O in S.Obj:
					C.append(O.semanticCat[0].lower())
			Cats,nExemplars = bvp.utils.basics.unique(C)
			CatMat = []
			for S in self.ScnList:
				ScCat = [False]*len(Cats)
				for O in S.Obj:
					ScCat[Cats.index(O.semanticCat[0].lower())] = True
				CatMat += [ScCat for x in range(int((S.ScnParams['frame_end']-S.ScnParams['frame_start']+1)))]
		elif CatType=='BasicLevel':
			# Should be done on LIBRARY basic level cats to assure no difference btw. scene lists
			Lib = bvp.bvpLibrary() # modify??
			Cat,nOcc = bvp.utils.basics.unique([o['basicCat'].lower() for o in Lib.objects if o['basicCat']])
			Cat.sort()
			CatMat = []
			for S in self.ScnList:
				ScCat = [False]*len(Cat)
				for O in S.Obj:
					if O.basicCat:
						ScCat[Cat.index(O.basicCat.lower())] = True
				CatMat += [ScCat for x in range(int((S.ScnParams['frame_end']-S.ScnParams['frame_start']+1)))]
		elif CatType=='Hierarchical':
			Lib = bvp.bvpLibrary()
			oCat = []
			for o in Lib.objects: 
				if o:
					oCat+=[oo.lower() for oo in o['semanticCat']]
			Cat,nOcc = bvp.utils.basics.unique(oCat)
			# Hacky: Add special cats. For all dictionary entries, the key (string) will 
			# be added to the (front of the) semantic category list for an object if that
			# list contains any of the strings in the list (dictionary values)
			Cat+=['animate','inanimate']
			CatAdd = dict(animate=['animal','human','plant'], # inanimate = !animate
							inanimate=['building','artsm','artlg','geometrical','vehicle'],
							animal=['human'],
							artlg=['vehicle','building','geometrical'],
							)
			CatMat = []
			for S in self.ScnList:
				ScCat = [False]*len(Cat)
				for O in S.Obj:
					if O.semanticCat:
						for sc in O.semanticCat:
							ScCat[Cat.index(sc.lower())] = True
							# Additional categories: 
							for k,v in CatAdd.items():
								if sc in v:
									ScCat[Cat.index(k.lower())] = True
				CatMat += [ScCat for x in range(int((S.ScnParams['frame_end']-S.ScnParams['frame_start']+1)))]
		elif CatType=='HighLevel':
			Lib = bvp.bvpLibrary()
			# Define leaves of category tree minimum level of specificity for categories (this is hard-coded & somewhat arbitrary!)
			# Re-define these as input??
			if Leaves is None:
				# Note: first match will abort search for matches.
				Leaves = ['human', # humans
						'fish','creeper','bird','land mammal','reptile','animal', # animals
						'bush','tree','food','plant',# plants
						'building', # buildings
						'geometrical', # nonsense
						'tool','weapon','artsm',# artsm
						'aircraft','auto','boat','vehicle', # vehicle
						'furniture','outdoor','artlg' # artlg
						]
			# Hacky: Add special cats. For all dictionary entries, the key (string) will 
			# be added to the (front of the) semantic category list for an object if that
			# list contains any of the strings in the list (dictionary values)
			Cat = Leaves+['animate','inanimate']
			CatAdd = dict(animate=['animal','human','plant'], # inanimate = !animate
							inanimate=['building','artsm','artlg','geometrical','vehicle'],
							animal=['human'],
							artlg=['vehicle','building','geometrical'],
							)
			CatMat = []
			for S in self.ScnList:
				ScCat = [False]*len(Cat)
				# Object categories
				for O in S.Obj:
					if O.semanticCat:
						for sc in O.semanticCat:
							if sc in Cat:
								ScCat[Cat.index(sc.lower())] = True
							# Additional categories: 
							for k,v in CatAdd.items():
								if sc in v:
									ScCat[Cat.index(k.lower())] = True
				CatMat += [ScCat for x in range(int((S.ScnParams['frame_end']-S.ScnParams['frame_start']+1)))]
		elif CatType=='Backgrounds':
			# BG categories
			if Leaves is None:
				Leaves = ['indoor','outdoor','open','closed','partlyopen','buildings','hills','flat','room','hall']
			Cat = Leaves
			CatMat = []
			for S in self.ScnList:
				ScCat = [False]*len(Cat)
				if S.BG.semanticCat:
					for sc in S.BG.semanticCat:
						if sc in Cat:
							ScCat[Cat.index(sc.lower())] = True
				CatMat += [ScCat for x in range(int((S.ScnParams['frame_end']-S.ScnParams['frame_start']+1)))]
		elif CatType=='Skies':
			# BG categories
			if Leaves is None:
				Leaves = ['day','night','sunset','partly cloudy','sunny','stars','colors']
			Cat = Leaves
			CatMat = []
			for S in self.ScnList:
				ScCat = [False]*len(Cat)
				if S.Sky.semanticCat:
					for sc in S.Sky.semanticCat:
						if sc in Cat:
							ScCat[Cat.index(sc.lower())] = True
				CatMat += [ScCat for x in range(int((S.ScnParams['frame_end']-S.ScnParams['frame_start']+1)))]
		elif CatType=='HierarchicalObjBGSky':
			CMo,Co = self.getSemanticCatMatrix('HighLevel')
			CMb,Cb = self.getSemanticCatMatrix('Backgrounds')
			CMs,Cs = self.getSemanticCatMatrix('Skies')
			CatMat = [a+b+c for a,b,c in zip(CMo,CMb,CMs)]
			Cat = Co+Cb+Cs
		return CatMat,Cat
	def Update(self,RaiseError=False):
		'''
		Assure that all objects / backgrounds are up-to-date with library files (semantic cats, real world size, etc.)
		Optionally, raise an error if the "grpName" (unique string designating each object) has changed in the bvpLibrary
		since scene list creation.
		'''
		Lib = bvp.bvpLibrary()
		Fail=False
		for iS,S in enumerate(self.ScnList):
			# Objects
			for iO,O in enumerate(S.Obj):
				try:
					N = bvp.bvpObject(O.grpName,Lib)
					self.ScnList[iS].Obj[iO].semanticCat = N.semanticCat
					self.ScnList[iS].Obj[iO].realWorldSize = N.realWorldSize
				except:
					Fail=True
					print('Update failed because grpName has been changed for scene %d object %s!\nNeeds to be manually updated!'%(iS,O.grpName))
			# Background
			try:
				N = bvp.bvpBG(S.BG.grpName,Lib)
				self.ScnList[iS].BG.semanticCat = N.semanticCat
				self.ScnList[iS].BG.realWorldSize = N.realWorldSize
			except:
				Fail=True
				print('Update failed because grpName has been changed for scene %d background %s! Needs to be manually updated!'%(iS,S.BG.grpName))
			# Skies
			try:
				N = bvp.bvpSky(S.Sky.grpName,Lib)
				self.ScnList[iS].Sky.semanticCat = N.semanticCat
				self.ScnList[iS].Sky.realWorldSize = N.realWorldSize
			except:
				if S.Sky.grpName is not None:
					Fail=True
					print('Update failed because grpName has been changed for scene %d sky %s! Needs to be manually updated!'%(iS,S.Sky.grpName))
		# Update render options
		if hasattr(self.RenderOptions,'file_format'):
			# Assume both need changing:
			self.RenderOptions.image_settings = {'file_format':self.RenderOptions.file_format,'color_mode':self.RenderOptions.color_mode}
			# Get rid of old ones
			self.RenderOptions.__delattr__('file_format')
			self.RenderOptions.__delattr__('color_mode')

		if Fail and RaiseError:
			raise Exception('One or more objects need manual updating!')

	def PlotImagePos(self,ScnIdx=None):
		'''
		Plots image positions of objects in all scenes
		'''
		if not ScnIdx:
			ScnIdx = range(self.nScenes)
		for Ct,Scn in enumerate(self.ScnList):
			if Ct in ScnIdx:
				for O in Scn.Obj:
					plt.plot(O.pos2D[0],O.pos2D[1],'k.',alpha=.5)
		# Assumes image size!
		plt.xlim((0,1))
		plt.ylim((1,0))
		plt.show()
	def Render(self,RenderType=('Image',),RenderGroupSize=1,memory=7700):
		'''
		Renders locally, calling this machine. Blender is closed and re-opened after RenderGroupSize scenes.
		This is an easy way to prevent Blender from 

		WARNING: Can go for a LONG time with big render jobs! Only recommended for one scene at a time! 
		
		This function writes three different kinds of temporary files associated with the render job:
		
		(1) a pickle (saved as .pik) file ("SLpickleFile" variable below)
		(2) a python script to read in and do the rendering ("BlenderPyFile" variable below). Two lines written into this file determine (a) the pickled scene list file to load, and (b) the portion or chunk of the scene list to render for each job
		(3) a shell script that calls blender with each chunk's python script
		
		'''
		# General set-up:
		Blender = bvp.Settings['Paths']['BlenderCmd']
		BlendFile = os.path.join(bvp.__path__[0],'BlendFiles','Blank.blend')
		nCPUs = '2'
		nChunks = int(math.ceil(float(self.nScenes)/RenderGroupSize))
		# This string should be used to specify (masks, zdepth, contours, etc) 
		if 'LogFileAdd' in self.RenderOptions.BVPopts:
			LogAdd = self.RenderOptions.BVPopts['LogFileAdd']
		else:
			LogAdd = '' #self.RenderOptions.BVPopts['LogFileAdd']		
		for x in ['Image','Clay','ObjectMasks','Zdepth','Contours','Normals']:
			self.RenderOptions.BVPopts[x] = x in RenderType
			if x in RenderType:
				LogAdd += '_'+x
		if 'Test' in RenderType:
			if len(RenderType)>2 and not "Image" in RenderType:
				raise Exception("I'm still too stupid to handle test renders of depth, normals, etc")
			elif len(RenderType)==1 and not "Image" in RenderType:
				RenderType = ("Test","Image")
			# Keep original values to re-set later:
			resPctOrig  = copy.copy(self.RenderOptions.resolution_percentage)
			# Set render options for test render
			self.RenderOptions.resolution_percentage = 50 
			self.RenderOptions.BVPopts['BasePath'] = self.RenderOptions.BVPopts['BasePath'].replace('Scenes','Test')
			self.RenderOptions.BVPopts['Type'] = 'FirstAndLastFrame' #'FirstFrame'

		# Creation of temporary files
		# Pre: set up temp directory
		BaseDir = os.path.dirname(os.path.split(self.RenderOptions.BVPopts['BasePath'])[0])
		if not os.path.exists(BaseDir):
			os.mkdir(BaseDir)
		# -> (write slurm output here too???)
		# -> Make specific date??? No - there should only be one for each stim set, right...?
		if not os.path.exists(os.path.join(BaseDir,'Log')):
			os.mkdir(os.path.join(BaseDir,'Log'))
		
		# (1) Save scene list as a temporary pickle file to be loaded by the RenderFile
		# Save scene list as a temporary pickle file to be loaded by the RenderFile
		rName = 'ScnListRender_%s%s_%s'%(self.Name,LogAdd,time.strftime('%Y%m%d_%H%M%S'))
		SLpickleFile = os.path.join(BaseDir,'Log',rName+'.pik') 
		with open(SLpickleFile,'wb') as fid:
			pickle.dump(self,fid,protocol=2)
		# (2,3) Setup: 
		BlenderPyFileBase = self.RenderOptions.BVPopts['RenderFile']
		# Get this file into a list: 
		with open(BlenderPyFileBase,'r') as fid:
			RenderScript = fid.readlines()
		# Set up first of two lines to print into temp file:
		FileToLoadLine = "TempFile = '%s'\n"%SLpickleFile #os.path.join(bvp.__path__[0],'Scripts','CurrentRender.pik')
		
		for x in range(nChunks):
			ScnToRenderLine = 'ScnToRender = range(%d,%d)\n'%(x*RenderGroupSize,min([(x+1)*RenderGroupSize,self.nScenes]))
			InsertLine1 = RenderScript.index('### --- REPLACE 1 --- ###\n')+1
			InsertLine2 = RenderScript.index('### --- REPLACE 2 --- ###\n')+1
			RenderScript[InsertLine1] = FileToLoadLine
			RenderScript[InsertLine2] = ScnToRenderLine
			ChunkfNm = '%s_chunk%03d.py'%(rName,x+1)
			BlenderPyFile = os.path.join(BaseDir,'Log',ChunkfNm) # Add datestr to "Log" ? 
			with open(BlenderPyFile,'w') as fid:
				fid.writelines(RenderScript)
			# Create & call slurm script for this chunk
			#TempScriptName = os.path.join(BaseDir,'Log','BlenderRenderTmp_chunk%03d.sh'%(x+1))
			#BlenderCmd = Blender+' -b '+BlendFile+' -P '+BlenderPyFile+' --mem '+str(memory) # Specify output? stdout? File?
			BlenderCmd = [Blender,'-b',BlendFile,'-P',BlenderPyFile]
			subprocess.call(BlenderCmd)
	def RenderSlurm(self,RenderType=('Image',),RenderGroupSize=3,Is_Overwrite=False,memory=7700):
		'''
		Calls separate instances of Blender via Slurm to render the scene list. 
		
		Writes three different kinds of temporary files associated with the render job:
		
		(1) a pickle (saved as .pik) file ("SLpickleFile" variable below)
		(2) a python script to read in and do the rendering ("BlenderPyFile" variable below). Two lines written into this file determine (a) the pickled scene list file to load, and (b) the portion or chunk of the scene list to render for each job
		(3) a shell script for use by sbatch that calls blender with each chunk's python script
		
		Inputs: 
		RenderType = a tuple, with any of the following strings in it: 
			('Image','Clay'*,'ObjectMasks','Zdepth','Contours'*,'Normals')
			* Not working yet!
		RenderGroupSize = <int>, number of scenes to render in a single job. A scene can be an arbitrary number of frames (usu. ~50)
		Is_Overwrite = True/False, option as to whether to over-write extant files (True) or skip files that are already rendered (False). 
		memory = maximum memory required for the job (in MB). This is a bit difficult to estimate... Aim high!
		ML 2011.??
		'''

		''' 
		For error messages:
		 -e, --error=<filename pattern>
              Instruct SLURM to connect the batch script's standard error directly to the file name specified in the "filename pattern".  See the --input option for filename specification options.
        '''
		### --- General set-up: --- ###
		Blender = bvp.Settings['Paths']['BlenderCmd'] #'/Applications/Blender/FreestyleBranch_r37828_32bit/blender.app/Contents/MacOS/blender'
		BlendFile = os.path.join(bvp.__path__[0],'BlendFiles','Blank.blend')
		nCPUs = '2'
		### --- Set type of render --- ###
		# Keep original render options for re-set at end:
		BVPoptOrig = copy.copy(self.RenderOptions.BVPopts)
		if 'LogFileAdd' in self.RenderOptions.BVPopts:
			LogAdd = self.RenderOptions.BVPopts['LogFileAdd']
		else:
			LogAdd = '' #self.RenderOptions.BVPopts['LogFileAdd']		

		for x in ['Image','Clay','ObjectMasks','Zdepth','Contours','Normals','Voxels']:
			self.RenderOptions.BVPopts[x] = x in RenderType
			if x in RenderType:
				LogAdd += '_'+x
		if 'Test' in RenderType:
			if len(RenderType)>2 and not "Image" in RenderType:
				raise Exception("I'm still too stupid to handle test renders of depth, normals, etc")
			elif len(RenderType)==1 and not "Image" in RenderType:
				RenderType = ("Test","Image")
			# Keep original values to re-set later:
			resPctOrig  = copy.copy(self.RenderOptions.resolution_percentage)
			# Set render options for test render
			self.RenderOptions.resolution_percentage = 50 
			self.RenderOptions.BVPopts['BasePath'] = self.RenderOptions.BVPopts['BasePath'].replace('Scenes','Test')
			self.RenderOptions.BVPopts['Type'] = 'FirstAndLastFrame' #'FirstFrame'
		### --- Creation of temporary files --- ###
		# Pre: set up temp directory
		BaseDir = os.path.dirname(os.path.split(self.RenderOptions.BVPopts['BasePath'])[0])
		if bvp.Verbosity_Level > 3: 
			print('I think the base directory is :\n%s'%BaseDir)
		if not os.path.exists(BaseDir):
			os.mkdir(BaseDir)
			if bvp.Verbosity_Level > 3:
				print('made base dir!')
		if bvp.Verbosity_Level > 3:
			print('I think the log directory is :\n%s'%os.path.join(BaseDir,'Log'))
		if not os.path.exists(os.path.join(BaseDir,'Log')):
			os.mkdir(os.path.join(BaseDir,'Log'))
			if bvp.Verbosity_Level > 3:
				print('made log dir!')
		### --- [optionally] Cull list to remove already-rendered files --- ### 
		if not Is_Overwrite:
			# Set up path to check
			if 'Image' in RenderType:
				BP = self.RenderOptions.BVPopts['BasePath']
			else:
				# Check only one type of output! There is no option to ONLY overwrite scenes of one type
				BP = self.RenderOptions.BVPopts['BasePath'].replace('Scenes',RenderType[0])
				if 'ObjectMasks' in BP:
					BP = BP.replace('ObjectMasks','Masks')
			# Get files in that path
			if os.path.exists(os.path.dirname(BP.strip('%s'))):
				fNm = os.listdir(os.path.dirname(BP))
			else:
				fNm = [] # no files rendered yet if there's no directory!
			ToKill = []
			# Loop through scenes to see what has been rendered:
			for iS,S in enumerate(self.ScnList):
				# Create list of file names to be rendered:
				n = sum([x=='#' for x in S.fPath])
				ss = '%0'+str(n)+'d'
				stFr = int(S.FrameRange[0])
				finFr = int(S.FrameRange[-1])
				nn = 1
				if self.RenderOptions.BVPopts['Type']=='FirstFrame':
					finFr = stFr
				elif self.RenderOptions.BVPopts['Type']=='every4th':
					while not stFr%4==1:
						stFr+=1
					nn = 4
				### ---- 
				frNum = range(stFr,finFr+1,nn)
				doneFr = 0
				for fr in frNum:
					fToRender = S.fPath.replace('#'*n,ss)%fr
					if 'ObjectMasks' in RenderType:
						if any([(fToRender in x) and ('m01' in x) for x in fNm]):
							# File found!
							doneFr = copy.copy(fr)
					else:
						if any([fToRender in x for x in fNm]):
							# File found!
							doneFr = copy.copy(fr)
							self.ScnList[iS].FrameRange = (max([stFr,doneFr,1]),finFr)
							RenderMe = False
						else:
							RenderMe = True
							break
				if not RenderMe:
					# All files have been found!
					print('Cropping scene %d!'%S.Num)
					ToKill.append(iS)
				# ### ----
				# fToRender = [S.fPath.replace('#'*n,ss)%fr for fr in frNum]
				# # Do not re-render them if they have already been rendered!
				# nRendered = sum([fP in x for x in fNm for fP in fToRender])
				# if 'ObjectMasks' in RenderType:
				# 	nRendered = sum([(fP in x) and ('m01' in x) for x in fNm for fP in fToRender])
				# if nRendered >= S.ScnParams['frame_end']:
				# 	print('Cropping scene %d!'%S.Num)
				# 	# All done with this scene!
				# 	ToKill.append(self.ScnList.index(S))
				# elif nRendered>1 and self.RenderOptions.BVPopts['Type']=='FirstFrame':
				# 	ToKill.append(self.ScnList.index(S))
				# else:
				# 	I = self.ScnList.index(S)
				# 	self.ScnList[I].FrameRange = (self.ScnList[I].FrameRange[0]+nRendered,self.ScnList[I].FrameRange[1])
			#1/0
			self.ScnList = [self.ScnList[i] for i in range(self.nScenes) if not i in ToKill]
		nChunks = int(math.ceil(float(self.nScenes)/RenderGroupSize))
		# Save scene list as a temporary pickle file to be loaded by the RenderFile
		rName = 'ScnListRender_%s%s_%s'%(self.Name,LogAdd,time.strftime('%Y%m%d_%H%M%S'))
		SLpickleFile = os.path.join(BaseDir,'Log',rName+'.pik') 
		savePik(self,SLpickleFile)
		# Set up text files to be loaded in the render process 
		BlenderPyFileBase = self.RenderOptions.BVPopts['RenderFile']
		# Get this file into a list: 
		with open(BlenderPyFileBase,'r') as fid:
			RenderScript = fid.readlines()
		# Set up first of two lines to print into temp file:
		FileToLoadLine = "TempFile = '%s'\n"%SLpickleFile #os.path.join(bvp.__path__[0],'Scripts','CurrentRender.pik')
		jobIDs = []
		for x in range(nChunks):
			if x == nChunks-1:
				Ch,Leftovers = divmod(self.nScenes,nChunks)
				if Leftovers:
					RenderTo=Leftovers
				else:
					RenderTo=RenderGroupSize
			else:
				RenderTo=RenderGroupSize
			ScnToRenderLine = 'ScnToRender = range(%d,%d)\n'%(x*RenderGroupSize,x*RenderGroupSize+RenderTo)
			InsertLine1 = RenderScript.index('### --- REPLACE 1 --- ###\n')+1
			InsertLine2 = RenderScript.index('### --- REPLACE 2 --- ###\n')+1
			RenderScript[InsertLine1] = FileToLoadLine
			RenderScript[InsertLine2] = ScnToRenderLine
			ChunkfNm = '%s_chunk%03d.py'%(rName,x+1)
			BlenderPyFile = os.path.join(BaseDir,'Log',ChunkfNm) # Add datestr to "Log" ? 
			with open(BlenderPyFile,'w') as fid:
				fid.writelines(RenderScript)
			# Create & call slurm script for this chunk
			TempScriptName = os.path.join(BaseDir,'Log','%s_chunk%03d.sh'%(rName,x+1))
			with open(TempScriptName,'wb') as fid:
				fid.write('#!/bin/sh\n')
				fid.write('#SBATCH\n')
				BlenderCmd = Blender+' -b '+BlendFile+' -P '+BlenderPyFile
				fid.write(BlenderCmd)
				# Cleanup (move to .done file instead?)
				#fid.write('rm '+BlenderPyFile) 
				#fid.write('rm '+TempScriptName) 
			SlurmOut = os.path.join(BaseDir,'Log','%s_chunk%03d_SlurmLog_hID=%%N'%(rName,x+1))
			#SlurmJob = "BVPrender_Chunk%03d"
			SlurmCmd = ['sbatch','-c',nCPUs,'-p','all','--mem',str(memory),'-o',SlurmOut,TempScriptName]
			#SlurmCmd = ['sbatch','-c',nCPUs,'-w','ibogaine',TempScriptName,'-o',SlurmOut]
			if bvp.Verbosity_Level>3:
				print('Calling:')
				print(SlurmCmd)
			stdOut = subprocess.check_output(SlurmCmd).decode('utf-8')
			jobID = re.search('(?<=Submitted batch job )[0-9]*',stdOut).group()
			jobIDs.append(jobID)
		# Re-set SceneList rendering options:
		self.RenderOptions.BVPopts = BVPoptOrig
		if 'Test' in RenderType:
			self.RenderOptions.resolution_percentage = resPctOrig
		# Done!
		print('Rendering has begun... Check slurm for progress!')
		return jobIDs
	def RenderCheck(self,rType='Scenes'):
		'''
		Check on render progress, show a bar graph of completion

		rType is the kind of render on which you wish to check ('Scenes','Zdepth','Normals',etc)

		'''
		if not bvp.Is_Numpy:
			raise Exception('Only works outside of Blender!')
		
		FP = copy.copy(self.RenderOptions.BVPopts['BasePath'])
		if FP[-2:]=='%s':
			FP = os.path.split(FP)[0]
		if not 'Scenes' in FP:
			raise Exception("I was kind of expecting 'Scenes' to be in your base rendering path. ..")
		FP = FP.replace('Scenes',rType)
		fNm = os.listdir(FP)
		n = []
		for S in self.ScnList:
			ScF = S.fPath.replace('##','')
			n.append(float(sum([ScF in f for f in fNm])))
			if rType=='Masks':
				n.pop()
				n.append(float(sum([(ScF in x) and ('m01' in x) for x in fNm])))

		tt = copy.copy(self.RenderOptions.BVPopts['Type'])
		if rType.lower=='test':
			tt = 'FirstFrame'
		if tt=='All':
			a = np.array(self.nFramesPerScene)
			Pct = n/a
		elif tt=='every4th':
			a = np.array(self.nFramesPerScene)
			Pct = n/a # This is still bogus for Counterstrike data, b/c scenes are not separately labeled
		else:
			Pct=n
		plt.barh(range(self.nScenes),Pct)
		if self.IncompleteScenes:
			plt.plot([0]*len(self.IncompleteScenes),self.IncompleteScenes,'ro')
		plt.ylim([0,self.nScenes])
		plt.xlim([0,1.1])
		plt.xlabel('Pct. complete')
		plt.ylabel('Scene')
		plt.title('Render progress: %s'%self.Name)
		plt.show()
