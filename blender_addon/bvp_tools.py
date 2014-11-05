import bpy
import bvp
import os
from bpy.types import Panel

"""
NOTES
=====

Useful: 
# To show property type:
type(bpy.data.scenes['Scene'].bl_rna.properties['frame_start'])

http://blender.stackexchange.com/questions/15917/populate-a-list-with-custom-property-dictionary-data

# Useful: latest builds by OS
https://builder.blender.org/download/

# Material library:
https://sites.google.com/site/aleonserra/home/scripts/matlib-vx#TOC-Demo-Video:

# Meta-Androcto / Peter Casseta libraries:
# Meta: 
http://blenderartists.org/forum/showthread.php?252957-Cycles_Matlib-Beta-Release!-Help-Wanted!/page4
# Peter Casseta online/offline:
http://blenderartists.org/forum/showthread.php?256334-An-Online-Material-Library-for-Cycles

# Creating objects:
http://wiki.blender.org/index.php/Dev:2.5/Py/Scripts/Cookbook/Code_snippets/Three_ways_to_create_objects

Dialog box example (for saving??)
http://www.blender.org/documentation/blender_python_api_2_57_release/bpy.types.Operator.html

The interface for database selection would benefit from not being fixed - we could add a 
mechanism to add a new database without too much trouble. This would involve changing the 
property type to something other than EnumProperty (which as I understand is fixed)

Useful for lists:
Will need to define a collection property, define the property type with which to populate the list,
and then add the new type and collection type (?) I think...
http://blender.stackexchange.com/questions/15917/populate-a-list-with-custom-property-dictionary-data

Dynamic EnumProperty:
http://blender.stackexchange.com/questions/10910/dynamic-enumproperty-by-type-of-selection

Shit, there's a selected_objects value in bpy.context - who knew?


see the following for bounding boxes:
https://github.com/sambler/addonsByMe/blob/master/create_bound_box.py
"""


bl_info = {
	"name": "BVP tools panel",
	"description": "B.lender V.ision P.roject toolbox panel",
	"author": "Mark Lescroart",
	"version": (0, 1),
	"blender": (2, 72, 0),
	#"location": "File > Import-Export",
	#"warning": "", # used for warning icon and text in addons panel
	#"wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"
	#	   "Scripts/My_Script",
	"category": "3D View"
	}

### --- Misc parameters --- ###
bb_types = ['MESH','LATTICE','ARMATURE'] # Types allowable for computing bounding box of object groups. Add more?
dbport = bvp.Settings['db']['port']
dbpath = bvp.Settings['Paths']['LibDir'] # only necessary for creating client instances...
dbname = 'bvp_1_0' #bvp.Settings['db']['name']
act_parent_file = ""
db_results = []
last_import = ""
### --- Start BVP database server? --- ###

try:
	dbi = bvp.bvpDB(dbname=dbname)
	del dbi
except pymongo.errors.ConnectionError:
	import warnings
	warnings.warn()
	# Subprocess start db server

	# Insert at end if server is started: 
	#import psutil
	#PROCNAME = "mongod"
	#for proc in psutil.process_iter():
    #	if proc.name() == PROCNAME:
    #    	proc.kill()

### --- BVP element properties --- ###
class ObjectProps(bpy.types.PropertyGroup):
	"""Properties for bvpObjects"""
	fp = bpy.data.filepath
	if fp=="":
		pth = ""
	else:
		pth = os.path.split(bpy.data.filepath)[1][:-6]
	name = bpy.props.StringProperty(name='name',default="")
	parent_file = bpy.props.StringProperty(name='parent_file',default=pth)
	real_world_size = bpy.props.FloatProperty(name="real_world_size",min=.001,max=300.,default=1.)
	semantic_cat = bpy.props.StringProperty(name='semantic_cat',default='thing')
	basic_cat = bpy.props.StringProperty(name='basic_cat',default='thing')
	wordnet_label = bpy.props.StringProperty(name='wordnet_label',default='entity.n.01')	
	is_realistic = bpy.props.BoolProperty(name='is_realistic',default=False)
	is_cycles = bpy.props.BoolProperty(name='is_cycles',default=False)
	# Define computed properties (nverts, nfaces, manifold, etc) here, too?
	del fp
	del pth
# To come:
#class BGProps(bpy.types.PropertyGroup):
#	pass

class ActionProps(bpy.types.PropertyGroup):
	"""Properties for bvpActions"""
	act_name = bpy.props.StringProperty(name='act_name',default="")
	parent_file = bpy.props.StringProperty(name='parent_file',default="")
	semantic_cat = bpy.props.StringProperty(name='semantic_cat',default='do')
	wordnet_label = bpy.props.StringProperty(name='wordnet_label',default='do.v.01')
	fps = bpy.props.FloatProperty(name='fps',default=30.,min=15.,max=100.) # 100 is optimistic...
	nframes = bpy.props.IntProperty(name='fps',default=30,min=2,max=1000) # 1000 is also optimistic...
	is_cyclic = bpy.props.BoolProperty()
	is_transitive = bpy.props.BoolProperty()
	is_translating = bpy.props.BoolProperty()
	is_armature = bpy.props.BoolProperty(default=True)
	# Define computed properties (compute from constraints?) (number of bones?)

class SkyProps(bpy.types.PropertyGroup):
	"""Properties for bvpSkies"""
	parent_file = bpy.props.StringProperty(name='parent_file',default="")
	semantic_cat = bpy.props.StringProperty(name='semantic_cat',default='sky')
	wordnet_label = bpy.props.StringProperty(name='wordnet_label',default='sky.n.01')	

'''
# UI list option for displaying databases (more flexible, more space)
class DBprop(bpy.types.PropertyGroup):
	"""Grouped database properties"""
	id = bpy.props.IntProperty()
	port = bpy.props.IntProperty(name='port',default=bvp.Settings['db']['port'])
	path = bpy.props.StringProperty(name='path',default=bvp.Settings['Paths']['LibDir'])
'''

## -- For dynamic EnumProperties -- ##
def enum_groups(self,context):
	ob = context.object
	if len(ob.users_group)==0:
		return [("","No Group",""),]
	else:
		return [(g.name,g.name,"") for g in ob.users_group]

def enum_db_results(self,context):
	"""Enumerate all objects (group names) returned from a database query"""
	global db_results
	out = [("","","")]+[(o['name'],o['name'],','.join(o['semantic_cat'])) for o in db_results]
	return out

def declare_properties():
	'''Declarations of extra object properties

	These properties contain (most of) the meta-data stored about 
	each scene element in the BVP database.

	This doesn't need to be a function, necessarily. Done this way just to 
	keep all the bvp-specific property definitions together.

	TO DO: Un-register them upon close (?)

	DEPRECATED. All objects in DB will need to be updated to put these
	properties onto GROUPS rather than objects. 
	'''
	### --- DEPRECATED --- ###

	# ## -- For both object and background elements -- ##
	# # Real world size
	# bpy.types.Object.RealWorldSize = bpy.props.FloatProperty(name="RealWorldSize",min=.001,max=300.,default=1.)
	# # Imprecise list of semantic labels for an object; for convenience 
	# # (a string, w/ comma-separated descriptors/categories for the object in question)
	# bpy.types.Object.SemanticCat = bpy.props.StringProperty(name='SemanticCat',default='thing')
	# # Precise definitional label for object
	# bpy.types.Object.wordnet_label = bpy.props.StringProperty(name='wordnet_label',default='entity.n.01')
	# # Reasonably realistic-looking, not cartoony or otherwise bad.
	# bpy.types.Object.realistic = bpy.props.BoolProperty(name='realistic',default=False)
	# # Is configured with cycles materials, ready to render with cycles render engine
	# bpy.types.Object.is_cycles = bpy.props.BoolProperty(name='is_cycles',default=False)
	# # Parent file
	# bpy.types.Object.parent_file = bpy.props.StringProperty(name='parent_file',default="")

	## -- Specifically for background elements -- ##
	# Semantic Category of allowable objects (within scene)
	bpy.types.Object.ObjectSemanticCat = bpy.props.StringProperty(name='ObjectSemanticCat',default='thing')
	# Semantic Category of allowable skies (for scene)
	bpy.types.Object.SkySemanticCat = bpy.props.StringProperty(name='SkySemanticCat',default='all') # DomeTex, FlatTex, BlenderSky, Night, Day, etc...
	# Focal length of camera (for background)
	bpy.types.Object.Lens = bpy.props.FloatProperty(name='Lens',min=25.,max=50.,default=50.) # DomeTex, FlatTex, BlenderSky, Night, Day, etc...

	### --- /DEPRECATED --- ###

	## -- By class -- ## 
	bpy.types.Object.groups = bpy.props.EnumProperty(name='groups',description='Groups using this object',items=enum_groups)
	
	bpy.types.Group.bvpObject = bpy.props.PointerProperty(type=ObjectProps)
	bpy.types.Group.is_object = bpy.props.BoolProperty(name='is_object',default=True)

	#bpy.types.Group.bvpBG = bpy.props.PointerProperty(BGProps)
	#bpy.types.Group.is_bg = bpy.props.BoolProperty(name='is_bg',default=True)
	
	bpy.types.Action.bvpAction = bpy.props.PointerProperty(type=ActionProps)
	## -- For database management -- ##
	# active_db
	db_tmp = bvp.bvpDB(dbname=dbname)
	dbnm = [(d,d,'') for d in db_tmp.dbi.connection.database_names() if not d in ['local','admin']]
	# TO DO: Add ShapeNet / ModelNet to this list! 
	bpy.types.WindowManager.active_db = bpy.props.EnumProperty(items=dbnm,name='active_db',default=dbname) 
	bpy.types.WindowManager.active_group = bpy.props.StringProperty(name='active_group',default="") 
	bpy.types.WindowManager.active_action = bpy.props.StringProperty(name='active_action',default="") 
	bpy.types.WindowManager.query_results = bpy.props.EnumProperty(items=enum_db_results,name='Search results')
	# Add .WindowManager.bvp.active_xxx?

### --- Operators --- ###
class NextScene(bpy.types.Operator):
	"""Skip to the next scene"""
	bl_idname = "bvp.nextscene"
	bl_label = "Skip to next scene"
	bl_options = {'REGISTER','UNDO'}
	
	def execute(self,context):
		ScnList = list(bpy.data.scenes)
		ScnIdx = ScnList.index(context.scene)
		if ScnIdx<len(ScnList)-1:
			context.screen.scene = ScnList[ScnIdx+1]
		return {"FINISHED"}

class PrevScene(bpy.types.Operator):
	"""Skip to the previous scene"""
	bl_idname = "bvp.prevscene"
	bl_label = "Skip to previous scene"
	bl_options = {'REGISTER','UNDO'}
	
	def execute(self,context):
		ScnList = list(bpy.data.scenes)
		ScnIdx = ScnList.index(context.scene)
		if ScnIdx>0:
			context.screen.scene = ScnList[ScnIdx-1]
		return {"FINISHED"}

class RescaleGroup(bpy.types.Operator):
	"""Creates a group of Blender objects and standardizes the size.

	Set a group of objects to canonical position (centered, max dimension = 10)
	Position is defined relative to the BOTTOM, CENTER of the object (defined by the  bounding 
	box (maximal extent of vertices, irrespective of the object's origin) 

	Origins of all objects are set to (0,0,0).

	WARNING: NOT NECESSARILY RELIABLE. There is a great deal of variability in the way in which 3D 
	models are stored in the myriad free 3D sites online; thus a GREAT MANY conditional statements
	would be necesary to have a reliably working function. If you want to write such a function, 
	be my guest. In the meantime, use with caution. 

	"""
	bl_idname = "bvp.rescale_group"
	bl_label = "Set up group of objects"
	bl_options = {'REGISTER','UNDO'}
	def execute(self,context):
		scn = bpy.context.scene
		ob_list = [o for o in scn.objects if o.select and not o.type in ['CAMERA']]
		ToSet_Size = 10.0
		ToSet_Loc = (0.0,0.0,0.0)
		ToSet_Rot = 0.0
		# FIRST: Clear parent relationships
		p = [o for o in ob_list if not o.parent and not 'ChildOf' in o.constraints.keys()]
		if len(p)!=1:
			raise Exception('BVP group set-up requires exactly one parent object in the group!')
		else:
			p = p[0]
		np = [o for o in ob_list if o.parent or 'ChildOf' in o.constraints.keys()]
		if p:
			for o in np:
				bvp.utils.blender.grab_only(o)
				bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
				if 'ChildOf' in o.constraints.keys():
					o.constraints.remove(o.constraints['ChildOf'])
		# SECOND: Reposition all object origins 
		(MinXYZ,MaxXYZ) = self.get_group_bounding_box(ob_list)
		BotMid = [(MaxXYZ[0]+MinXYZ[0])/2,(MaxXYZ[1]+MinXYZ[1])/2,MinXYZ[2]]
		bvp.utils.blender.set_cursor(BotMid)
		SzXYZ = []
		for Dim in range(3):
			SzXYZ.append(MaxXYZ[Dim]-MinXYZ[Dim])
		ScaleF = ToSet_Size/max(SzXYZ)
		for o in ob_list:
			bvp.utils.blender.grab_only(o)
			bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
			o.scale = o.scale * ScaleF
			o.location = ToSet_Loc
		# Update scene to reflect changes
		scn.update()
		# THIRD: Re-parent everything
		for o in np:
			bvp.utils.blender.grab_only(p)
			o.select = True
			bpy.ops.object.parent_set()
		# LAST: Create group (if necessary) and name group
		if not ob_list[0].users_group:
			for o in ob_list:
				o.select=True
			bpy.ops.group.create(name=scn.name)
		# Done
		return {"FINISHED"}

	def get_group_bounding_box(self,ob_list):
		'''Returns the maximum and minimum X, Y, and Z coordinates of a set of objects

		Parameters
		----------
		ob_list : list or tuple 
			list of Blender objects for which to get bounding box

		Returns
		-------
		minxyz,maxxyz : lists
			min/max x,y,z coordinates for all objects. Think about re-structuring this to be a
			more standard format for a bounding box. 
		'''
		BBx = list()
		BBy = list()
		BBz = list()
		for ob in ob_list: 
			bvp.utils.blender.grab_only(ob)
			if ob.type in bb_types:
				bpy.ops.object.transform_apply(rotation=True)
			for ii in range(8):
				BBx.append(ob.bound_box[ii][0] * ob.scale[0] + ob.location[0]) 
				BBy.append(ob.bound_box[ii][1] * ob.scale[1] + ob.location[1])
				BBz.append(ob.bound_box[ii][2] * ob.scale[2] + ob.location[2])
		MinXYZ = [min(BBx),min(BBy),min(BBz)]
		MaxXYZ = [max(BBx),max(BBy),max(BBz)]
		# Done
		return MinXYZ,MaxXYZ	

class DBSaveObject(bpy.types.Operator):
	bl_idname = "bvp.db_save_object"
	bl_label = "Save the active object to the active database"
	bl_options = {'REGISTER','UNDO'}
	def execute(self,context):
		wm = context.window_manager
		ob = context.object
		grp = bpy.data.groups[wm.active_group]
		# Parent file nonsense because we can't set bvpObject.parent_file here:
		pfile = grp.bvpObject.parent_file
		thisfile = bpy.data.filepath #if len(bpy.data.filepath)>0 else pfile
		if thisfile=="":
			raise NotImplementedError("Please save this file into %s before trying to save to database."%(os.path.join(dbpath,'Objects/')))		
			# Need to check for over-writing file? 
		if pfile=="":
			pfile = os.path.split(bpy.data.filepath)[1][:-6]
		
		# Compute parameters
		## Poses
		rig = [o for o in grp.objects if o.type=='ARMATURE']
		nposes = None # by default
		if rig:
			if len(rig)>1:
				raise Exception('More than one rig present in group %s! Abort, abort!'%grp.name)
			rig = rig[0]
			if rig.pose_library:
				nposes = len(rig.pose_library.pose_markers)
		## Faces
		try:
			nfaces = sum([len(oo.data.faces) for oo in grp.objects if oo.type=='MESH'])
		except:
			# New for version 2.63 w/ bmeshes:
			nfaces = sum([len(oo.data.polygons) for oo in grp.objects if oo.type=='MESH'])
		## Vertices
		nverts = sum([len(oo.data.vertices) for oo in grp.objects if oo.type=='MESH'])
		## Semantic categories
		semcat = [s.strip() for s in grp.bvpObject.semantic_cat.split(',')]
		semcat = [s.lower() for s in semcat if s]
		## WordNet labels
		wordnet = [s.strip() for s in grp.bvpObject.wordnet_label.split(',')]
		wordnet = [s.lower() for s in wordnet if s]
		#is_manifold = False # worth it? 
		# Create database instance
		dbi = bvp.bvpDB(port=dbport,dbname=wm.active_db)
		# Construct object struct to save
		to_save = dict(
			# Edited through UI
			name=wm.active_group, # also not great.
			parent_file=pfile, # hacky. ugly. 
			wordnet_label=wordnet,
			semantic_cat=semcat,
			basic_cat=grp.bvpObject.basic_cat,
			real_world_size=grp.bvpObject.real_world_size,
			is_realistic=grp.bvpObject.is_realistic,
			is_cycles=grp.bvpObject.is_cycles,
			# Computed
			nfaces=nfaces,
			nvertices=nverts,
			nposes=nposes,
			constraints=None,
			#is_manifold=is_manifold, # worth it? 
			#_id='tempX12345', # dbi.db.id? generate_id? Look up ID? Check database for extant
			)
		dbi.objects.save(to_save)
		save_path = os.path.join(dbpath,'Objects',pfile+'.blend')
		if save_path==thisfile:
			bpy.ops.wm.save_as_mainfile(filepath=save_path)
		else:
			raise NotImplementedError('Still WIP! Just work inside your database files, you lazy bastard!')
			tmpf = '/tmp/action_tempfile.blend' # Set in settings?
			bpy.ops.wm.save_as_mainfile(filepath=tmpf,copy=True)
			script = bvp.utils.basics.load_template('Save') # 'SaveGroup' instead? This script doesn't work yet. Edit <bvp>/Scripts/Template_Save.py
			script.format() # Depends on script
			bvp.blend(script,pfile)		
		return {"FINISHED"}

class WordNetLookup(bpy.types.Operator):
	bl_idname = "bvp.wordnet_lookup"
	bl_label = "Search wordnet for the synsets associated with a word"
	bl_options = {'REGISTER','UNDO'}
	def execute(self,context):
		raise NotImplementedError('Not functioning yet! (Max, get to it!)')
		# An on-the-fly import seems best, so to not insist on WordNet
		# as a dependency outside of the use of this function
		from nltk.corpus import wordnet as wn
		# etc...

## TO DO: 
# class DBSaveBG(bpy.types.Operator):
# 	pass

class DBSaveAction(bpy.types.Operator):
	bl_idname = "bvp.db_save_action"
	bl_label = "Save the active object to the active database"
	bl_options = {'REGISTER','UNDO'}
	def execute(self,context):
		wm = context.window_manager
		ob = context.object
		act = bpy.data.actions[wm.active_action]
		# Compute parameters

		## Frames
		FR = act.animation_data.action.frame_range
		nframes = FR[1]-FR[0]

		## Semantic categories
		semcat = [s.strip() for s in act.bvpAction.semantic_cat.split(',')]
		semcat = [s.lower() for s in semcat if s]
		## WordNet labels
		wordnet = [s.strip() for s in act.bvpAction.wordnet_label.split(',')]
		wordnet = [s.lower() for s in wordnet if s]

		# Get parent file, determine if it is THIS file.
		pfile = act.bvpAction.parent_file
		thisfile = bpy.data.filepath #if len(bpy.data.filepath)>0 else pfile
		if thisfile=="":
			raise NotImplementedError("Please save this file into %s before trying to save to database."%(os.path.join(dbpath,'Actions/')))
			# Need to check for over-writing file? 
		if pfile=="":
			pfile = os.path.split(bpy.data.filepath)[1][:-6]

		# Create database instance
		dbi = bvp.bvpDB(port=dbport,dbname=wm.active_db)
		# Construct action struct to save
		to_save = dict(
			# Edited through UI
			act_name=act.name,
			parent_file=pfile,
			wordnet_label=act.bvpAction.wordnet_label,
			semantic_cat=act.bvpAction.semantic_cat,
			fps=act.bvpAction.fps,
			nframes=nframes,
			is_cyclic=act.bvpAction.is_cyclic,
			is_translating=act.bvpAction.is_translating,
			is_transitive=act.bvpAction.is_transitive,
			is_armature=act.bvpAction.is_armature,
			is_verified=False, # Will be done through database later, once it's in there
			# Computed
			# Constraints?? Bounding box??
			)
		dbi.actions.save(to_save)
		save_path = os.path.join(dbpath,'Actions',pfile+'.blend')
		if pfile==thisfile:
			bpy.ops.wm.save_as_mainfile(filepath=save_path)
		else:
			raise NotImplementedError('Still WIP! Just work inside your database files, you lazy bastard!')
			tmpf = '/tmp/action_tempfile.blend' # Set in settings?
			bpy.ops.wm.save_as_mainfile(filepath=tmpf,copy=True)
			script = bvp.utils.basics.load_template('Save') # This script doesn't work yet. Edit <bvp>/Scripts/Template_Save.py
			script.format() # Depends on script
			bvp.blend(script,pfile)

class DBSearchDialog(bpy.types.Operator):
	bl_idname = "bvp.db_search"
	bl_label = "Query database for:"
	bl_options = {'REGISTER','UNDO'}

	active_db = bpy.props.StringProperty(name="active_db")
	bvp_type = bpy.props.EnumProperty(name='BVP type',
		items=[('action','action',""),
			   ('background','background',""),
			   ('object','object',""),
			   ('sky','sky',""),
			   ('shadow','shadow',"")],
		default='object')
	semantic_cat = bpy.props.StringProperty(name='Loose semantic label',default="")
	wordnet_label =  bpy.props.StringProperty(name='Precise WordNet label',default="")
	ename = bpy.props.StringProperty(name='Group/Action name',default="")
	# Real world size min/max?

	def execute(self, context):
		global db_results
		global last_import
		wm = context.window_manager
		dbi = bvp.bvpDB(dbname=self.active_db)
		props = ['semantic_cat','wordnet_label','ename']
		query = dict((p,getattr(self,p)) for p in props if getattr(self,p))
		print(query) # unnecessary
		db_results = [r for r in dbi.objects.find(query)]
		last_import = self.bvp_type
		from pprint import pprint # unnecessary
		pprint(db_results) # unnecessary
		return {'FINISHED'}
 
	def invoke(self, context, event):
		wm = context.window_manager
		self.active_db = wm.active_db
		return context.window_manager.invoke_props_dialog(self)

class DBImport(bpy.types.Operator):
	bl_idname = "bvp.db_import"
	bl_label = "Import scene element from database"
	bl_options = {'REGISTER','UNDO'}
	proxy_import = False
	def execute(self,context): 
		global db_results
		global last_import
		
		wm = bpy.context.window_manager
		to_import = [d for d in db_results if d['name']==wm.query_results][0]
		if last_import=='object':
			print('--- importing: ---')
			print(to_import)
			O = bvp.bvpObject(**to_import)
			O.Place(proxy=self.proxy_import)
		elif last_import=='action':
			raise NotImplementedError('Not yet! need to apply actions to objects!')
		return {'FINISHED'}

class DBImportProxy(DBImport,bpy.types.Operator):
	bl_idname = "bvp.db_import_proxy"
	bl_label = "Import scene element from database (proxy only)"
	bl_options = {'REGISTER','UNDO'}

	proxy_import = True

### --- Misc. supporting classes --- ###
'''
# UI list option for displaying databases (more flexible, more space)
# Need database creation option (?)
class BVP_DB_LIST(bpy.types.UIList):
	"""List class to establish database list in DB tools panel"""
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
		split = layout.split(0.2)
		split.label(str(item.id)) # item.name
		split.prop(item, "name", text="", emboss=False, translate=False) #, icon='BORDER_RECT'
'''

### --- Panels --- ###

class View3DPanel():
	"""SettingProperties for all child classes"""
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'TOOLS'
	bl_category = 'BVP'
	bl_context = "objectmode"

class BVP_PANEL_db_tools(View3DPanel,Panel):
	"""Creates a BVP panel in the Tools window for database actions"""
	bl_label = "Database tools"
	bl_idname = "BVP_db_tools"

	def draw(self, context):
		# Get window manager / associated database list
		wm = context.window_manager
		# Head title
		layout = self.layout
		row = layout.row()
		# # For extensible list of databases, maybe use the following line.
		# # It's less compact but more flexible; requires definition of 'db_index'
		# # property. Maybe implement later.
		# row.template_list("BVP_DB_LIST", "", wm, "active_db",wm,"db_index")
		spl = layout.split()
		col = spl.column()
		col.label('Active DB:')
		col = spl.column()
		col.prop(wm, "active_db",text='')

		row = layout.row()
		row.operator("bvp.db_search",text="Search DB")
		row = layout.row()
		row.prop(wm,'query_results')
		if len(db_results)>0:
			spl = layout.split()
			col = spl.column()
			col.operator('bvp.db_import',text='Place Full')
			col = spl.column()
			col.operator('bvp.db_import_proxy',text='Place Proxy')
			#col.label('Import Full')

class BVP_PANEL_object_tools(View3DPanel,Panel):
	"""Creates a BVP panel in the Tools window"""
	bl_label = "Object tools"
	bl_idname = "BVP_object_tools"

	# NOTE: I don't want to use poll, because I want to still display this window 
	# if there isn't an active object (for Create group / rescale button)
	def draw(self, context):
		layout = self.layout
		# Get currently-selected object
		ob = context.object
		scene = context.scene	
		wm = context.window_manager
		# Object or no
		if ob is None: # better to use poll?
			row = layout.row()
			row.label('(No object selected)')
			wm.active_group = ""
		else:
			wm.active_group = ob.groups
			row = layout.row()
			if len(ob.users_group)<1: #ob.dupli_groups is None:
				row.label(text='(no BVP object group)')
				row = layout.row()
				row.operator('bvp.rescale_group',text='Create group & rescale')	
			else:
				grp = bpy.data.groups[wm.active_group]
				spl = layout.split()
				
				## -- 1st column -- ##
				col = spl.column()
				col.label("BVP object:")
				col.label("File:")
				col.label("Labels:")
				col.label("Basic cat:")
				col.label("WordNet:")
				col.label('Real size:')
				# Boolean properties
				col.prop(grp.bvpObject,'is_realistic',text='realistic')
				# Button for re-scaling object groups 
				col.operator('bvp.rescale_group',text='Rescale')	
				
				## -- 2nd column -- ##
				col = spl.column()
				col.prop(ob,'groups',text="")
				col.prop(grp.bvpObject,'parent_file',text='')
				col.prop(grp.bvpObject,'semantic_cat',text='')
				col.prop(grp.bvpObject,'basic_cat',text='')
				col.prop(grp.bvpObject,'wordnet_label',text='')
				col.prop(grp.bvpObject,'real_world_size',text='')
				col.prop(grp.bvpObject,'is_cycles',text='cycles')
				# Button for re-scaling object groups 
				col.operator('bvp.db_save_object',text='Save to DB')

class BVP_PANEL_action_tools(View3DPanel,Panel):
	"""Creates a BVP actions panel in the Tools window"""
	bl_label = "Action tools"
	bl_idname = "BVP_action_tools"

	# Don't display this dialog if there isn't an action available.
	@classmethod
	def poll(self,context):
		if context.object:
			if context.object.animation_data:
				return True
	def draw(self, context):
		# Get currently-selected object
		ob = context.object	
		wm = context.window_manager
		act = ob.animation_data.action
		wm.active_action = act.name
		# Layout
		layout = self.layout
		spl = layout.split()	
		## -- 1st column -- ##
		col = spl.column()
		col.label("Name:")
		col.label("File:")
		col.label("Labels:")
		col.label("WordNet:")
		col.label("Frame rate:")
		# Boolean properties
		col.prop(act.bvpAction,'is_cyclic',text='cyclic')
		col.prop(act.bvpAction,'is_translating',text='translating')
		col.operator('bvp.wordnet_lookup',text='Search WordNet')
		## -- 2nd column -- ##
		col = spl.column()
		col.prop(act,'name',text="")
		col.prop(act.bvpAction,'parent_file',text='')
		col.prop(act.bvpAction,'semantic_cat',text='')
		col.prop(act.bvpAction,'wordnet_label',text='')
		col.prop(act.bvpAction,'fps',text="")
		# Boolean properties
		col.prop(act.bvpAction,'is_transitive',text='transitive')
		col.prop(act.bvpAction,'is_armature',text='armature')
		# Button for re-scaling object groups 
		col.operator('bvp.db_save_action',text='Save to DB')
		if isinstance(ob.data,bpy.types.Armature):
			row = layout.row()
			row.label('%d bones'%len(ob.data.bones))

class BVP_PANEL_scene_tools(View3DPanel,Panel):
	"""Creates a BVP panel in the Tools window for scene actions"""
	bl_label = "Scene tools"
	bl_idname = "BVP_scene_tools"

	def draw(self, context):
		layout = self.layout
		# Head title
		layout.label(text="Navigation")
		# Buttons for scene navigation
		row = layout.row(align=True)
		row.operator('bvp.nextscene',text='Prev')
		row.operator('bvp.prevscene',text='Next')
		# Select by list? (template_ID?) This will make it easier 
		# to work in the full-screen 3D view window
		# Get current scene
		scene = context.scene
		# TO DO:
		row = layout.row()
		row.label('Background properties:')
		row = layout.row()
		row.label('(Work in progress)')
		# Search through scene objects to determine if any are BVP bg objects
		# Display bvpBG properties (constraints,realworldsize,wordnet_label,etc...)
		# Editing:
		# Buttons to add constraints of different types
		# Buttons to test constraints / reset scene
		# Buttons to add sky

def register():
	# Order of registering props/object should perhaps be examined for optimality...
	# It works this way, but it doesn't seem clean.
	for c in [ObjectProps,ActionProps]: #, BGProps, SkyProps]: 
		# Do these in a separate file? Imported, registered separately? 
		bpy.utils.register_class(c)
	declare_properties()
	# Lists again for panels, operators?
	bpy.utils.register_module(__name__)
	
	#bpy.types.WindowManager.db_list = bpy.props.CollectionProperty(type=DBprop) #name='Databases',
	#bpy.types.WindowManager.db_index = bpy.props.IntProperty()
	#wm = bpy.context.window_manager
	#wm.db_index = 0

def unregister():
	# Un-register classes(necessary?)
	#for c in [ObjectProps,ActionProps]: #ActionProps, BGProps]: 
	#	# Do these in a separate file? Imported, registered separately? 
	#	bpy.utils.unregister_class(c)
	bpy.utils.unregister_module(__name__)
	# Delete temp properties
	del bpy.types.WindowManager.active_db
	del bpy.types.WindowManager.active_group
	del bpy.types.WindowManager.active_action
	del bpy.types.WindowManager.query_results
	# More? 
	
if __name__ == "__main__":
	# declare_properties() #(?)
	register()
