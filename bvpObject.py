'''
.B.lender .V.ision .Project class for storage of abstraction of a Blender object
'''
## NOTE! See http://western-skies.blogspot.com/2008/02/simple-complete-example-of-python.html for __getstate__() and __setstate__() methods

# Imports
import os
import bvp # This seems like it shouldn't work, but it does... WHY?
import random
import warnings
# Get rid of these - import from local directories
from bvp.utils.basics import fixedKeyDict 
from bvp.utils.blender import add_group,add_action,grab_only,set_cursor,new_scene
from bvp.utils.bvpMath import PerspectiveProj
# Blender imports # GET RID OF this too! find a better way to set a global variable...
from . import Verbosity_Level, Is_Blender
#from . import bvpDB # Why is this causing me problems?
if Is_Blender:
	import bpy
	from . import bmu

class bvpObject(object):
	'''Layer of abstraction for objects (imported from other files) in Blender scenes.
	'''
	def __init__(self,dbi=None,action=None,pose=None,pos3D=(0.,0.,0.),size3D=3.,rot3D=(0.,0.,0.),**kwargs):
		"""	Class to store an abstraction of an object in a BVP scene. 

		Stores all necessary information to define an object in a scene: identifying information for
		the object in the database of all BVP objects (in `kwargs`, for database with interface `dbi`), 
		as well as (optionally) position, size, rotation, pose, and action information.

		Parameters
		----------
		dbi : bvpDB object | None
			Database interface object for local/network BVP database of objects. If set to None, database is
			not searched, object is created from 
		pose : int | None
			Index for pose in object's pose library (if object has an armature with a pose library)
		action : bvpAction object | dict (?)

		pos3D : tuple or bpy.Vector
			Position [X,Y,Z] in 3D. If the object has an action attached to it, this is the 
			starting position for the action. 
		size3D : float | 3.0
			Size of largest dimension. Set to "None" to use object's real world size? (TO DO??)
		rot3D : bpy euler or tuple | (0.,0.,0.)
			rotation (xyz euler) in 3D
		
		Other Parameters
		----------------		
		grpName : string
			ID for object (unique name for an object in the database, which is also (as of 2014.09, but
			this may change) the name for the Blender group in the archival .blend file)
		semanticCat : string | list
			semantic category of object
		realWorldSize : float
			Size of object in meters
		...

		Returns
		-------
		bvpObject instance

		Notes
		-----
		All "Other Parameters" are kwargs, which will be used to search the BVP database (for which `dbi` 
		is the database interface) for an object. Currently NO error is thrown if this object is not unique.

		TO DO (maybe): update this function to optionally throw an error if unique objects are desired.

		Any object property that is stored in the BVP databse can be used as a kwarg, including but not 
		limited to the variables listed here. This is intended to be kept open-ended, since it is difficult 
		to know what information future users will want to store about their 3D objects.		
		"""
		# Allow dbi to be a list of parameters to create a bvpDB. This helps with rendering on cluster 
		# computers; dictionaries are easier to store/pass as arguments than objects. 
		if isinstance(dbi,dict):
			dbi = bvp.bvpDB(**dbi)
		# Default attribute fields
		dbob = dict(realWorldSize=5.0,grpName='default_sphere',parentFile=None,semanticCat=None)
		if dbi is None:
			dbob.update(kwargs)
		else:
			# Query database. Update to optionally throw error if object is not unique??
			result = dbi.dbi.objects.find_one(kwargs)
			if result is None:
				raise Exception("Could not find specified object in database!")
			dbob.update(result)
		# Set attributes based on database object fields. (Too flexible??)
		for k,v in dbob.items():
			# Should set at least: grpName,parentFile,semanticCat,wordnet_label,realWorldSize,
			# nVertices, nFaces,
			setattr(self,k,v)
		# Set input attributes
		self.action = action
		self.pose = pose
		self.pos3D = pos3D
		self.size3D = size3D
		self.rot3D = rot3D
		# Misc Cleanup - remove?
		self.pos2D=None # location in the image plane (normalized 0-1)
		# uuuuh... lame. Fix?
		if isinstance(self.realWorldSize,(list,tuple)):
			self.realWorldSize = self.realWorldSize[0]

	def __repr__(self):
		"""Display string"""
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
		'''Places object into Blender scene, with pose & animation information

		Parameters
		----------
		Scn : string scene name | None
			If provided, the object will be linked to the named scene. If a scene
			named "Scn" does not exist, it will be created.
		
		'''
		# Optionally link to a specific scene
		Scn = bvp.utils.blender.set_scene(Scn)

		if self.grpName=='default_sphere':
			uv = bpy.ops.mesh.primitive_uv_sphere_add
			default_diameter=10.
			uv(size=default_diameter/2.)
			set_cursor((0,0,-default_diameter/2.))
			bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
			bpy.ops.transform.translate(value=(0,0,default_diameter/2.))
			set_cursor((0,0,0))
			G = bpy.context.object
		else:
			obLibDir,obFile = os.path.split(self.parentFile)
			G = add_group(self.grpName,obFile,obLibDir)
		# Eliminate any other currently-selected objects
		grab_only(G) 

		# Objects are stored at max dim. 10 for easier viewability /manipulation
		# Allow for asymmetrical scaling for weirdo-looking objects? (currently no)
		Sz = float(self.size3D)/10. 

		setattr(G,'scale',bmu.Vector((Sz,Sz,Sz))) # uniform x,y,z scale
		if not self.pos3D is None:
			setattr(G,'location',self.pos3D)
		if not self.rot3D is None:
			# Use bpy.ops.transform here instead? Some objects may not have position set to zero properly!
			setattr(G,'rotation_euler',self.rot3D)

		# Get armature, if an armature exists for this object
		if not G.dupli_group is None:
			Arm = [x for x in G.dupli_group.objects if x.type=='ARMATURE']
			if len(Arm)>0:
				# Some armature object detected. Proceed with pose / action.
				if len(Arm)>1:
					warnings.warn('Multiple armatures detected, this is probably an irregularity in the file...')
					# Try to deal with it by selecting the armature with a pose library attached:
					pose_test = [a for a in Arm if not a.pose_library is None]
					if len(pose_test)==0:
						Arm = Arm[0]
					elif len(pose_test)==1:
						Arm = pose_test[0]
					else:
						raise Exception("Aborting - all armatures have pose libraries, I don't know what to do")
				elif len(Arm)==1:
					Arm = Arm[0]
				bpy.ops.object.proxy_make(object=Arm.name) #object=pOb.name,type=Arm.name)
				ArmProxy = bpy.context.object
				ArmProxy.pose_library = Arm.pose_library
				# Update self w/ list of poses??
				if not ArmProxy.pose_library is None:
					self.poses = [x.name for x in ArmProxy.pose_library.pose_markers]
			else:
				Arm = None
		else:
			# For clarity
			Arm = None

		# Set pose, action
		if not self.pose is None:
			self.ApplyPose(ArmProxy,self.pose)
		if not self.action is None:
			# Get bvpAction if not already a bvpAction object
			if isinstance(self.action,dict):
				self.action = bvp.bvpAction(**self.action)
			self.ApplyAction(ArmProxy,self.action)
		# Deal with particle systems. Use of particle systems in general is not advised, since
		# they complicate sizing and drastically slow renders.
		if not G.dupli_group is None:
			for o in G.dupli_group.objects:
				# Get the MODIFIER object that contains the particle system
				PartSystModf = [p for p in o.modifiers if p.type=='PARTICLE_SYSTEM']
				for psm in PartSystModf:
					# Option 1: Turn off the whole modifier (this seems to work)
					if self.size3D  < 3.:
						psm.show_render = False
						psm.show_viewport = False
					# Option 2: shorten / lengthen w/ object size
					# NOTE: This doesn't work, since many particle systems are modified
					# after creation (e.g., hair is commonly styled). Again, avoid if 
					# possible...
		Scn.update()
		# Update scene, because some poses / effects don't seem to take effect until the frame changes:
		Scn.frame_current+=1
		Scn.update()
		Scn.frame_current-=1
		Scn.update()

	def PlaceObjFull(self,Scn=None,objects=True,materials=True,textures=True):
		"""Import full copy of object (all meshes, materials, etc)

		PROBABLY BROKEN CURRENTLY (2014.09)

		USE WITH CAUTION. Only for modifying meshes / materials, which you PROBABLY DON'T WANT TO DO.

		Parameters
		----------
		Scn : scene within file (?) | None
			Don't know if this is even usable (2014.02.05)
		"""
		# Optionally link to a differet scene
		Scn = bvp.utils.blender.set_scene(Scn)

		if self.grpName is None:
			print('Empty object! Using sphere instead!')
			uv = bpy.ops.mesh.primitive_uv_sphere_add
			uv(size=5)
			set_cursor((0,0,-5.))
			bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
			bpy.ops.transform.translate(value=(0,0,5))
			set_cursor((0,0,0))
		else:
			obLibDir,obFile = os.path.split(self.parentFile)
			add_group(self.grpName,obFile,obLibDir)
			# 
		G = bpy.context.object
		Sz = float(self.size3D)/10. # Objects are stored at max dim. 10 for easier viewability /manipulation
		setattr(G,'scale',bmu.Vector((Sz,Sz,Sz))) # uniform x,y,z scale
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

	def ApplyAction(self,arm,action):
		'''Apply an action to an armature.

		Kept separate from bvpObject __init__ function so to be able to interactively apply actions 
		in an open Blender session.

		Parameters
		----------
		arm : bpy.data.object containing armature
			Armature object to which the action is applied.
		action : bvpAction
			Action to be applied. Must have file_name and path attributes
		'''
		# 
		act = add_action(action.name,action.file_name,action.path)
		if arm.animation_data is None:
			arm.animation_data_create()
		arm.animation_data.action = act

	def ApplyPose(self,Arm,PoseIdx):
		'''Apply a pose to an armature.

		Parameters
		----------
		Arm : bpy.data.object contianing armature
			Armature to which to apply pose
		PoseIdx : scalar 
			Index for pose in the armature's pose library

		Notes
		-----
		This function only applies WHOLE-ARMATURE poses (for now). Later it may be useful to update
		this function to pose individual bones of an armature.
		
		'''
		# Set mode to pose mode
		grab_only(Arm)
		bpy.ops.object.posemode_toggle()
		bpy.ops.pose.select_all(action="SELECT")
		bpy.ops.poselib.apply_pose(pose_index=PoseIdx)
		# Set back to previous mode 
		# (IMPORTANT: otherwise Blender may puke and die with next command)
		bpy.ops.object.posemode_toggle()