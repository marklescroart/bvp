'''
Constraints for a scene list
'''

from bvp.bvpConstraint import bvpConstraint

class bvpSLConstraint(bvpConstraint):
	'''
	Class to contain constraints for properties of a scene list
	
	Necessary??
	WTF, let's see (2012.03.06)
	'''
	def __init__(self):
				### def SetScenes():
		'''
		Computes concretely what will be in each scene and where. Commits probabilities into instances.
		'''
		pass
		"""

		Fields to set: 

		Minutes
		Seconds
		Scenes
		ScnList
		# Compute number of scenes / duration if not given
		# Build in check for inconsistencies?
		if not self.Minutes and not self.Seconds and not self.nScenes:
			raise Exception('Please specify either nScenes, Minutes, or Seconds')
		if not self.Minutes and not self.Seconds:
			self.Seconds = self.nScenes * self.sPerScene_mean
		if not self.Minutes:
			self.Minutes = self.Seconds / 60.
		if not self.Seconds:
			self.Seconds = self.Minutes * 60.
		if not self.nScenes:
			self.nScenes = MakeBlenderSafe(np.floor(self.Seconds / self.sPerScene_mean))

		self.nObjectsPerCat = [len(o) for o in self.Lib.objects.values()]
		# Special case for humans with poses:
		nPoses = 5
		# TEMP!
		#print('Pre-increase of human cat:')
		#print(self.nObjectsPerCat)
		Categories = self.Lib.objects.keys()
		if "Human" in Categories:
			hIdx = Categories.index("Human")
			self.nObjectsPerCat[hIdx] = self.nObjectsPerCat[hIdx] * nPoses
		self.nObjects = sum(self.nObjectsPerCat)
		# TEMP!
		#print('Post-increase of human cat:')
		#print(self.nObjectsPerCat)

		self.nBGsPerCat = [len(bg) for bg in self.Lib.bgs.values()]
		self.nBGs = sum(self.nBGsPerCat)

		self.nSkiesPerCat = [len(s) for s in self.Lib.skies.values()]
		self.nSkies = sum(self.nSkiesPerCat)

		# Frames and objects per scene will vary with the task in any given experiment... 
		# for now, this is rather simple (i.e., we will not try to account for every task we might ever want to perform)
		# Scene temporal duration
		self.nFramesPerScene = np.random.randn(self.nScenes)*self.sPerScene_std + self.sPerScene_mean
		self.nFramesPerScene = np.minimum(self.nFramesPerScene,self.sPerScene_max)
		self.nFramesPerScene = np.maximum(self.nFramesPerScene,self.sPerScene_min)
		# Note conversion of seconds to frames 
		self.nFramesPerScene = MakeBlenderSafe(np.round(self.nFramesPerScene * self.FrameRate))
		self.nFramesTotal = sum(self.nFramesPerScene)
		# Compute nFramesTotal to match Seconds exactly 
		while self.nFramesTotal < self.Seconds*self.FrameRate:
			self.nFramesPerScene[np.random.randint(self.nScenes)] += 1
			self.nFramesTotal = sum(self.nFramesPerScene)
		while self.nFramesTotal > self.Seconds*self.FrameRate:
			self.nFramesPerScene[np.random.randint(self.nScenes)] -= 1
			self.nFramesTotal = sum(self.nFramesPerScene)
		### --- Scene Objects --- ###
		# Set object count per scene
		self.nObjPerScene = np.round(np.random.randn(self.nScenes)*self.nObj_std + self.nObj_mean) #self.nScenes
		self.nObjPerScene = np.minimum(self.nObjPerScene,self.nObj_max)
		self.nObjPerScene = np.maximum(self.nObjPerScene,self.nObj_min)
		self.nObjPerScene = MakeBlenderSafe(self.nObjPerScene)
		# Set object categories per scene
		self.nObjectsUsed = MakeBlenderSafe(np.sum(self.nObjPerScene))
		
		# Get indices for objects, bgs, skies by category (imaginary part), exemplar (real part) 
		# ??? NOTE: These functions can be replaced with different functions to sample from object, background, or sky categories differently...
		if not self.obIdx:
			obIdx = self.MakeListFromLib(Type='Obj')
		else:
			obIdx = self.obIdx
		if not self.bgIdx:
			bgIdx = self.MakeListFromLib(Type='BG')
		else:
			bgIdx = self.bgIdx
		if not self.skyIdx:
			skyIdx = self.MakeListFromLib(Type='Sky')
		else:
			skyIdx = self.skyIdx
		
		### --- Get rendering options --- ###
		self.RenderOptions = RenderOptions(self.rParams)
		### --- Create each scene (make concrete from probablistic constraints) --- ###
		self.ScnList = []
		#print('Trying to create %d Scenes'%self.nScenes)
		for iScn in range(self.nScenes):
			# Get object category / exemplar number
			ScOb = []
			for o in range(self.nObjPerScene[iScn]):
				if bvp.Verbosity_Level > 3: print('Running object number %d'%o)
				# This is a shitty way to do this - better would be a matrix. Fix??
				ObTmp = obIdx.pop(0) 
				if bvp.Verbosity_Level > 3: print('CatIdx = %d'%ObTmp.imag)
				if bvp.Verbosity_Level > 3: print('ObIdx = %d'%ObTmp.real)
				Cat = self.Lib.objects.keys()[int(ObTmp.imag)]
				if bvp.Verbosity_Level > 3: print(Cat)
				if Cat in PosedCategories:
					obII = int(bvp.utils.floor(ObTmp.real/nPoses))
					Pose = int(bvp.utils.mod(ObTmp.real,nPoses))
				else:
					obII = int(ObTmp.real)
					Pose = None
				Grp,Fil = self.Lib.objects[Cat][obII]
				oParams = {
					'categ':Cat, #MakeBlenderSafe(ObTmp.imag),
					'exemp':Grp, #MakeBlenderSafe(ObTmp.real),
					'obFile':Fil, #self.obFiles,
					'obLibDir':os.path.join(self.Lib.LibDir,'Objects'), #self.obLibDir,
					'pose':Pose,
					'rot3D':None, # Set??
					'pos3D':None, # Set??
					}
				# Update oparams w/ self.oparams for general stuff for this scene list?? (fixed size, location, rotation???)
				# Make Rotation wrt camera???
				ScOb.append(bvpObject(oParams))
			
			# Get BG
			if bgIdx:
				Cat = self.Lib.bgs.keys()[int(bgIdx[iScn].imag)]
				Grp,Fil = self.Lib.bgs[Cat][int(bgIdx[iScn].real)]
				bgParams = {
					'categ':Cat, #MakeBlenderSafe(bgIdx[iScn].imag),
					'exemp':Grp, #MakeBlenderSafe(bgIdx[iScn].real),
					'bgFile':Fil,
					'bgLibDir':os.path.join(self.Lib.LibDir,'Backgrounds'), #self.bgLibDir,
					#'oParams':{}
					}
				bgParams.update(self.bgParams)
				ScBG = bvpBG(bgParams)
			else:
				# Create default BG (empty)
				ScBG = bvpBG(self.bgParams)
				
			# Get Sky
			if skyIdx:
				Cat = self.Lib.skies.keys()[int(skyIdx[iScn].imag)]
				Grp,Fil = self.Lib.skies[Cat][int(skyIdx[iScn].real)]			
				skyParams = {
					'categ':Cat, #MakeBlenderSafe(skyIdx[iScn].imag),
					'exemp':Grp, #MakeBlenderSafe(skyIdx[iScn].real),
					'skyLibDir':os.path.join(self.Lib.LibDir,'Skies'), #self.skyLibDir,
					#'skyFiles':self.skyFiles,
					'skyFile':Fil
					#'skyList':self.skyList,
					}
				skyParams.update(self.skyParams)
				ScSky = bvpSky(skyParams)
			else:
				# Create default sky
				ScSky = bvpSky(self.skyParams)
			# Get Camera
			# GET cParams from BG??? have to do that here???
			ScCam = bvpCamera(self.cParams)
			# Timing
			self.ScnParams = fixedKeyDict({
				'frame_start':1,
				'frame_end':self.nFramesPerScene[iScn]
				})
			newScnParams = {
				'Num':iScn+1,
				'Obj':ScOb,
				'BG':ScBG,
				'Sky':ScSky,
				'Cam':ScCam,
				'ScnParams':self.ScnParams,
				}
			Scn = bvpScene(newScnParams)
			# Object positions are committed as scene is created...
			self.ScnList.append(Scn)
	def MakeListFromLib(self,Type='Obj'):
		'''
		Usage: Idx = MakeListFromLib(Type='Obj')
		
		Creates an index/list of (objects, bgs) for each scene, given a bvpLibrary
		Input "Type" specifies which type of scene element ('Obj','BG','Sky') is to be arranged into a list. (case doesn't matter)
		
		Each (object, bg, etc) is used an equal number of times
		Potentially replace this function with other ways to sample from object categories...? 
		(sampling more from some categories than others, guaranteeing an equal number of exemplars from each category, etc)
		ML 2011.10.31
		'''
		if Type.lower()=='obj':
			List = self.nObjectsPerCat
			nUsed = self.nObjectsUsed
		elif Type.lower()=='bg':
			List = self.nBGsPerCat
			nUsed = self.nScenes
		elif Type.lower()=='sky':
			List = self.nSkiesPerCat
			nUsed = self.nScenes
		else:
			raise Exception('WTF - don''t know what to do with Type=%s'%Type)
		nAvail = sum(List)
		if nAvail==0:
			return None
		Idx = np.concatenate([np.arange(o)+n*1j for n,o in enumerate(List)])
		# decide how many repetitions of each object to use
		nReps = np.floor(float(nUsed)/float(nAvail))
		nExtra = nUsed - nReps * nAvail
		ShufIdx = np.random.permutation(nAvail)[:nExtra]
		Idx = np.concatenate([np.tile(Idx,nReps),Idx[ShufIdx]])
		np.random.shuffle(Idx) # shuffle objects
		### NOTE! this leaves open the possiblity that multiple objects of the same type will be in the same scene. OK...
		Idx = Idx.tolist()
		return Idx
		"""