## NOTE! See http://western-skies.blogspot.com/2008/02/simple-complete-example-of-python.html for __getstate__() and __setstate__() methods

# Imports
import bvp,copy
from bvp.utils.basics import fixedKeyDict,gridPos,linspace # non-numpy-dependent version of linspace
from bvp.utils.blender import SetCursor
from bvp.utils.bvpMath import ImPosCount
if bvp.Is_Blender:
	import bpy

# def getCamPos(n,xL=(-5,5),yL=(-5,5),zL=(0,10)):
# 	# Cam Position
# 	p = []
# 	for x in linspace(xL[0],xL[1],n):
# 		for y in linspace(yL[0],yL[1],n):
# 			for z in linspace(zL[0],zL[1],n):
# 				p.append([x,y,z])
# # Fix Position
# f = [[0,0,0] for x in range(len(p))]
# return p,f

class bvpScene(object):
	'''
	Usage: S = bvpScene(Num=0,Obj=None,BG=None,Sky=None,Shadow=None,Cam=None,FrameRange=(1,1),fPath=None,FrameRate=15)
	
	Class for an abstraction of a Blender scene. Holds all information regarding background, sky, and objects 
	(identity, size, position) in the scene. NOT (necessarily) a real Blender scene in a .blend file. Can be 
	rendered / created in Blender (for debugging, inspection, modification, custom render, whatever).
	
	Inputs:
	Num - Scene number (identifier - 1 to ????)
	Obj - List of class bvpObject. Objects can either have* or not have* position specified in advance. 
		If no positions are specified a priori, bvpScene method "PopulateScene" 
	BG - instance of class bvpBG, which controls background and constraints on object / camera positions.
	Sky - instance of class bvpSky, which controls sky (image), world settings, and lighting. 
	Cam - instance of class bvpCam. Defaults to slight up-right camera with no motion.
	
	FrameRange - frame span to render of this scene (1,1) by default.
	FrameRate - 15 by default (set in bvp.settings)
	
	Commonly, the 
	ML 2011.10.26
	'''
	#def __init__(self,scnParams={}):
	def __init__(self,Num=0,Obj=None,BG=None,Sky=None,Shadow=None,Cam=None,FrameRange=(1,1),fPath=None,FrameRate=bvp.Settings['RenderDefaults']['FrameRate']): # is frame rate Necessary? Determines camera speed...
		'''
		Class to store sufficient info for defining a scene in Blender.
		
		2011.10.11 ML
		'''		
		# Add inputs as class properties
		Input = locals()
		for i in Input:
			if not i in ['self']:
				setattr(self,i,Input[i])
		
		if not self.Obj:
			# Make "Obj" field into a list
			self.Obj = []
		# Set default sky parameters
		if not self.Sky: 
			self.Sky = bvp.bvpSky()
		# Set default background parameters
		if not self.BG:
			self.BG = bvp.bvpBG()
		# Default camera: Fixed position!
		if not self.Cam:
			self.Cam = bvp.bvpCamera(lens=self.BG.lens) # TO DO: Set cam default to file "Settings"! 
		# Final elements, shadows, are not necessary
		# Set file path for renders:
		if not self.fPath:
			self.fPath = 'Sc%04d_##'%self.Num
		self.FrameRate = FrameRate

	# Consider adding fPath to the list of attributes...
	# Change fPath in inputs to fBase, incorporate self.num automatically into base.
	# @propertry
	# def fPath(self):
	# 	...
	@property
	def nObjects(self):
		return len(self.Obj)
	@property
	def ScnParams(self):
		d = fixedKeyDict({
			'frame_start':self.FrameRange[0],
			'frame_end':self.FrameRange[1] # Default is 3 seconds
			# MORE??
			})
		return d
	def __repr__(self):
		S = 'Class "bvpScene" (Num=%d, %.2f s, Frames=(%d-%d)):\n'%(self.Num,(self.FrameRange[1]-self.FrameRange[0]+1)/float(self.FrameRate),self.FrameRange[0],self.FrameRange[1])
		S+='BACKGROUND%s\n\n'%self.BG
		S+='SKY%s\n\n'%self.Sky
		S+='SHADOW%s\n\n'%self.Shadow
		S+='CAMERA%s\n\n'%self.Cam
		S+='OBJECTS\n'
		for o in self.Obj:
			S+='%s\n'%o
		return S
	
	def PopulateScene(self,ObList,ResetCam=True,ImPosCt=None,EdgeDist=0.,ObOverlap=.50,MinSz2D=0,RaiseError=False,nIter=50):
		'''Choose positions for all objects in "ObList" input within the scene,
		according to constraints provided by scene background.
		
		ImPosCt tracks the number of times that each image location (bin) 
		has had an object in it. Can be omitted for single scenes (defaults
		to randomly sampling whole image)

		ML 2012.03
		'''
		from random import shuffle
		if not ImPosCt:
			ImPosCt = ImPosCount(0,0,ImSz=1.,nBins=5,e=1)
		Attempt = 1
		Done = False
		while Attempt<=nIter and not Done:
			Fail = False
			ObToAdd = []
			if bvp.Verbosity_Level > 3:
				print('### --- Running PopulateScene, Attempt %d --- ###'%Attempt)
			if ResetCam:
				# Start w/ random cam,fixation position
				cPos = self.BG.camConstraints.sampleCamPos(self.FrameRange)
				fPos = self.BG.camConstraints.sampleFixPos(self.FrameRange)
				self.Cam = bvp.bvpCamera(location=cPos,fixPos=fPos,frames=self.FrameRange,lens=self.BG.lens)
			# Multiple object constraints for moving objects
			OC = []
			for o in ObList:
				# Randomly cycle through object constraints
				if not OC:
					if type(self.obConstraints) is list:
						OC = copy.copy(self.obConstraints)
					else:
						OC = [copy.copy(self.obConstraints)]
					shuffle(OC)
				oc = OC.pop()
				NewOb = copy.copy(o) # resets size each iteration as well as position
				if self.BG.obstacles:
					Obst = self.BG.obstacles+ObToAdd
				else:
					Obst = ObToAdd
				if not o.semanticCat:
					# Sample semantic category based on BG??
				 	# UNFINISHED as of 2012.10.22
				 	pass #etc.
				if not o.size3D:
					# OR: Make real-world size the default??
					# OR: Choose objects by size??
					NewOb.size3D = oc.sampleSize()
				if not o.rot3D:
					# NOTE: This is fixing rotation of objects to be within 90 deg of facing camera
					NewOb.rot3D = oc.sampleRot(self.Cam)
				if not o.pos3D:
					# Sample position last (depends on Cam position, It may end up depending on pose, rotation, (or action??)
					NewOb.pos3D,NewOb.pos2D = oc.sampleXY(NewOb.size3D,self.Cam,Obst=Obst,EdgeDist=EdgeDist,ObOverlap=ObOverlap,RaiseError=False,ImPosCt=ImPosCt,MinSz2D=MinSz2D)
					if NewOb.pos3D is None:
						Fail=True
						break
				ObToAdd.append(NewOb)
			if not Fail:
				Done=True
			else:
				Attempt+=1
		# Check for failure
		if Attempt>nIter and RaiseError:
			raise Exception('MaxAttemptReached','Unable to populate scene %s after %d attempts!'%(self.BG.grpName,nIter))
		elif Attempt>nIter and not RaiseError:
			print('Warning! Could not populate scene! Only got to %d objects!'%len(ObToAdd))
		self.Obj = ObToAdd
		# Make sure last fixation hasn't "wandered" away from objects: 
		fPosFin = self.BG.camConstraints.sampleFixPos((1,),obj=ObToAdd)
		self.Cam.fixPos = self.Cam.fixPos[:-1]+[fPosFin[0],]

	def ApplyOpts(self,Scn=None,rOpts=None):
		'''
		Usage: ApplyOpts(Scn=None,rOpts=None)

		Apply general options to scene (environment lighting, world, start/end frames, etc), 
		including (optionally) render options (of class 'RenderOptions'))
		
		ML 2011
		'''
		if not Scn:
			Scn = bpy.context.scene # Get current scene if input not supplied
		# Set frames (and other scene props?)
		for s in self.ScnParams.keys():
			setattr(Scn,s,self.ScnParams[s])
		if rOpts:
			# Set filepath
			if rOpts.BVPopts['BasePath'][-2:]!='%s':
				print('Warning! base path did not have room to add scene-specific file name. MODIFYING...')
				rOpts.BVPopts['BasePath']+='%s'
			Scn.render.filepath = rOpts.BVPopts['BasePath']%self.fPath
			rOpts.ApplyOpts()
	def GetOcclusion(self):
		'''
		Get occlusion matrix (% occlusion of each object by others)
		TO COME (?)
		'''


	def Create(self,rOpts=None,Scn=None):
		'''
		Creates scene (imports BG, sky, lights, objects, shadows) in Blender
		'''
		if not Scn:
			Scn = bpy.context.scene
		# set layers to correct setting
		Scn.layers = [True]+[False]*19
		# set cursort to center
		SetCursor((0,0,0))
		# place bg
		self.BG.PlaceBG()
		if self.BG.realWorldSize<50. and 'indoor' in self.BG.semanticCat:
			# Due to a problem with skies coming inside the corners of rooms
			Scale = self.BG.realWorldSize*1.5
		else:
			Scale = self.BG.realWorldSize
		self.Sky.PlaceSky(num=self.Num,Scale=Scale)
		self.Cam.PlaceCam(IDname='Cam%03d'%self.Num)
		if self.Shadow:
			self.Shadow.PlaceShadow(Scale=self.BG.realWorldSize)
		for o in self.Obj:
			o.PlaceObj()
		Scn.name = self.fPath
		self.ApplyOpts(rOpts=rOpts)
		Scn.layers = [True]*20
	def CreateWorking(self,rOpts=None,Scn=None):
		'''
		Creates scene (imports BG, sky, lights, objects, shadows) in Blender
		(Allows for objects without 3D pos / size yet!)
		'''
		if not Scn:
			Scn = bpy.context.scene
		# set layers to correct setting
		Scn.layers = [True]+[False]*19
		# set cursort to center
		SetCursor((0,0,0))
		# place bg
		self.BG.PlaceBG()
		self.Sky.PlaceSky(num=self.Num,Scale=self.BG.realWorldSize)
		self.Cam.PlaceCam(IDname='Cam%03d'%self.Num)
		if self.Shadow:
			self.Shadow.PlaceShadow(Scale=self.BG.realWorldSize)
		for o in self.Obj:
			try:
				o.PlaceObj()
			except:
				pass
		Scn.name = self.fPath
		self.ApplyOpts(rOpts=rOpts)
		Scn.layers = [True]*20	
	def Render(self,rOpts,Scn=None):
		'''
		Usage: Render(rOpts,Scn=None)

		Renders the scene (immediately, in open instance of Blender)
		
		rOpts (class RenderOptions) specifies rendering parameters.

		ML 2011.10
		'''
		if not Scn:
			Scn = bpy.context.scene
		# Reset scene nodes (?)
		
		# Apply rendering options
		Scn.render.filepath = rOpts.BVPopts['BasePath']%self.fPath
		rOpts.ApplyOpts()
		# Render all layers!
		Scn.layers = [True]*20
		if rOpts.BVPopts['Type'].lower()=='firstframe':
			Scn.frame_step = Scn.frame_end+1 # so only one frame will render
		elif rOpts.BVPopts['Type'].lower()=='firstandlastframe':
			Scn.frame_step = Scn.frame_end-1
		elif rOpts.BVPopts['Type'].lower()=='all':
			Scn.frame_step = 1
		elif rOpts.BVPopts['Type'].lower()=='every4th':
			# Assure that scene starts with a multiple of 4 + 1
			while not Scn.frame_start%4==1:
				Scn.frame_start += 1
			Scn.frame_step = 4
		else:
			raise Exception("Invalid render type specified!\n   Please use 'FirstFrame','FirstAndLastFrame', or 'All'")
		# Render animation
		bpy.ops.render.render(animation=True,scene=Scn.name)

	def Clear(self,Scn=None):
		'''
		Usage: Clear(Scn=None)

		Removes all objects, lights, background; resets world settings; clears all nodes; readies scene for next import /render
		
		This is essential for memory saving in long render runs. Use with caution. Highly likely to crash Blender.

		ML 2011
		'''
		### --- Removing objects for next scene: --- ### 
		if not Scn:
			Scn = bpy.context.scene
		# Remove all mesh objects		
		Me = list()
		for o in bpy.data.objects:
			#ml.GrabOnly(o)
			if o.type=='MESH': # Only mesh objects for now = cameras too?? Worlds??
				Me.append(o.data)
			if o.name in Scn.objects: # May not be... why?
				Scn.objects.unlink(o)
			o.user_clear()
			bpy.data.objects.remove(o)		
		# Remove mesh objects
		for m in Me:
			m.user_clear()
			bpy.data.meshes.remove(m)
		# Remove all textures:
		# To come
		# Remove all images:
		# To come
		# Remove all worlds:
		# To come
		# Remove all actions/poses:
		for act in bpy.data.actions:
			act.user_clear()
			bpy.data.actions.remove(act)
		# Remove all armatures:
		for arm in bpy.data.armatures:
			arm.user_clear()
			bpy.data.armatures.remove(arm)
		# Remove all groups:
		for g in bpy.data.groups:
			g.user_clear()
			bpy.data.groups.remove(g)
		# Remove all rendering nodes
		for n in Scn.node_tree.nodes:
			Scn.node_tree.nodes.remove(n)
		# Re-set (delete) all render layers
		RL = bpy.context.scene.render.layers.keys()
		bpy.ops.scene.render_layer_add()
		for ii,n in enumerate(RL):
			bpy.context.scene.render.layers.active_index=0
			bpy.ops.scene.render_layer_remove()
		# Rename newly-added layer (with default properties) to default name:
		bpy.context.scene.render.layers[0].name = 'RenderLayer'
		# Set only first layer to be active
		Scn.layers = [True]+[False]*19
