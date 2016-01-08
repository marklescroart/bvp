# Functions for gui

from ..bvpDB import bvpDB
import os

try: 
    import bpy
    is_blender = True
except:
    is_blender = False

if is_blender:
    print("Defining classes...")
    ## -- Base properties for property groups -- ##
    class WordNet_Label(bpy.types.PropertyGroup):
        #bl_idname = "bvp.WordNet_Label"
        name = bpy.props.StringProperty(name="label", default = "")
        frame = bpy.props.IntProperty(default=1)
        id = bpy.props.IntProperty() # necessary?

    class WordNet_Label_List(bpy.types.UIList):
        #bl_idname = "bvp.WordNet_Label_List"
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

    def enum_wn_results(self,context):
        """Enumerate all WordNet synsets (WordNet labels) returned from the most recent lemma query"""
        global wn_results
        out = [("","","")]+[(o['synset'],o['synset']+': '+o['definition'],o['hypernyms']) for o in wn_results]
        return out

    def enum_dbs(self,context):
        """Enumerate all active databases for pymongo server (if running)"""
        try:
            # TO DO: Add ShapeNet / ModelNet to this list?
            dbi = bvpDB(port=dbport)
            dbnm = [(d,d,'') for d in dbi.dbi.client.database_names() if not d in ['local','admin']]
        except:
            dbnm = [('(none)','(none)','')]
        return dbnm

    ## -- General property declarations -- ##
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


        for c in [WordNet_Label,ObjectProps,ActionProps, BGProps, SkyProps,RenderOptions]: 
            # Do these in a separate file? Imported, registered separately? 
            bpy.utils.register_class(c)        
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

        bpy.types.Group.bvpBG = bpy.props.PointerProperty(type=BGProps)
        #bpy.types.Group.is_bg = bpy.props.BoolProperty(name='is_bg',default=False)
        
        bpy.types.Action.bvpAction = bpy.props.PointerProperty(type=ActionProps)
        
        bpy.types.Scene.bvpRenderOptions = bpy.props.PointerProperty(type=RenderOptions)
        ## -- For database management -- ##
        bpy.types.WindowManager.active_db = bpy.props.EnumProperty(items=enum_dbs,name='active_db') 
        bpy.types.WindowManager.active_group = bpy.props.StringProperty(name='active_group',default="") 
        #bpy.types.WindowManager.active_action = bpy.props.StringProperty(name='active_action',default="") 
        bpy.types.WindowManager.query_results = bpy.props.EnumProperty(items=enum_db_results,name='Search results')
        bpy.types.WindowManager.wn_results = bpy.props.EnumProperty(items=enum_wn_results,name='WordNet search results')
        bpy.types.WindowManager.wn_label_index = bpy.props.IntProperty(default=0)
        # Add .WindowManager.bvp.active_xxx?