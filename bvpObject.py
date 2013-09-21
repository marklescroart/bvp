'''
.B.lender .V.ision .Project class for storage of abstraction of a Blender object
'''
## NOTE! See http://western-skies.blogspot.com/2008/02/simple-complete-example-of-python.html for __getstate__() and __setstate__() methods

# Imports
import os,bvp,random
from bvp.utils.basics import fixedKeyDict 
from bvp.utils.blender import AddGroup,GrabOnly
from bvp.utils.math import PerspectiveProj
# Blender imports
if bvp.Is_Blender:
	import bpy

class bvpObject(object):
	'''
	Usage: bvpObject(obID=None,Lib=None,pos3D=None,size3D=None,rot3D=None,pose=None)
	
	Class to store an abstraction of an object in a BVP scene. Stores all necessary information to define an object in a scene.
	
	Inputs:
		'obID':'Animal', # purely informative, not used (as of 2011.11.30)
		'Lib': bvpLibrary object, contains relevant info about object (file location, real size, (more??))
		'pos3D':[], # position [X,Y,Z] in 3D
		'size3D':3., # Size of largest dimension. Set to "None" to use object's real world size? (TO DO??)
		'rot3D':[], # rotation (xyz euler) in 3D
		'pose':[], # number for pose in object's pose library
	
	Other Properties:
		(All object properties from bvpLibrary.objects entry, including "realWorldSize","semanticCat")
	
	To place in a scene, minimally requires obID and Lib. Optionally input position in 3D, position in 2D
	
	All properties should be scalars (int/float) or tuples
	
	'''
	def __init__(self,obID=None,Lib=None,pos3D=None,size3D=3.,rot3D=None,pose=None):
		# Set inputs to local values
		Inpt = locals()
		for i in Inpt:
			if not i=='self':
				setattr(self,i,Inpt[i])
		# Default values
		self.grpName=None
		self.parentFile=None
		self.semanticCat=None
		self.realWorldSize=1.0 # size of object in meters
		self.nVertices=0
		self.nFaces=0
		self.pos2D=None # location in the image plane (normalized 0-1)
		if obID:
			if not Lib:
				Lib = bvp.bvpLibrary()
			TmpOb = Lib.getSC(obID,'objects')
			self.__dict__.update(TmpOb)
		#else:
			# Default object?
		if isinstance(self.realWorldSize,(list,tuple)):
			self.realWorldSize = self.realWorldSize[0]
	def __repr__(self):
		S = '\n ~O~ bvpObject "%s" ~O~\n'%(self.grpName)
		if self.parentFile:
			S+='Parent File: %s\n'%self.parentFile
		if self.semanticCat:
			S+=self.semanticCat[0]
			for s in self.semanticCat[1:]: S+=', %s'%s
			S+='\n'
		if self.pos3D:
			S+='Position: (x=%.2f, y=%.2f, z=%.2f) '%tuple(self.pos3D)
		if self.size3D:
			S+='Size: %.2f '%self.size3D
		if self.pose:
			S+='Pose: #%d'%self.pose
		if self.pos3D or self.size3D or self.pose:
			S+='\n'
		if self.nVertices:
			S+='%d Verts; %d Faces'%(self.nVertices,self.nFaces)
		return(S)
	def PlaceObj(self,Scn=None):
		'''
		Usage: PlaceObj(Scn=None)
		
		Places object into Blender scene, along with pose, animation information** 
		
		** animation info still to come **
		ML 2012.01.31
		'''
		if not Scn:
			Scn=bpy.context.scene
		if self.grpName is None:
			print('Empty object! Using sphere instead!')
			uv = bpy.ops.mesh.primitive_uv_sphere_add
			uv(size=5)
			bvp.utils.blender.SetCursor((0,0,-5.))
			bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
			bpy.ops.transform.translate(value=(0,0,5))
			bvp.utils.blender.SetCursor((0,0,0))
		else:
			obLibDir,obFile = os.path.split(self.parentFile)
			AddGroup(obFile,self.grpName,obLibDir)
		G = bpy.context.object
		Sz = float(self.size3D)/10. # Objects are stored at max dim. 10 for easier viewability /manipulation
		setattr(G,'scale',bvp.bmu.Vector((Sz,Sz,Sz))) # uniform x,y,z scale
		if self.pos3D:
			setattr(G,'location',self.pos3D)
		if self.rot3D:
			# Use bpy.ops.transform here instead? Some objects may not have position set to zero properly!
			setattr(G,'rotation_euler',self.rot3D)
		if self.pose or self.pose==0: # allow for pose index to equal zero, but not None
			Arm,Pose = self.GetPoses(G)
			self.ApplyPose(Arm,self.pose)
		# Deal with particle systems:
		if not self.grpName is None:
			for o in G.dupli_group.objects:
				# Get the MODIFIER object that contains the particle system
				PartSystModf = [p for p in o.modifiers if p.type=='PARTICLE_SYSTEM']
				for psm in PartSystModf:
					#print('Object %s has particle system %s'%(o.name,ps.name))
					# Option 1: Turn off the whole modifier (this seems to work)
					if self.size3D  < 3.:
						psm.show_render = False
						psm.show_viewport = False
					# Option 2: shorten / lengthen w/ object size
					#psm.particle_system (set hair normal lower doesn't seem to work...s)
		Scn.update()
		# Because some poses / effects don't seem to take effect until the frame changes:
		Scn.frame_current+=1
		Scn.update()
		Scn.frame_current-=1
		Scn.update()
	def PlaceObjFull(self,Scn=None):
		"""
		import full copy of object (all meshes, etc)
		USE WITH CAUTION. Only for modifying meshes / materials, 
		which you PROBABLY DON'T WANT TO DO.
		"""
		if not Scn:
			Scn=bpy.context.scene
		if self.grpName is None:
			print('Empty object! Using sphere instead!')
			uv = bpy.ops.mesh.primitive_uv_sphere_add
			uv(size=5)
			bvp.utils.blender.SetCursor((0,0,-5.))
			bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
			bpy.ops.transform.translate(value=(0,0,5))
			bvp.utils.blender.SetCursor((0,0,0))
		else:
			obLibDir,obFile = os.path.split(self.parentFile)
			AddGroup(obFile,self.grpName,obLibDir)
		G = bpy.context.object
		Sz = float(self.size3D)/10. # Objects are stored at max dim. 10 for easier viewability /manipulation
		setattr(G,'scale',bvp.bmu.Vector((Sz,Sz,Sz))) # uniform x,y,z scale
		if self.pos3D:
			setattr(G,'location',self.pos3D)
		if self.rot3D:
			# Use bpy.ops.transform here instead? Some objects may not have position set to zero properly!
			setattr(G,'rotation_euler',self.rot3D)
		if self.pose or self.pose==0: # allow for pose index to equal zero, but not None
			Arm,Pose = self.GetPoses(G)
			self.ApplyPose(Arm,self.pose)
		# Deal with particle systems:
		if not self.grpName is None:
			for o in G.dupli_group.objects:
				# Get the MODIFIER object that contains the particle system
				PartSystModf = [p for p in o.modifiers if p.type=='PARTICLE_SYSTEM']
				for psm in PartSystModf:
					#print('Object %s has particle system %s'%(o.name,ps.name))
					# Option 1: Turn off the whole modifier (this seems to work)
					if self.size3D  < 3.:
						psm.show_render = False
						psm.show_viewport = False
					# Option 2: shorten / lengthen w/ object size
					#psm.particle_system (set hair normal lower doesn't seem to work...s)
		Scn.update()
		# Because some poses / effects don't seem to take effect until the frame changes:
		Scn.frame_current+=1
		Scn.update()
		Scn.frame_current-=1
		Scn.update()

	def GetPoses(self,pOb):
		'''
		Usage: Arm,Pose = GetPoses(pOb)
		
		Creates a proxy object from the armature object within a linked 
		group. (note: THERE BETTER ONLY BE ONE!). Assigns the pose library
		from the original armature in the group to the proxy object, and
		returns the proxy armature object and a list of the pose names in 
		the pose library.
		
		ML 2012.03.02
		'''
		# Make proxy object
		GrabOnly(pOb)
		Arm = [x for x in pOb.dupli_group.objects if x.type=='ARMATURE'][0]
		bpy.ops.object.proxy_make(object=Arm.name) #object=pOb.name,type=Arm.name)
		ArmProxy = bpy.context.object
		ArmProxy.pose_library=Arm.pose_library
		Pose = [x.name for x in ArmProxy.pose_library.pose_markers]
		return ArmProxy,Pose
	def ApplyPose(self,Arm,PoseIdx):
		'''
		Usage: ApplyPose(Arm,PoseIdx)
		
		Apply a pose to an armature
		
		ML 2012.01
		'''
		# Set mode to pose mode
		GrabOnly(Arm)
		bpy.ops.object.posemode_toggle()
		bpy.ops.pose.select_all(action="SELECT")
		bpy.ops.poselib.apply_pose(pose_index=PoseIdx)
		bpy.ops.object.posemode_toggle()