"""
This is the graphical interface add-on to Blender for the B.lender V.ision P.roject (bvp) python module. 

It's possible to use bvp without actually opening Blender, but if you want to, this GUI is designed to 
make it easier to:
- modify scene elements (objects, backgrounds, actions, skies, and shadows) in your bvp database
- create, edit, modify, and save scenes
- label certian properties of new scene elements
"""

"""
NOTES
=====

TO DO: 
- Start/stop database buttons from top DBtools pane
- Mechanism to add new databases from DBtools pane (with setup of folders??)
- Break this ridiculous file up into multiple files. This is approaching 1,000 lines long. 

Check out http://www/wiki/Useful_Blender_Links for misc. tips on objects, material libraries, etc - 
need to compile those into a list of useful Blenderization on a public web page

Shit, there's a selected_objects value in bpy.context - who knew?
"""

import bpy
import bvp
import os
from bpy.types import Panel
import numpy as np


bl_info = {
    "name": "BVP tools panel",
    "description": "B.lender V.ision P.roject toolbox panel",
    "author": "Mark Lescroart",
    "version": (0, 1),
    "blender": (2, 72, 0),
    #"location": "File > Import-Export",
    #"warning": "", # used for warning icon and text in addons panel
    #"wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"
    #      "Scripts/My_Script",
    "category": "3D View"
    }

### --- Misc parameters --- ###
bb_types = ['MESH','LATTICE','ARMATURE'] # Types allowable for computing bounding box of object groups. Add more?
#dbname = bvp.config.get('db', 'dbname')
#dbhost = bvp.config.get('db', 'dbhost')
dbi = bvp.DBInterface()
dbpath = dbi.db_dir # only necessary for creating client instances...
to_save = {}
db_results = []
last_import = ""
wn_results = []


## -- Base properties for property groups -- ##
class WordNet_Label(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty(name="label", default = "")
    frame = bpy.props.IntProperty(default=1)
    id = bpy.props.IntProperty() # necessary?

class WordNet_Label_List(bpy.types.UIList):
## -- Display UI list -- ##
    """List class to set up display of WordNet label list"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split(0.2)
        split.label(str(item.frame)) # item.name
        split.prop(item, "name", text="", emboss=False, translate=False) #, icon='BORDER_RECT'

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

class ActionProps(bpy.types.PropertyGroup):
    """Properties for bvpActions"""
    # Set act_name default to bpy.context.object.animation_data.action.name? Will that dynamically update? 
    # Or: new wisdom: these necessarily depend on the current action & file, so just read those properties
    # rather than creating duplicate properties just to have everything in the same place.
    #act_name = bpy.props.StringProperty(name='act_name',default="")
    #parent_file = bpy.props.StringProperty(name='parent_file',default="")
    #semantic_cat = bpy.props.StringProperty(name='semantic_cat',default='')
    wordnet_label = bpy.props.CollectionProperty(type=WordNet_Label)
    fps = bpy.props.FloatProperty(name='fps',default=30.,min=15.,max=100.) # 100 is optimistic...
    nframes = bpy.props.IntProperty(name='fps',default=30,min=2,max=1000) # 1000 is also optimistic...
    is_cyclic = bpy.props.BoolProperty()
    is_broken = bpy.props.BoolProperty()
    bg_interaction = bpy.props.BoolProperty()
    obj_interaction = bpy.props.BoolProperty()
    is_translating = bpy.props.BoolProperty()
    is_armature = bpy.props.BoolProperty(default=True)
    is_interactive = bpy.props.BoolProperty()
    is_animal = bpy.props.BoolProperty()
    # Define computed properties (compute from constraints?) (number of bones?)

class BGProps(bpy.types.PropertyGroup):
    """Properties for bvpSkies"""
    parent_file = bpy.props.StringProperty(name='parent_file',default="")
    semantic_cat = bpy.props.StringProperty(name='semantic_cat',default='sky')
    wordnet_label = bpy.props.StringProperty(name='wordnet_label',default='sky.n.01')   

class SkyProps(bpy.types.PropertyGroup):
    """Properties for bvpSkies"""
    parent_file = bpy.props.StringProperty(name='parent_file',default="")
    semantic_cat = bpy.props.StringProperty(name='semantic_cat',default='sky')
    wordnet_label = bpy.props.StringProperty(name='wordnet_label',default='sky.n.01')   

class RenderOptions(bpy.types.PropertyGroup):
    """Properties for bvpSkies"""
    do_image = bpy.props.BoolProperty(default=True)
    do_zdepth = bpy.props.BoolProperty(default=False)
    do_masks = bpy.props.BoolProperty(default=False)
    do_normals = bpy.props.BoolProperty(default=False)


'''
# UI list option for displaying databases (more flexible, more space)
class DBprop(bpy.types.PropertyGroup):
    """Grouped database properties"""
    id = bpy.props.IntProperty()
    port = bpy.props.IntProperty(name='port',default=bvp.Settings['db']['port'])
    path = bpy.props.StringProperty(name='path',default=bvp.Settings['Paths']['LibDir'])
'''

## -- For dynamic EnumProperties -- ##
def enum_groups(self, context):
    ob = context.object
    if len(ob.users_group)==0:
        return [("","No Group",""),]
    else:
        return [(g.name,g.name,"") for g in ob.users_group]

def enum_db_results(self, context):
    """Enumerate all objects (group names) returned from a database query"""
    global db_results
    out = [("","","")]+[(o['name'],o['name'],','.join(o['semantic_cat'])) for o in db_results]
    return out

def enum_wn_results(self, context):
    """Enumerate all WordNet synsets (WordNet labels) returned from the most recent lemma query"""
    global wn_results
    out = [("","","")]+[(o['synset'],o['synset']+': '+o['definition'],o['hypernyms']) for o in wn_results]
    return out

def enum_dbs(self, context):
    """Enumerate all active databases for couchdb server (if running)"""
    try:
        # TO DO: Add ShapeNet / ModelNet to this list?
        dbi = bvp.DBInterface()
        dbnm = [(d, d, '') for d in dbi.dbconn if not d in ['_replicator', '_users', 'test']]
    except:
        dbnm = [('(none)','(none)','')]
    return dbnm

## -- General property declarations -- ##
def declare_properties():
    """Declarations of extra object properties

    These properties contain (most of) the meta-data stored about 
    each scene element in the BVP database.

    This doesn't need to be a function, necessarily. Done this way just to 
    keep all the bvp-specific property definitions together.

    TO DO: Un-register them upon close (?)

    DEPRECATED. All objects in DB will need to be updated to put these
    properties onto GROUPS rather than objects. 
    """
    ### --- DEPRECATED --- ###

    # ## -- For both object and background elements -- ##
    # # Real world size
    # bpy.types.Object.RealWorldSize = bpy.props.FloatProperty(name="RealWorldSize",min=.001,max=300.,default=1.)
    # # Imprecise list of semantic labels for an object; for convenience 
    # # (a string, w/ comma-separated descriptors/categories for the object in question)
    # bpy.types.Object.semantic_category = bpy.props.StringProperty(name='semantic_category',default='thing')
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
    bpy.types.Object.sky_semantic_category = bpy.props.StringProperty(name='sky_semantic_category',default='all') # DomeTex, FlatTex, BlenderSky, Night, Day, etc...
    # Focal length of camera (for background)
    bpy.types.Object.Lens = bpy.props.FloatProperty(name='Lens',min=25.,max=50.,default=50.) # DomeTex, FlatTex, BlenderSky, Night, Day, etc...

    ### --- /DEPRECATED --- ###

    ## -- By class -- ## 
    bpy.types.Object.groups = bpy.props.EnumProperty(name='groups',description='Groups using this object',items=enum_groups)
    
    bpy.types.Group.Object = bpy.props.PointerProperty(type=ObjectProps)
    bpy.types.Group.is_object = bpy.props.BoolProperty(name='is_object',default=True)

    bpy.types.Group.Background = bpy.props.PointerProperty(type=BGProps)
    #bpy.types.Group.is_bg = bpy.props.BoolProperty(name='is_bg',default=False)
    
    bpy.types.Action.Action = bpy.props.PointerProperty(type=ActionProps)
    
    bpy.types.Scene.bvpRenderOptions = bpy.props.PointerProperty(type=RenderOptions)
    ## -- For database management -- ##
    bpy.types.WindowManager.active_db = bpy.props.EnumProperty(items=enum_dbs,name='active_db') 
    bpy.types.WindowManager.active_group = bpy.props.StringProperty(name='active_group',default="") 
    #bpy.types.WindowManager.active_action = bpy.props.StringProperty(name='active_action',default="") 
    bpy.types.WindowManager.query_results = bpy.props.EnumProperty(items=enum_db_results,name='Search results')
    bpy.types.WindowManager.wn_results = bpy.props.EnumProperty(items=enum_wn_results,name='WordNet search results')
    bpy.types.WindowManager.wn_label_index = bpy.props.IntProperty(default=0)
    # Add .WindowManager.bvp.active_xxx?

### --- Operators --- ###
class NextScene(bpy.types.Operator):
    """Skip to the next scene"""
    bl_idname = "bvp.nextscene"
    bl_label = "Skip to next scene"
    bl_options = {'REGISTER','UNDO'}
    
    def execute(self, context):
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
    
    def execute(self, context):
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
    def execute(self, context):
        scn = context.scene
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
        """Returns the maximum and minimum X, Y, and Z coordinates of a set of objects

        Parameters
        ----------
        ob_list : list or tuple 
            list of Blender objects for which to get bounding box

        Returns
        -------
        minxyz,maxxyz : lists
            min/max x,y,z coordinates for all objects. Think about re-structuring this to be a
            more standard format for a bounding box. 
        """
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
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        wm = context.window_manager
        ob = context.object
        grp = bpy.data.groups[wm.active_group]
        # Parent file nonsense because we can't set Object.parent_file here:
        pfile = grp.Object.parent_file
        thisfile = bpy.data.filepath #if len(bpy.data.filepath)>0 else pfile
        if thisfile=="":
            raise NotImplementedError("Please save this file into %s before trying to save to database."%(os.path.join(dbi.db_dir,'Objects/')))     
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
        semcat = [s.strip() for s in grp.Object.semantic_cat.split(',')]
        semcat = [s.lower() for s in semcat if s]
        ## WordNet labels
        wordnet = [s.strip() for s in grp.Object.wordnet_label.split(',')]
        wordnet = [s.lower() for s in wordnet if s]
        #is_manifold = False # worth it? 
        # Create database instance
        dbi = bvp.DBInterface(dbname=wm.active_db)
        # Construct object struct to save
        to_save = dict(
            # Edited through UI
            name=wm.active_group, # also not great.
            type='Object',
            fname=pfile + '.blend', # hacky. ugly. 
            wordnet_label=wordnet,
            semantic_category=semcat,
            basic_category=grp.Object.basic_cat,
            real_world_size=grp.Object.real_world_size,
            is_realistic=grp.Object.is_realistic,
            is_cycles=grp.Object.is_cycles,
            # Computed
            n_faces=nfaces,
            n_vertices=nverts,
            n_poses=nposes,
            constraints=None,
            #is_manifold=is_manifold, # worth it? 
            #_id='tempX12345', # dbi.db.id? generate_id? Look up ID? Check database for extant
            )
        # Create object instance instead, call save method? NEED ID...
        dbi.put_document(to_save)
        save_path = os.path.join(dbpath, 'Object', pfile + '.blend')
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

## TO DO: 
# class DBSaveBG(bpy.types.Operator):
#   pass

class DBSaveAction(bpy.types.Operator):
    bl_idname = "bvp.db_save_action"
    bl_label = "Save action to active database"
    bl_options = {'REGISTER','UNDO'}
    # Properties
    do_save = bpy.props.BoolProperty(name='overwrite',default=True)
    # Methods
    def execute(self, context):
        global to_save
        wm = context.window_manager
        # Create database instance
        dbi = bvp.DBInterface(dbname=wm.active_db)

        if self.do_save:
            print('Saving %s in database'%repr(to_save))
            # Save in database
            dbi.put_document(to_save)
            # Save parent file
            save_path = os.path.join(dbpath,'Action',to_save['file_name'])
            print('NOT saving %s'%save_path)
            #bpy.ops.wm.save_mainfile(filepath=save_path)
        else:
            # NOOOOOO!
            print("Aborting - nothing saved!")
        # Cleanup
        to_save = {}
        #   # Eventually, I would like to add the ability to append the active action to another file
        #   raise NotImplementedError('Still WIP! Just work inside your database files, you lazy bastard!')
        #   tmpf = '/tmp/action_tempfile.blend' # Set in settings?
        #   bpy.ops.wm.save_as_mainfile(filepath=tmpf,copy=True)
        #   script = bvp.utils.basics.load_template('Save') # This script doesn't work yet. Edit <bvp>/Scripts/Template_Save.py
        #   script.format() # Depends on script
        #   bvp.blend(script,pfile)
        return {'FINISHED'}
        
    def invoke(self, context,event):
        global bvpact
        bvpact = Action.from_blender(context, dbi)
        # (get docdict)
        chk = dbi.query(**bvpact.docdict)

        ## OLD
        # Create database instance
        dbi = bvp.DBInterface(port=dbport,dbname=wm.active_db)
        # Check for existence of to_save in database
        chk = dbi.dbi.Action.find_one(dict(name=to_save['name']))
        print("chk is: ")
        print(chk)
        if chk is None:
            self.do_save = True
            return self.execute(context) #{'RUNNING_MODAL'} #wm.invoke_props_dialog(self)
        else:
            self.do_save = False
            to_save['_id'] = chk['_id']
            return wm.invoke_props_dialog(self)

# Eventual class to start up database server
# Look into SQLite!
# class DBStartup(bpy.types.Operator):
#   try:
#       dbi = bvp.DBInterface(dbname=dbname)
#       del dbi
#   except pymongo.errors.ConnectionError:
#       import warnings
#       warnings.warn('Unable to initialize pymongo server! You''re probably borked!')

class DBSearchDialog(bpy.types.Operator):
    bl_idname = "bvp.db_search"
    bl_label = "Query database for:"
    bl_options = {'REGISTER','UNDO'}
    # Use wm.active_db?? But we probably can't change that here.
    active_db = bpy.props.StringProperty(name="Current database")
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
        wm = context.window_manager # Not necessary??
        dbi = bvp.DBInterface(dbname=self.active_db)
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

        # etc...

class WordNetSearchDialog(bpy.types.Operator):
    bl_idname = "bvp.wn_search"
    bl_label = "Query WordNet for existence of lemma:"
    bl_options = {'REGISTER','UNDO'}
    lemma = bpy.props.StringProperty(name='Search word (lemma)',default="")
    # Real world size min/max?
    
    def get_wn_synsets(self,lemma):
        """Get all synsets for a word, return a list of [wordnet_label,definition, hypernym_string]
        for all synsets returned."""
        from nltk.corpus import wordnet as wn
        synsets = wn.synsets(lemma)
        out = []
        for s in synsets:
            if not '.v.' in s.name(): continue # only verbs!
            hyp = ''
            for ii,ss in enumerate(s.hypernym_paths()):
                try:
                    hyp+=(repr([hn.name() for hn in ss])+'\n')
                except:
                    hyp+='FAILED for %dth hypernym\n'%ii
            out.append(dict(synset=s.name(), definition=s.definition(),hypernyms=hyp))
        return out

    def execute(self, context):
        global wn_results
        wm = bpy.context.window_manager
        wn_results = self.get_wn_synsets(self.lemma)
        return {'FINISHED'}
 
    def invoke(self, context, event):
        print("Invoking WordNetSearchDialog!")
        return context.window_manager.invoke_props_dialog(self)

# to clear:
# wm.categories.clear()
class WordNetAddLabel(bpy.types.Operator):
    bl_idname = "bvp.wn_addlabel"
    bl_label = "Add current wordnet result as a label for group/action"
    bl_options = {'REGISTER','UNDO'}
    def execute(self, context): 
        # Add current label at current frame
        wm = context.window_manager
        act = context.object.animation_data.action
        added = act.Action.wordnet_label.add()
        added.name = wm.wn_results
        added.frame = bpy.context.scene.frame_current
        return {'FINISHED'}

class WordNetRemoveLabel(bpy.types.Operator):
    bl_idname = 'bvp.wn_removelabel'
    bl_label = "remove currently highlighted label"
    bl_options = {'REGISTER','UNDO'}
    def execute(self, context): 
        wm = context.window_manager
        act = context.object.animation_data.action
        act.Action.wordnet_label.remove(wm.wn_label_index)
        return {'FINISHED'}

class DBImport(bpy.types.Operator):
    bl_idname = "bvp.db_import"
    bl_label = "Import scene element from database"
    bl_options = {'REGISTER','UNDO'}
    proxy_import = False
    def execute(self, context): 
        global db_results
        global last_import
        
        wm = bpy.context.window_manager
        to_import = [d for d in db_results if d['name']==wm.query_results][0]
        if last_import=='object':
            print('--- importing: ---')
            print(to_import)
            O = bvp.Object(**to_import)
            O.Place(proxy=self.proxy_import)
        elif last_import=='action':
            raise NotImplementedError('Not yet! need to apply actions to objects!')
        return {'FINISHED'}

class DBImportProxy(DBImport,bpy.types.Operator):
    bl_idname = "bvp.db_import_proxy"
    bl_label = "Import scene element from database (proxy only)"
    bl_options = {'REGISTER','UNDO'}

    proxy_import = True

class ClipFrames(bpy.types.Operator):
    bl_idname = "bvp.clip_to_action"
    bl_label = "Clip scene frames to begin/end of action"
    bl_options = {'REGISTER','UNDO'}
    def execute(self, context):         
        scn = bpy.context.scene
        act = bpy.context.object.animation_data.action
        scn.frame_start = np.floor(act.frame_range[0])
        scn.frame_end = np.ceil(act.frame_range[1])
        return {'FINISHED'}
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

class RenderPanel():
    """SettingProperties for all child classes"""
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = 'BVP'
    #bl_context = "objectmode"


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
                col.prop(grp.Object,'is_realistic',text='realistic')
                # Button for re-scaling object groups 
                col.operator('bvp.rescale_group',text='Rescale')    
                
                ## -- 2nd column -- ##
                col = spl.column()
                col.prop(ob,'groups',text="")
                col.prop(grp.Object,'parent_file',text='')
                col.prop(grp.Object,'semantic_cat',text='')
                col.prop(grp.Object,'basic_cat',text='')
                col.prop(grp.Object,'wordnet_label',text='')
                col.prop(grp.Object,'real_world_size',text='')
                col.prop(grp.Object,'is_cycles',text='cycles')
                # Button for re-scaling object groups 
                col.operator('bvp.db_save_object',text='Save to DB')

class BVP_PANEL_action_tools(View3DPanel,Panel):
    """Creates a BVP actions panel in the Tools window"""
    bl_label = "Action tools"
    bl_idname = "BVP_action_tools"

    # Don't display this dialog if there isn't an action available.
    @classmethod
    def poll(self, context):
        if context.object:
            if context.object.animation_data:
                return True
    def draw(self, context):
        # Get currently-selected object
        ob = context.object 
        wm = context.window_manager
        act = ob.animation_data.action
        #wm.active_action = act.name
        # Layout
        layout = self.layout
        spl = layout.split()
        ## -- 1st column -- ##
        col = spl.column()
        col.label("Name:")
        #col.label("File:") # dead
        #col.label("Labels:") # dead
        col.operator('bvp.wn_search',text='Search WordNet')
        col.label("WordNet labels:")
        
        ## -- 2nd column -- ##
        col = spl.column()
        col.prop(act,'name',text="")
        #col.prop(act.Action,'parent_file',text='')
        #col.prop(act.Action,'semantic_cat',text='')
        row = col.row(align=True)
        row.prop(wm,'wn_results',text="")
        #row.prop(wm,'label_frame',text="")
        row.operator('bvp.wn_addlabel',text="Add label")
        row = layout.row()
        row.template_list("WordNet_Label_List", "wordnet labels", act.Action, "wordnet_label",wm,"wn_label_index")
        col = row.column(align=True)
        col.operator("bvp.wn_removelabel", icon='ZOOMOUT', text="")
        #col.operator("object.material_slot_remove", icon='ZOOMOUT', text="")

        row = layout.row()
        # Boolean properties - column 1
        spl = layout.split()        
        col = spl.column()
        col.prop(act.Action,'is_cyclic',text='cyclic')
        col.prop(act.Action,'bg_interaction',text='needs bg')
        col.prop(act.Action,'is_translating',text='translating')
        col.prop(act.Action,'is_interactive',text='interactive')
        # Boolean properties - column 2
        col = spl.column()
        col.prop(act.Action,'is_broken',text='broken')
        col.prop(act.Action,'obj_interaction',text='needs obj.')
        col.prop(act.Action,'is_armature',text='armature')
        col.prop(act.Action,'is_animal',text='animal/unique')
        ## -- Break -- ##
        spl = layout.split()
        col = spl.column()
        # Column 1: Clip frames
        col.operator('bvp.clip_to_action',text='Clip frames')
        # Column 2: Save to DB when done
        col = spl.column()
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
        row.operator('bvp.prevscene',text='Prev')
        row.operator('bvp.nextscene',text='Next')
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
        # Display Background properties (constraints,realworldsize,wordnet_label,etc...)
        # Editing:
        # Buttons to add constraints of different types
        # Buttons to test constraints / reset scene
        # Buttons to add sky

class BVP_PANEL_render(RenderPanel,Panel):
    """Creates a BVP panel in the Tools window for scene actions"""
    bl_label = "BVP rendering tools"
    bl_idname = "BVP_render_tools"

    def draw(self, context):
        scn = context.scene
        layout = self.layout
        # Head title
        layout.label(text="BVP rendering tools")
        # Buttons for scene navigation
        row = layout.row()
        spl = layout.split()
        # Column 1      
        col = spl.column()
        col.prop(scn.bvpRenderOptions,'do_image',text='image')
        col.prop(scn.bvpRenderOptions,'do_masks',text='masks')
        col = spl.column()
        col.prop(scn.bvpRenderOptions,'do_zdepth',text='z depth')
        col.prop(scn.bvpRenderOptions,'do_normals',text='normals')
        #row.operator('bvp.prevscene',text='Prev')
        #row.operator('bvp.nextscene',text='Next')
        # Select by list? (template_ID?) This will make it easier 
        # to work in the full-screen 3D view window
        row = layout.row()
        row.label('BVP stuff properties:')
        row = layout.row()
        row.label('for scene: %s'%context.scene.name)
        # Search through scene objects to determine if any are BVP bg objects
        # Display Background properties (constraints,realworldsize,wordnet_label,etc...)
        # Editing:
        # Buttons to add constraints of different types
        # Buttons to test constraints / reset scene
        # Buttons to add sky


def register():
    # Order of registering props/object should perhaps be examined for optimality...
    # It works this way, but it doesn't seem clean.
    for c in [WordNet_Label,ObjectProps,ActionProps, BGProps, SkyProps,RenderOptions]: 
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
    #   # Do these in a separate file? Imported, registered separately? 
    #   bpy.utils.unregister_class(c)
    bpy.utils.unregister_module(__name__)
    # Delete temp properties
    del bpy.types.WindowManager.active_db
    del bpy.types.WindowManager.active_group
    #del bpy.types.WindowManager.active_action
    del bpy.types.WindowManager.query_results
    del bpy.types.WindowManager.wn_results
    # More? 
    
if __name__ == "__main__":
    # declare_properties() #(?)
    register()
