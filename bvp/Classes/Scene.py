## NOTE! See http://western-skies.blogspot.com/2008/02/simple-complete-example-of-python.html for __getstate__() and __setstate__() methods

# Imports
import bvp
import copy
from ..utils.basics import fixedKeyDict, gridPos, linspace # non-numpy-dependent version of linspace
from ..utils.blender import set_cursor
from ..utils.bvpMath import ImPosCount
from ..options import config
try:
    import bpy
    is_blender = True
except ImportError: 
    is_blender = False

class Scene(object):
    """Class for storing an abstraction of a Blender scene. 

    Holds all information regarding background, sky (lighting), shadows, and objects (identity, size, 
    position, animation) in the scene. Scenes in .blend files can be created on the fly from these 
    objects, for rendering or inspection (in an interactive Blender session). 
    
    Parameters
    ----------
    num : scalar
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
    cam : bvpCam instance | None
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
    def __init__(self, num=0, objects=None, bg=None, sky=None, shadow=None, cam=None, frame_range=(1, 1), fpath=None, frame_rate=int(config.get('render','frame_rate'))): 
        """Class to store scene information in Blender.
        """     
        # Add all inputs as class properties (Shady?)
        Input = locals()
        for i in Input:
            if not i in ['self']:
                setattr(self, i, Input[i])
        
        if self.objects is None:
            # Make "objects" field into a list
            self.objects = []
        # Set default sky parameters
        if self.sky is None: 
            self.sky = bvp.Sky()
        # Set default background parameters
        if self.bg is None:
            self.bg = bvp.Background()
        # Default camera: Fixed position!
        if self.cam is None:
            self.cam = bvp.Camera(lens=self.bg.lens) # TO DO: Set cam default to file "Settings"! 
        # Final elements, shadows, are not necessary
        # Set file path for renders:
        if self.fpath is None:
            self.fpath = 'Sc%04d_##'%self.num
        self.frame_rate = frame_rate

    @property
    def nObjects(self):
        return len(self.objects)
    @property
    def ScnParams(self):
        d = fixedKeyDict({
            'frame_start':self.frame_range[0], 
            'frame_end':self.frame_range[1] # Default is 3 seconds
            # MORE??
            })
        return d
    def __repr__(self):
        S = 'Class "Scene" (num=%d, %.2f s, Frames=(%d-%d)):\n'%(self.num, (self.frame_range[1]-self.frame_range[0]+1)/float(self.frame_rate), self.frame_range[0], self.frame_range[1])
        S+='BACKGROUND%s\n\n'%self.bg
        S+='SKY%s\n\n'%self.sky
        S+='SHADOW%s\n\n'%self.shadow
        S+='CAMERA%s\n\n'%self.cam
        S+='OBJECTS\n'
        for o in self.objects:
            S+='%s\n'%o
        return S
    
    def populate_scene(self, ObList, ResetCam=True, ImPosCt=None, EdgeDist=0., ObOverlap=.50, MinSz2D=0, RaiseError=False, nIter=50):
        """Choose positions for all objects in "ObList" input within the scene, 
        according to constraints provided by scene background.
        
        ImPosCt tracks the number of times that each image location (bin) 
        has had an object in it. Can be omitted for single scenes (defaults
        to randomly sampling whole image)

        ML 2012.03
        """
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
                # Start w/ random cam, fixation position
                cPos = self.bg.CamConstraint.sampleCamPos(self.frame_range)
                fPos = self.bg.CamConstraint.sampleFixPos(self.frame_range)
                self.cam = bvp.Camera(location=cPos, fixPos=fPos, frames=self.frame_range, lens=self.bg.lens)
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
                if self.bg.obstacles:
                    Obst = self.bg.obstacles+ObToAdd
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
                    NewOb.rot3D = oc.sampleRot(self.cam)
                if not o.pos3D:
                    # Sample position last (depends on cam position, It may end up depending on pose, rotation, (or action??)
                    NewOb.pos3D, NewOb.pos2D = oc.sampleXY(NewOb.size3D, self.cam, Obst=Obst, EdgeDist=EdgeDist, ObOverlap=ObOverlap, RaiseError=False, ImPosCt=ImPosCt, MinSz2D=MinSz2D)
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
            raise Exception('MaxAttemptReached', 'Unable to populate scene %s after %d attempts!'%(self.bg.name, nIter))
        elif Attempt>nIter and not RaiseError:
            print('Warning! Could not populate scene! Only got to %d objects!'%len(ObToAdd))
        self.objects = ObToAdd
        # Make sure last fixation hasn't "wandered" away from objects: 
        fPosFin = self.bg.CamConstraint.sampleFixPos((1, ), obj=ObToAdd)
        self.cam.fixPos = self.cam.fixPos[:-1]+[fPosFin[0], ]

    def apply_opts(self, scn=None, render_options=None):
        """Apply general options to scene (environment lighting, world, start/end frames, etc), 
        including (optionally) render options (of class 'RenderOptions'))
        
        ML 2011
        """
        scn = bvp.utils.blender.set_scene(scn) 
        # Set frames (and other scene props?)
        for s in self.ScnParams.keys():
            setattr(scn, s, self.ScnParams[s])
        if render_options:
            # Set filepath
            if render_options.BVPopts['BasePath'][-2:]!='%s':
                print('Warning! base path did not have room to add scene-specific file name. MODIFYING...')
                render_options.BVPopts['BasePath']+='%s'
            scn.render.filepath = render_options.BVPopts['BasePath']%self.fpath
            render_options.apply_opts()

    def get_occlusion(self):
        """
        Get occlusion matrix (Percent occlusion of each object by others)
        TO COME (?)
        """
        pass


    def create(self, render_options=None, scn=None):
        """Creates the stored scene (imports bg, sky, lights, objects, shadows) in Blender

        Optionally, applies rendering options 

        Parameters
        ----------
        render_options : bvp.RenderOptions instance
            Class to store rendering options (e.g. size, base path, extra meta-information renders, etc.)
        scn : string scene name
            Scene to render within .blend file. Defaults to current scene.
        """
        scn = bvp.utils.blender.set_scene(scn)
        # set layers to correct setting
        scn.layers = [True]+[False]*19
        # set cursort to center
        set_cursor((0, 0, 0))
        # place bg
        self.bg.Place()
        if self.bg.realWorldSize<50. and 'indoor' in self.bg.semantic_category:
            # Due to a problem with skies coming inside the corners of rooms
            Scale = self.bg.realWorldSize*1.5
        else:
            Scale = self.bg.realWorldSize
        self.sky.Place(num=self.num, Scale=Scale)
        self.cam.Place(IDname='cam%03d'%self.num)
        if self.shadow:
            self.shadow.PlaceShadow(Scale=self.bg.realWorldSize)
        for o in self.objects:
            o.Place()
        scn.name = self.fpath
        self.apply_opts(render_options=render_options)
        scn.layers = [True]*20
    
    def create_working(self, render_options=None, scn=None):
        """Creates the stored scene, but allows for objects without set positions.

        See Scene.create() help.
        """
        if not scn:
            scn = bpy.context.scene
        # set layers to correct setting
        scn.layers = [True]+[False]*19
        # set cursort to center
        set_cursor((0, 0, 0))
        # place bg
        self.bg.Place()
        self.sky.Place(num=self.num, Scale=self.bg.realWorldSize)
        self.cam.Place(IDname='cam%03d'%self.num)
        if self.shadow:
            self.shadow.PlaceShadow(Scale=self.bg.realWorldSize)
        for o in self.objects:
            try:
                o.Place()
            except:
                pass
        scn.name = self.fpath
        self.apply_opts(render_options=render_options)
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
        scn = bvp.utils.blender.set_scene(scn)
        # Reset scene nodes (?)
        
        # Apply rendering options
        scn.render.filepath = render_options.BVPopts['BasePath']%self.fpath
        render_options.apply_opts()
        # Render all layers!
        scn.layers = [True]*20
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
        scn = bvp.utils.blender.set_scene(scn)
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
    def from_blender(cls, num, scn=None, dbi=None):
        """Gathers all elements present in a blender scene into a Scene.
        
        FORMERLY bvp.utils.blender.get_scene

        GUARANTEED TO BE BROKEN.

        Gets the background, objects, sky, shadows, and camera of the current scene
        for saving in a Scene. 
        
        Parameters
        ----------
        num : int
            0-first index for scene in scene list. (Sets render path for scene to be 'Sc%04d_##'%(Num+1))

        """
        assert is_blender, "Hey bozo! from_blender() can't be run outside blender!"
        if scn is None:
            scn = bpy.context.scene
        # Initialize scene:
        S = cls.__new__(blah)
        # Scroll through scene component types:
        type = ['objects', 'backgrounds', 'skies', 'shadows']
        # Get scene components:
        #vL = copy.copy(verbosity_level)
        #verbosity_level=1 # Turn off warnings for not-found library objects
        for o in scn.objects:
            for ct in type:
                # Search for object name in database... HMM.
                ob_add = Lib.getSC(o.name, ct)
                if ob_add and ct=='objects':
                    if 'ARMATURE' in [x.type for x in o.dupli_group.objects]:
                        Pob = [x for x in scn.objects if o.name in x.name and 'proxy' in x.name]
                        if len(Pob)>1:
                            raise Exception('WTF is up with more than one armature for %s??'%ob_add.name)
                        elif len(Pob)==0:
                            print('No pose has been set for poseable object %s'%o.name)
                        elif len(Pob)==1:
                            print('Please manually enter the pose for object %s scn.Obj[%d]'%(o.name, len(S.Obj)+1))
                    S.Obj.append(bvp.Object(o.name, Lib, 
                        size3D=o.scale[0]*10., 
                        rot3D=list(o.rotation_euler), 
                        pos3D=list(o.location), 
                        pose=None
                        ))

                elif ob_add and ct=='backgrounds':
                    S.BG = bvp.Background(o.name, Lib)
                elif ob_add and ct=='skies':
                    # Note: This will take care of lights, too
                    S.Sky = bvp.Sky(o.name, Lib)
                elif ob_add and ct=='shadows':
                    S.Shadow = bvp.Shadow(o.name, Lib)
        #verbosity_level=vL
        # Get camera:
        C = [c for c in bpy.context.scene.objects if c.type=='CAMERA']
        if len(C)>1 or len(C)==0:
            raise Exception('Too many/too few cameras in scene! (Found %d)'%len(C))
        C = C[0]
        CamAct = C.animation_data.action
        # lens
        S.Cam.lens = C.data.lens
        # frames
        S.Cam.frames = tuple(CamAct.frame_range)
        # location
        xC = [k for k in CamAct.fcurves if 'location'==k.data_path and k.array_index==0][0]
        yC = [k for k in CamAct.fcurves if 'location'==k.data_path and k.array_index==1][0]
        zC = [k for k in CamAct.fcurves if 'location'==k.data_path and k.array_index==2][0]
        def cLoc(fr):
            # Get x, y, z location given time
            return (xC.evaluate(fr), yC.evaluate(fr), zC.evaluate(fr))
        S.Cam.location = [cLoc(fr) for fr in CamAct.frame_range]
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
        S.Cam.fixPos = [fLoc(fr) for fr in FixAct.frame_range]
        # Last scene props: 
        S.FrameRange = tuple(CamAct.frame_range)
        S.ScnParams['frame_end'] = S.FrameRange[-1]
        S.fpath = 'Sc%04d_##'%(Num+1)
        S.Num = Num+1
        print('Don''t forget to set sky and poses!')
        return S
