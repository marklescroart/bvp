## NOTE! See http://western-skies.blogspot.com/2008/02/simple-complete-example-of-python.html for __getstate__() and __setstate__() methods

# Imports
import copy
from .MappedClass import MappedClass
from .Action import Action
from .Camera import Camera
from .Background import Background
from .Object import Object
from .Sky import Sky
from .Shadow import Shadow

# TODO: Get rid of all these imports, call e.g. bvpu.basics.fixedKeyDict
from .. import utils as bvpu
from ..utils.basics import fixedKeyDict, gridPos, linspace # non-numpy-dependent version of linspace
from ..utils.blender import set_cursor
from ..utils.bvpMath import ImPosCount
from ..options import config

import numpy as np

try:
    import bpy
    is_blender = True
except ImportError: 
    is_blender = False

DEFAULT_FRAME_RATE = int(config.get('render','frame_rate'))

class Scene(MappedClass):
    """Class for storing an abstraction of a Blender scene. 

    Holds all information regarding background, sky (lighting), shadows, and objects (identity, size, 
    position, animation) in the scene. Scenes in .blend files can be created on the fly from these 
    objects, for rendering or inspection (in an interactive Blender session). 
    
    Parameters
    ----------
    number : scalar
        Scene number (one-based by convention) within a list of scenes. Determines default scene name.
    objects : list of bvpObjects | None
        Objects with which to populate the scene. Defaults to none (no objects)
    bg : Background instance | None
        Scene background; controls background and constraints on object / camera positions. Defaults
        to complete blank scene. 
    sky : Sky instance | None
        Sky and lights; controls sky appearance, world settings, and lighting. Defaults to single
        sun lamp angled to the back-left of the whole scene, mild environment lighting, and no sky 
        (all alpha with no image/sky texture)
    shadow : Shadow instance | None
        Controls added shadows, if any. Defaults to none (no added shadows)
    camera : Camera instance | None
        Camera for the scene. Defaults to slight up-right camera with no camera motion.
    frame_range : 2-tuple
        Frame span to render of this scene. NOTE that this is 1-based (the first frame of a scene is 1, 
        not zero). Defaults to (1, 1)

    Other Parameters
    ----------------
    frame_rate : scalar
        Frame rate of movies to render. Technically this doesn't do much, since most renders are per-frame, 
        and you specify a final frame rate for a movie when you concatenate the images together, either with
        Blender, ffmpeg, or whatever your preferred video encoder is. Defaults to 15 (set in bvp.settings)
    
    Notes
    -----
    Objects can be placed in a scene without their positions / scales specified. You can then use the 
    Scene.populate_scene() method to set positions for the objects, given the background constraints.
    """
    #def __init__(self, scnParams={}):
    def __init__(self, 
                 number=0, 
                 objects=None, 
                 background=None, 
                 sky=None, 
                 shadow=None, 
                 camera=None, 
                 frame_range=(1, 1), 
                 fname=None, 
                 frame_rate=DEFAULT_FRAME_RATE): 
        """Class to store scene information in Blender.
        """     
        # Add all inputs as class properties (Shady?)
        inpt = locals()
        for k, v in inpt.items():
            if not k in ['self', 'type']:
                if v == 'None':
                    setattr(self, k, None)
                else:
                    setattr(self, k, v)
        self._temp_fields = ['camera'] # hmm... 
        self._data_fields = []
        self._db_fields = ['objects', 'background', 'sky', 'shadow']

        if self.objects is None:
            # Make "objects" field into a list
            self.objects = []
        # Set default sky parameters
        if self.sky is None: 
            self.sky = Sky()
        # Set default background parameters
        if self.background is None:
            self.background = Background()
        # Default camera: Fixed position!
        if self.camera is None:
            self.camera = Camera(lens=self.background.lens) # TO DO: Set camera default to file "Settings"! 
        #if self.render_options is None:
        #    self.render_options = RenderOptions()
        # Final elements, shadows, are not necessary
        # Set file path for renders:
        if self.fname is None:
            self.fname = 'Sc%04d_##'%self.number
        self.frame_rate = frame_rate

    @property
    def n_objects(self):
        return len(self.objects)

    @property
    def scn_params(self):
        d = fixedKeyDict({
            'frame_start':self.frame_range[0], 
            'frame_end':self.frame_range[1] # Default is 3 seconds
            # MORE??
            })
        return d

    def __repr__(self):
        rstr = 'Class "Scene" (number=%d, %.2f s, Frames=(%d-%d)):\n'%(self.number, (self.frame_range[1]-self.frame_range[0]+1)/float(self.frame_rate), self.frame_range[0], self.frame_range[1])
        rstr+='BACKGROUND %s\n\n'%self.background
        rstr+='SKY %s\n\n'%self.sky
        rstr+='SHADOW %s\n\n'%self.shadow
        rstr+='CAMERA %s\n\n'%self.camera
        rstr+='OBJECTS\n'
        for o in self.objects:
            rstr+='%s\n'%o
        return rstr

    def check_compatibility(self,bg, act, debug=True):
        """Helper function for populate_scene

        Does a quick check of whether or not a given action is compatible with a given background.
        
        Parameters
        ----------
        bg : Background instance
            Background to check
        act : Action instance
            Action to check
        debug : boolprints debug information about the background and the action

        Notes
        -----
        Could possibly extend to objects with a certain size
        """
        if bg == None or act == None:
            if RaiseError:
                raise Exception('Invalid Background or Action passed into check_compatibility!')
            if debug:
                print('Invalid Background or Action passed into check_compatibility!')
            return
        act_contains_x_origin = act.max_xyz[0] >= 0 >= act.min_xyz[0]
        act_contains_y_origin = act.max_xyz[1] >= 0 >= act.min_xyz[1]
        act_contains_z_origin = act.max_xyz[2] >= 0 >= act.min_xyz[2]
        tmp_ob = Object()
        tmp_ob.action = act
        const = bg.obConstraints
        tmp_ob.size3D = min(bg.obConstraints.Sz[2],bg.obConstraints.Sz[3])
        max_pos = tmp_ob.max_xyz_pos
        min_pos = tmp_ob.min_xyz_pos
        X_OK, Y_OK, Z_OK, r_OK = [True,True,True, True]
        if const.X:
            X_OK = (max_pos[0] - min_pos[0]) < (const.X[3] - const.X[2])
        if const.Y:
            Y_OK = (max_pos[1] - min_pos[1]) < (const.Y[3] - const.Y[2])
        if const.Z:
            if (const.Z[2] == const.Z[3]):
                if debug:
                    print('Constraint Z is constant for background %s. Ignoring Z constraint'%bg.name)
                Z_OK = (max_pos[2] - min_pos[2]) < const.Sz[3] - tmp_ob.size3D
            else:
                Z_OK = (max_pos[2] - min_pos[2]) < (const.Z[3] - const.Z[2])
        if const.r:
            maxR = ((max_pos[0]-min_pos[0])**2+(max_pos[1]-min_pos[1])**2+(max_pos[2]-min_pos[2])**2)**.5 #TODO: Enforce this better
            rB = True if const.r[3] is None else (maxR)<=2*const.r[3]
            r_OK = rB
        if all([X_OK, Y_OK, Z_OK, r_OK, act_contains_x_origin, act_contains_y_origin, act_contains_z_origin]):
            return True
        else:
            if debug:
                print("Action", act.name,"incompatible with bg",bg.name)
                print("max pos for action", act.max_xyz)
                print("min pos for action", act.min_xyz)
                print("ObConstraints:")
                print("Origin:", const.origin)
                print("X", const.X)
                print("Y", const.Y)
                print("Z", const.Z)
                if const.r:
                    print("R", const.r)
                print("Size", const.Sz)
                print("Temp Object Size", tmp_ob.size3D)
                print("Temp Object action max", max_pos)
                print("Temp Object action min", min_pos)
                print("X,Y,Z ok:", [X_OK, Y_OK, Z_OK, r_OK])
                print("origin containment:", [act_contains_x_origin, act_contains_y_origin, act_contains_z_origin])
            return False

    
    def populate_scene(self, ObList, ResetCam=True, ImPosCt=None, EdgeDist=0., ObOverlap=.50, MinSz2D=0, RaiseError=False, nIter=50):
        """Choose positions for all objects in "ObList" input within the scene, 
        according to constraints provided by scene background.
        
        ImPosCt tracks the number of times that each image location (bin) 
        has had an object in it. Can be omitted for single scenes (defaults
        to randomly sampling whole image)

        """
        # raise Exception("WIP! FiX ME!") # TODO
        # (This just might work doubtful)

        from random import shuffle
        if not ImPosCt:
            ImPosCt = ImPosCount(0, 0, ImSz=1., nBins=5, e=1)
        Attempt = 1
        Done = False
        while Attempt<=nIter and not Done:
            Fail = False
            ObToAdd = []
            #if verbosity_level > 3:
            #    print('### --- Running populate_scene, Attempt %d --- ###'%Attempt)
            if ResetCam:
                # Start w/ random camera, fixation position
                cPos = self.background.CamConstraint.sampleCamPos(self.frame_range)
                print('cpos', cPos)
                fPos = self.background.CamConstraint.sample_fix_location(self.frame_range,obj=ObToAdd)
            # Multiple object constraints for moving objects
            OC = []
            for o in ObList:
                # Randomly cycle through object constraints (in case there are multiple exclusive possible locations for an object)
                self.camera = Camera(location=cPos, fix_location=fPos, frames=self.frame_range, lens=self.background.lens)
                if not OC:
                    if type(self.background.obConstraints) is list:
                        OC = copy.copy(self.background.obConstraints)
                    else:
                        OC = [copy.copy(self.background.obConstraints)]
                    shuffle(OC)
                oc = OC.pop()
                NewOb = copy.copy(o) # resets size each iteration as well as position
                if NewOb.action is not None:
                    is_compatible = self.check_compatibility(self.background,NewOb.action)
                    if not is_compatible: #Check if it is even possible to use the action
                        if RaiseError:
                            raise Exception('Action' + NewOb.action.name +'is incompatible with bg' + self.background.name)
                        pass
                if self.background.obstacles:
                    Obst = self.background.obstacles+ObToAdd
                else:
                    Obst = ObToAdd
                if not o.semantic_category:
                    # Sample semantic category based on bg??
                    # UNFINISHED as of 2012.10.22
                    pass #etc.
                if not o.size3D:
                    # OR: Make real-world size the default??
                    # OR: Choose objects by size??
                    NewOb.size3D = oc.sampleSize()
                if not o.rot3D:
                    # NOTE: This is fixing rotation of objects to be within 90 deg of facing camera
                    NewOb.rot3D = oc.sampleRot(self.camera)
                if not o.pos3D:
                    # Sample position last (depends on camera position, It may end up depending on pose, rotation, (or action??)
                    NewOb.pos3D, NewOb.pos2D = oc.sampleXY(NewOb, self.camera, Obst=Obst, EdgeDist=EdgeDist, ObOverlap=ObOverlap, RaiseError=False, ImPosCt=ImPosCt, MinSz2D=MinSz2D)
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
            raise Exception('MaxAttemptReached', 'Unable to populate scene %s after %d attempts!'%(self.background.name, nIter))
        elif Attempt>nIter and not RaiseError:
            print('Warning! Could not populate scene! Only got to %d objects!'%len(ObToAdd))
        self.objects = ObToAdd
        # Make sure last fixation hasn't "wandered" away from objects: 
        
        # fPosFin = self.background.CamConstraint.sample_fix_location((1, ), obj=self.objects)
        # self.camera.fix_location = self.camera.fix_location[:-1]+[fPosFin[0], ]

    def get_occlusion(self):
        """
        Get occlusion matrix (Percent occlusion of each object by others)
        TO COME (?)
        """
        pass


    def create(self, render_options=None, scn=None, is_working=False):
        """Creates the stored scene (imports bg, sky, lights, objects, shadows) in Blender

        Optionally, applies rendering options 

        Parameters
        ----------
        render_options : RenderOptions instance
            Class to store rendering options (e.g. size, base path, extra meta-information renders, etc.)
        scn : string scene name
            Scene to render within .blend file. Defaults to current scene.
        """
        # print(self.camera.fix_location)
        scn = bvpu.blender.set_scene(scn)
        # set layers to correct setting
        scn.layers = [True]+[False]*19
        # set cursort to center
        set_cursor((0, 0, 0))
        # Background
        self.background.place()
        if self.background.semantic_category is not None and 'indoor' in self.background.semantic_category and self.background.real_world_size < 50.:
            # Due to a problem with skies coming inside the corners of rooms
            scale = self.background.real_world_size*1.5
        else:
            scale = self.background.real_world_size
        # Sky
        self.sky.place(number=self.number, scale=scale)
        # Camera
        self.camera.place(name='camera%03d'%self.number)
        # Shadow
        if self.shadow:
            self.shadow.place(scale=self.background.real_world_size)
        # Objects
        for o in self.objects:
            try:
                o.place()
            except Exception as e:
                if is_working:
                    pass
                else:
                    raise e
        scn.name = self.fname
        # Details
        for s in self.scn_params.keys():
            setattr(scn, s, self.scn_params[s])
        if render_options is not None:
            # Set filepath
            filepath = copy.copy(render_options.BVPopts['BasePath'])
            if not '{scene_name}' in filepath:
                print('Warning! base path did not have room to add scene name. MODIFYING...')
                filepath = ''.join([filepath, '{scene_name}'])
                print('New path is:',filepath.format(scene_name=self.fname))
            scn.render.filepath = filepath.format(scene_name=self.fname)
            # Apply other options
            render_options.apply_opts()
        scn.layers = [True]*20

    def render(self, render_options, scn=None):
        """Renders the scene (immediately, in open instance of Blender)
        
        Parameters
        ----------
        render_options : RenderOptions instance
            Class to specify rendering parameters
        scn : string scene name
            Scene to render. Defaults to current scene.
        """
        scn = bvpu.blender.set_scene(scn)
        # Reset scene nodes (?)
        
        # TODO: This is brittle and shitty. Need to revisit how to set final file names. 
        if scn.render.filepath is None:
            scn.render.filepath = render_options.BVPopts['BasePath']
        if '{scene_name}' in scn.render.filepath:
            scn.render.filepath = render_options.BVPopts['BasePath'].format(self.fname)
        elif '%s' in scn.render.filepath:
            scn.render.filepath = scn.render.filepath%self.fname
        # Apply rendering options
        render_options.apply_opts()
        # Render all layers!
        scn.layers = [True]*20 # TODO: Revisit locations where layers are set in this class's methods / in RenderOptions methods
        # TODO: Why isn't this in RenderOptions.apply_opts? Seems as if it should be...
        if render_options.BVPopts['Type'].lower()=='firstframe':
            scn.frame_step = scn.frame_end+1 # so only one frame will render
        elif render_options.BVPopts['Type'].lower()=='firstandlastframe':
            scn.frame_step = scn.frame_end-1
        elif render_options.BVPopts['Type'].lower()=='all':
            scn.frame_step = 1
        elif render_options.BVPopts['Type'].lower()=='every4th':
            # Assure that scene starts with a multiple of 4 + 1
            while not scn.frame_start%4==1:
                scn.frame_start += 1
            scn.frame_step = 4
        else:
            raise Exception("Invalid render type specified!\n   Please use 'FirstFrame', 'FirstAndLastFrame', or 'All'")
        # Render animation
        bpy.ops.render.render(animation=True, scene=scn.name)

    def clear(self, scn=None):
        """Resets scene to empty, ready for next.

        Removes all objects, lights, background; resets world settings; clears all nodes; 
        readies scene for next import /render. This is essential for memory saving in long 
        render runs. Use with caution. Highly likely to crash Blender.

        Parameters
        ----------
        scn : string scene name
            Scene to clear of all elements.
        """
        ### --- Removing objects for next scene: --- ### 
        scn = bvpu.blender.set_scene(scn)
        # Remove all mesh objects       
        Me = list()
        for o in bpy.data.objects:
            #ml.grab_only(o)
            if o.type=='MESH': # Only mesh objects for now = cameras too?? Worlds??
                Me.append(o.data)
            if o.name in scn.objects: # May not be... why?
                scn.objects.unlink(o)
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
        for n in scn.node_tree.nodes:
            scn.node_tree.nodes.remove(n)
        # Re-set (delete) all render layers
        RL = bpy.context.scene.render.layers.keys()
        bpy.ops.scene.render_layer_add()
        for ii, n in enumerate(RL):
            bpy.context.scene.render.layers.active_index=0
            bpy.ops.scene.render_layer_remove()
        # Rename newly-added layer (with default properties) to default name:
        bpy.context.scene.render.layers[0].name = 'RenderLayer'
        # Set only first layer to be active
        scn.layers = [True]+[False]*19
    
    @classmethod
    def from_blender(cls, number, scn=None, dbi=None):
        """Gathers all elements present in a blender scene into a Scene.
        
        FORMERLY bvp.utils.blender.get_scene

        GUARANTEED TO BE BROKEN.

        Gets the background, objects, sky, shadows, and camera of the current scene
        for saving in a Scene. 
        
        Parameters
        ----------
        number : int
            0-first index for scene in scene list. (Sets render path for scene to be 'Sc%04d_##'%(Num+1))

        """
        raise Exception('HUGELY WIP. NOT READY YET.') ## TODO: FIX ME!
        assert is_blender, "Hey bozo! from_blender() can't be run outside blender!"
        if scn is None:
            scn = bpy.context.scene
        # Initialize scene:
        new_scn = cls.__new__(blah)
        # Scroll through scene component types:
        type = ['objects', 'backgrounds', 'skies', 'shadows']
        # Get scene components:
        #vL = copy.copy(verbosity_level)
        #verbosity_level=1 # Turn off warnings for not-found library objects
        for o in scn.objects:
            for ct in type:
                # Search for object name in database... HMM.
                ob_add = 0 ## SEARCH DATABASE FOR ME, OR DERIVE FROM OBJECT PROPS IN FILE. ##Lib.getSC(o.name, ct)
                if ob_add and ct=='objects':
                    if 'ARMATURE' in [x.type for x in o.dupli_group.objects]:
                        Pob = [x for x in scn.objects if o.name in x.name and 'proxy' in x.name]
                        if len(Pob)>1:
                            raise Exception('WTF is up with more than one armature for %s??'%ob_add.name)
                        elif len(Pob)==0:
                            print('No pose has been set for poseable object %s'%o.name)
                        elif len(Pob)==1:
                            print('Please manually enter the pose for object %s scn.Obj[%d]'%(o.name, len(new_scn.Obj)+1))
                    new_scn.Obj.append(Object(o.name, Lib, 
                        size3D=o.scale[0]*10., 
                        rot3D=list(o.rotation_euler), 
                        pos3D=list(o.location), 
                        pose=None
                        ))

                elif ob_add and ct=='backgrounds':
                    new_scn.BG = Background(o.name, Lib)
                elif ob_add and ct=='skies':
                    # Note: This will take care of lights, too
                    new_scn.Sky = Sky(o.name, Lib)
                elif ob_add and ct=='shadows':
                    new_scn.Shadow = Shadow(o.name, Lib)
        #verbosity_level=vL
        # Get camera:
        C = [c for c in bpy.context.scene.objects if c.type=='CAMERA']
        if len(C)>1 or len(C)==0:
            raise Exception('Too many/too few cameras in scene! (Found %d)'%len(C))
        C = C[0]
        CamAct = C.animation_data.action
        # lens
        new_scn.Cam.lens = C.data.lens
        # frames
        new_scn.Cam.frames = tuple(CamAct.frame_range)
        # location
        xC = [k for k in CamAct.fcurves if 'location'==k.data_path and k.array_index==0][0]
        yC = [k for k in CamAct.fcurves if 'location'==k.data_path and k.array_index==1][0]
        zC = [k for k in CamAct.fcurves if 'location'==k.data_path and k.array_index==2][0]
        def cLoc(fr):
            # Get x, y, z location given time
            return (xC.evaluate(fr), yC.evaluate(fr), zC.evaluate(fr))
        new_scn.Cam.location = [cLoc(fr) for fr in CamAct.frame_range]
        # Fixation position
        Fix = [c for c in bpy.context.scene.objects if "CamTar" in c.name][0]
        # (Possible danger - check for multiple fixation points??)
        FixAct = Fix.animation_data.action
        xF = [k for k in FixAct.fcurves if 'location'==k.data_path and k.array_index==0][0]
        yF = [k for k in FixAct.fcurves if 'location'==k.data_path and k.array_index==1][0]
        zF = [k for k in FixAct.fcurves if 'location'==k.data_path and k.array_index==2][0]
        def fLoc(fr):
            # Get x, y, z location given time
            return (xF.evaluate(fr), yF.evaluate(fr), zF.evaluate(fr))
        new_scn.Cam.fix_location = [fLoc(fr) for fr in FixAct.frame_range]
        # Last scene props: 
        new_scn.frame_range = tuple(CamAct.frame_range)
        new_scn.scn_params['frame_end'] = new_scn.frame_range[-1]
        new_scn.fname = 'Sc%04d_##'%(Num+1)
        new_scn.Num = Num+1
        print('Don''t forget to set sky and poses!')
        return new_scn
