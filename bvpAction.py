'''
.B.lender .V.ision .Project class for storage of actions
'''
## NOTE! See http://western-skies.blogspot.com/2008/02/simple-complete-example-of-python.html for __getstate__() and __setstate__() methods

# Imports
import os
import bvp # This seems like it shouldn't work, but it does... WHY?
import random
import warnings
# Get rid of these - import from local directories
# from bvp.utils.basics import fixedKeyDict 
# from bvp.utils.blender import add_group,add_action,grab_only,set_cursor,new_scene
# from bvp.utils.bvpMath import PerspectiveProj
# Blender imports # Is there a better way to set a global variable?
from . import Verbosity_Level, Is_Blender
#from . import bvpDB # Why is this causing me problems?
if Is_Blender:
	import bpy
	from . import bmu

class bvpAction(object):
	'''Layer of abstraction for armature-based actions (imported from other files) in Blender scenes.
	'''
	def __init__(self,dbi=None,**kwargs):
		"""	Class to store an armature-based action for an object in a BVP scene. 

		WIP.

		Parameters
		----------
		dbi : bvpDB object | None
			Database interface object for local/network BVP database of objects. If set to None, database is
			not searched, object is created from 

		Other Parameters
		----------------		
		name : string
			ID for object (unique name for an object in the database, which is also (as of 2014.09, but
			this may change) the name for the Blender group in the archival .blend file)
		armature : string
			class of armature to which this action can be applied, e.g. "mixamo_human"
		semantic_cat : string | list
			semantic category of object
		...

		Returns
		-------
		bvpAction instance

		Notes
		-----

		parameters: armature, name, file_name, semantic_cat, wordnet_label, bounding_box (normalized to 0-1, i.e.
			it will be a multiplier on the base object's size), frame_range, cycle (T/F), 

		All "Other Parameters" are kwargs, which will be used to search the BVP database (for which `dbi` 
		is the database interface) for an action. Currently NO error is thrown if the action is not unique.

		TO DO (maybe): update this function to optionally throw an error if unique actions are desired.

		Any action property that is stored in the BVP databse can be used as a kwarg, including but not 
		limited to the variables listed here. This is intended to be kept open-ended, since it is difficult 
		to know what information future users will want to store about actions.
		"""
		# Allow dbi to be a list of parameters to create a bvpDB. This helps with rendering on cluster 
		# computers; dictionaries are easier to store/pass as arguments than objects. 
		if isinstance(dbi,dict):
			dbi = bvp.bvpDB(**dbi)
		# NO defaults, because what's the point of an empty action?
		if dbi is None:
			# Even this is questionable... Allows for on-the-fly definition of actions, but do we care? Probably not.
			dbob = kwargs
		else:
			# Query database. Update to optionally throw error if object is not unique??
			dbob = dbi.dbi.actions.find_one(kwargs)
		# Set attributes based on database object fields. (Too flexible??)
		for k,v in dbob.items():
			setattr(self,k,v)

	def __repr__(self):
		"""Display string"""
		S = '\n ~A~ bvpAction "%s" ~A~\n'%(self.name)
		if hasattr(self,'cycle') and self.cycle:
			S+='Cyclic action '
		if hasattr(self,'armature') and not self.armature is None:
			S+='for armature class %s\n'%self.armature
		if hasattr(self,'file_name') and not self.file_name is None:
			S+='File name: %s\n'%self.file_name 
		if hasattr(self,'frame_range') and not self.frame_range is None:
			S+='frame range: %s\n, '%repr(self.frame_range)
		# Better is wordnet: insert wordnet labels here (w/ search thru nltk for hyper/hyponyms?)
		if hasattr(self,'semantic_cat') and not self.semantic_cat is None:
			S+=self.semantic_cat[0]
			for s in self.semantic_cat[1:]: S+=', %s'%s
			S+='\n'
		return(S)
