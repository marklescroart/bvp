# Imports
import os
import numpy as np
from .mapped_class import MappedClass
from .. import utils as bvpu
from ..options import config

try: 
    import bpy
    is_blender = True
except ImportError:
    is_blender = False
    pass

class Action(MappedClass):
    """Layer of abstraction for armature-based actions (imported from other files) in Blender scenes.
    """
    def __init__(self, name='DummyAction', fname=None, armature='mixamo_human', type='Action',
        wordnet_label=None, wordnet_frames=None, is_armature=True, _id=None, _rev=None, n_frames=None,
        is_cyclic=False, is_translating=False, is_broken=False, bg_interaction=False, obj_interaction=False, 
        is_interactive=False, is_animal=False, fps=24, min_xyz=None, max_xyz=None, min_xyz_trajectory=None, max_xyz_trajectory = None, dbi=None):
        """Class to store an armature-based action for an object in a BVP scene. 

        Parameters
        ----------
        name : string
            ID for object (unique name for an object in the database, which is also (as of 2014.09, but
            this may change) the name for the Blender group in the archival .blend file)
        fname : string
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
        min_xyz_trajectory : list of tuples
            min points of the object's bounding box at different points in trajectory
        max_xyz_trajectory : list of tuples
            max points of the object's bounding box at different points in trajectory
        dbi : DBInterface object
            Database interface (for saving, loading, etc)

        Returns
        -------
        Action instance

        """
        # Transplanted from vm_tools - use me? 
        # inpt = locals()
        # self.type = 'Action'
        # for k, v in inpt.items():
        #     if not k in ['self']:
        #         setattr(self, k, v)

        # Quick setting of attributes
        inpt = locals()
        self.type = 'Action'
        for k, v in inpt.items(): 
            if not k in ('self', 'type'):
                if v == 'None':
                    setattr(self, k, None)
                else:
                    setattr(self, k, v)        # Set _temp_params, etc.
        self._temp_fields = []
        self._data_fields = []
        # self.motion_trajectory = [(0,0,0) for i in range(5)]

    #def save(self, context):
    #    """Save Action to database; must be called inside an active Blender session"""
    #    if not is_blender:
    #        raise Exception("Can't save while operating outside of Blender!")
    #    pass

    def link(self):
        # TODO: move the whole add_action function here. 
        # Seems dumb to have it elsewhere, only used here.
        return bvpu.blender.add_action(self.name, self.fname, self.path)

    @classmethod
    def from_blender(cls, context, dbi):
        """Create an Action from a selected object in Blender. 

        This function only works within an active Blender session. The selected object must be an armature with
        an action linked to it. 

        Parameters
        ----------
        context : bpy context
            context for determining selected object, etc
        """
        # Idiot-proofing
        assert is_blender, "from_blender() only works within an active blender session."
        n_samples = 5 # Number of samples for object trajectory (for bounding box across time)
        # Get relevant blender objects 
        wm = context.window_manager
        ob = context.object
        act = ob.animation_data.action
        # Compute parameters
        ## Frames
        n_frames = np.floor(act.frame_range[1])-np.ceil(act.frame_range[0])
        ## WordNet labels
        wordnet_label = [s.name for s in act.Action.wordnet_label]
        wordnet_frames = [s.frame for s in act.Action.wordnet_label]
        ## Bounding box
        if isinstance(ob.data, bpy.types.Armature):
            # Get child objects, armatures have no position information
            ob_list = [ob]+list(ob.children)
        scn = context.scene
        mn, mx = [], []
        st = int(np.floor(act.frame_range[0]))
        fin = int(np.ceil(act.frame_range[1]))
        for fr in range(st, fin):
            scn.frame_set(fr)
            if bpy.app.version < (2, 80, 0):
                scn.update()
            else:
                bpy.context.view_layer.update()
            # Re-visit me
            mntmp, mxtmp = bvpu.blender.get_group_bounding_box(ob_list)
            mn.append(mntmp)
            mx.append(mxtmp)
        min_xyz = np.min(np.vstack(mn), axis=0).tolist()
        max_xyz = np.max(np.vstack(mx), axis=0).tolist()
        idx = np.floor(np.linspace(st, fin, n_samples)).astype(np.int)
        min_xyz_trajectory = [mn[ii].tolist() for ii in idx]
        max_xyz_trajectory = [mx[ii].tolist() for ii in idx]

        #bvpu.blender.make_cube('bbox', min_xyz, max_xyz) # works. This shows the bounding box, if you want. 
        bvpu.blender.grab_only(ob)
        ## Parent file
        #pfile = act.Action.parent_file
        # The above value (pfile) is ignored for now. Need to eventually implement some way to take the contents 
        # of the current file (group/action/whatever) and save them (append them) to another specfied file
        # in the database. Currently NOT IMPLEMENTED.
        thisfile = os.path.dirname(bpy.data.filepath) #if len(bpy.data.filepath)>0 else pfile
        if thisfile=="":
            # Require saving in db-appropriate location 
            raise NotImplementedError("Please save this file into %s before trying to save to database."%(os.path.join(dbpath, 'Action/')))
        # Construct bvp Action
        bvpact = cls.__new__(cls)
        bvpact.__init__(name=act.name, 
            fname=thisfile, 
            # Labels / info
            wordnet_label=wordnet_label, 
            wordnet_frames=wordnet_frames, 
            # Flags
            is_cyclic=act.Action.is_cyclic, 
            is_translating=act.Action.is_translating, 
            is_broken=act.Action.is_broken, 
            is_armature=act.Action.is_armature, 
            bg_interaction=act.Action.bg_interaction, 
            obj_interaction=act.Action.obj_interaction, 
            is_interactive=act.Action.is_interactive, 
            is_animal=act.Action.is_animal, 
            # Computed / assumed
            n_frames=n_frames, 
            fps=act.Action.fps, 
            min_xyz=min_xyz, 
            max_xyz=max_xyz,
            min_xyz_trajectory = np.array(mn)[np.floor(np.linspace(1,len(mn),num=5))],
            max_xyz_trajectory = np.array(mn)[np.floor(np.linspace(1,len(mx),num=5))],
            dbi=dbi)
        return bvpact

    def __repr__(self):
        """Display string"""
        rstr = '\n ~A~ Action "%s" ~A~\n'%(self.name)
        for k, v in self.docdict.items():
            rstr += '%s : %s\n'%(k, repr(v))
        return rstr
