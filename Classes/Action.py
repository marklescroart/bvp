'''
.B.lender .V.ision .Project class for storage of actions
'''
## NOTE! See http://western-skies.blogspot.com/2008/02/simple-complete-example-of-python.html for __getstate__() and __setstate__() methods

# Imports
import os
import random
import warnings
from .DB import DB
from .MappedClass import MappedClass
import ..utils as bvpu
import ..Settings # Config file, same as vm_tools, pycortex, etc.

try: 
	import bpy
	#from . import bmu
	is_blender = True
except ImportError:
	is_blender = False
	pass

class Action(MappedClass):
	'''Layer of abstraction for armature-based actions (imported from other files) in Blender scenes.
	'''
	def __init__(self, name='DummyAction', file_name=None, armature='mixamo_human', wordnet_label=None, wordnet_frames=None,
			is_cyclic=False, is_translating=False, is_broken=False, bg_interaction=False, obj_interaction=False, 
			is_interactive=False, is_animal=False, fps=24, min_xyz=None, max_xyz=None, dbi=None):
		"""Class to store an armature-based action for an object in a BVP scene. 

		Parameters
		----------
		dbi : DB object | None
			Database interface object for local/network BVP database of objects. If set to None, database is
			not searched, object is created from 

		Other Parameters
		----------------		
		name : string
			ID for object (unique name for an object in the database, which is also (as of 2014.09, but
			this may change) the name for the Blender group in the archival .blend file)
		file_name : string
			Name of file in which action resides
		armature : string
			Class of armature to which this action can be applied, e.g. "mixamo_human"
			### mmm... Should possibly be a foreign key to an armature class. 
		wordnet_label : list
			Specific WordNet category or categories for action (e.g. walk.v.01)
		wordnet_frames : list
			List of frames at which each wordnet label first applies (each labeled action is assumed to 
			continue either until the next label or the end of the action)
		is_cyclic : bool
			Whether or not action is cyclical (whether last frame returns to first frame)
		is_translating : bool
			Whether or not the action moves the animated object (substantially*) from its initial position
			* this is currently loosely defined
		is_broken : bool
			Whether or not action is currently broken
		bg_interaction : bool
			Whether or not the action requires a background to be sensible (e.g. an action for climbing stairs
			would be ridiculous without stairs)
		obj_interaction : bool
			Whether or not the action requires an object to be sensible (e.g. swinging a baseball bat)
		is_interactive : bool
			Whether or not the action requires another human to be sensible (e.g. shaking hands). Gesticulating
			or communicating does not necessarily require `is_interactive` to be True, if the recipient of the
			gesture or communication act could possibly be off-camera. 
		is_animal : bool
			Whether or not the action applies to an animal. This is temporary, will be replaced by the `armature`
			field when code/library are mature. 
		fps : int
			frames per second for action to appear normal
		min_xyz : list 
			minimum x, y, and z positions for animated object during action 
			(part of bounding box for action)
		max_xyz : list 
			maximum x, y, and z positions for animated object during action 
			(part of bounding box for action)	
		dbi : DB object
			Database interface (for saving, loading, etc)

		Returns
		-------
		Action instance

		"""
		# Transplanted from vm_tools - use me? 
        # inpt = locals()
        # self.type = 'Action'
        # for k,v in inpt.items():
        #     if not k in ['self']:
        #         setattr(self,k,v)


		# Allow dbi to be a list of parameters to create a DB. This helps with rendering on cluster 
		# computers; dictionaries are easier to store/pass as arguments than objects. 
		if isinstance(self.dbi,dict):
			self.dbi = DB(**self.dbi)
		# NO defaults, because what's the point of an empty action?
		if dbi is None:
			# Even this is questionable... Allows for on-the-fly definition of actions, but do we care? Probably not.
			dbob = kwargs
		else:
			# Query database. Update to optionally throw error if object is not unique??
			# Not great: this is mongodb sepecific. Don't want.
			dbob = dbi.dbi.actions.find_one(kwargs)

	def save(self, context):
		"""Save Action to database; must be called inside an active Blender session"""
		if not is_blender:
			raise Exception("Can't save while operating outside of Blender!")
		pass

	@classmethod
	def from_blender(cls,context):
		"""Create an bvp.Action from a selected object in Blender. 

		This function only works within an active Blender session. The selected object must be an armature with
		an action linked to it. 

		Parameters
		----------
		context : bpy context
			context for determining selected object, etc

		Returns
		-------
		Action : bvp.Action object
			duh.
		"""
		# Idiot-proofing
		if not is_blender:
			raise Exception("from_blender() only works within an active blender session.")
		# Get relevant blender objects 
		wm = context.window_manager
		ob = context.object
		act = ob.animation_data.action
		# Compute parameters
		## Frames
		n_frames = np.floor(act.frame_range[1])-np.ceil(act.frame_range[0])
		## WordNet labels
		wordnet_labels = [s.name for s in act.bvpAction.wordnet_label]
		wordnet_frames = [s.frame for s in act.bvpAction.wordnet_label]
		## Bounding box
		if isinstance(ob.data,bpy.types.Armature):
			# Get child objects, armatures have no position information
			ob_list = [ob]+list(ob.children)
		scn = context.scene
		mn,mx = [],[]
		for fr in range(int(np.floor(act.frame_range[0])),int(np.ceil(act.frame_range[1]))):
		    scn.frame_set(fr)
		    scn.update()
		    # Re-visit me
		    mntmp,mxtmp = bvp.utils.blender.get_group_bounding_box(ob_list)
		    mn.append(mntmp)
		    mx.append(mxtmp)
		min_xyz = np.min(np.vstack(mn),axis=0).tolist()
		max_xyz = np.max(np.vstack(mx),axis=0).tolist()
		#bvpu.blender.make_cube('bbox',min_xyz,max_xyz) # works. This shows the bounding box, if you want. 
		bvpu.blender.grab_only(ob)
		## Parent file
		#pfile = act.bvpAction.parent_file
		# The above value (pfile) is ignored for now. Need to eventually implement some way to take the contents 
		# of the current file (group/action/whatever) and save them (append them) to another specfied file
		# in the database. Currently NOT IMPLEMENTED.
		thisfile = os.path.split(bpy.data.filepath)[1] #if len(bpy.data.filepath)>0 else pfile
		if thisfile=="":
			# Require saving in db-appropriate location 
			raise NotImplementedError("Please save this file into %s before trying to save to database."%(os.path.join(dbpath,'Action/')))
		# Create database instance
		dbi = DB(port=Settings['db']['port'], dbname=wm.active_db)
		# Construct bvp Action
		bvpact = cls.__new__(cls)
        bvpact.__init__(name=act.name,
			file_name=thisfile,
			# Labels / info
			wordnet_labels=wordnet_labels,
			wordnet_frames=wordnet_frames,
			# Flags
			is_cyclic=act.bvpAction.is_cyclic,
			is_translating=act.bvpAction.is_translating,
			is_broken=act.bvpAction.is_broken,
			is_armature=act.bvpAction.is_armature,
			bg_interaction=act.bvpAction.bg_interaction,
			obj_interaction=act.bvpAction.obj_interaction,
			is_interactive=act.bvpAction.is_interactive,
			is_animal=act.bvpAction.is_animal,
			# Computed / assumed
			n_frames=n_frames,
			fps=act.bvpAction.fps,
			min_xyz=min_xyz,
			max_xyz=max_xyz,
			dbi=dbi)
        return bvpact

	def __repr__(self):
		"""Display string"""
		S = '\n ~A~ Action "%s" ~A~\n'%(self.name)
		for k,v in self.docdict:
			S += '%s : %s\n'%(k,repr(v))
		return S
