# Imports
import math as bnp
from .Constraint import CamConstraint
from .. import utils as bvpu

try:
    import bpy
    import mathutils as bmu
    is_blender = True
except ImportError:
    is_blender = False

class Camera(object):
    """Class to handle placement of camera and camera fixation target for a scene."""
    def __init__(self, location=((17.5, -17.5, 8), ), fix_location=((0, 0, 3.5), ), frames=(1, ), lens=50., clip=(.1, 500.)): 
        """Class to handle placement of camera and camera fixation target for a scene.

        Parameters
        ----------
        location : list of tuples
            a list of positions for each of n keyframes, each specifying camera 
            location as an (x, y, z) tuple
        fix_location : list of tuples
            as location, but for the fixation target for the camera
        frames : list
            a list of the keyframes at which to insert camera / fixation locations. 
            Position is linearly interpolated for all frames between the keyframes. 
        
        Notes
        -----
        If location is specified to be "None", a random location for each keyframe 
            is drawn according to the defaults in CamConstraint. The same is true
            for fix_location.
        
        Tested up to 2 keyframes as of 2012.02.20 -- more may fail
        """
        # Default camera parameters
        inpt = locals()
        self.type = 'Camera'
        for k, v in inpt.items():
            if not i in ('self', 'type'):
                setattr(self, k, v)
        constr = CamConstraint() # Initialize w/ default parameters 
        if all([x==1 for x in self.frames]):
            self.frames = (1, )
        if location is None:
            self.location = constr.sampleCamPos(self.frames)
        if fix_location is None:
            self.fix_location = constr.sampleFixPos(self.frames)

    @property
    def n_loc(self):
        return len(self.location)

    @property
    def n_fix(self):
        return len(self.fix_location)

    @property
    def n_frames(self):
        return max(self.frames) - min(self.frames) + 1

    @property
    def n_keyframes(self):
        return len(self.frames)
    def __repr__(self):
        S = '\n~C~ Camera ~C~\n'
        S += 'Camera lens: %s, clipping: %s, frames: %s\n cam location key points: %s\n fix location key points: %s'%(str(self.lens), 
            str(self.clip), str(self.frames), str([["%.2f"%x for x in Pos] for Pos in self.location]), str([["%.2f"%x for x in Pos] for Pos in self.fix_location]))
        return S
        
    def place(self, name='000', draw_size=0.33, scn=None):
        """Places camera into Blender scene (only works within Blender)

        Parameters
        ----------
        name : string
            Name for Blender object. "cam_" is automatically prepended to the name.
        scn : bpy.data.scene instance
            Scene to which to add the camera.
        """
        if not is_blender:
            raise Exception("Cannot call place() while operating outside Blender!") # !!! TODO: general exception class for trying to call blender (bpy) functions while operating outside of blender
        if scn is None:
            scn = bpy.context.scene
        # This looks like idiocy to me, but it might be idiocy caused by a stupid Blender bug Comment back in if something crops up here. 
        # try:
        #     self.clip
        # except:
        #     print('setting lens - this is some dumb shit!')
        #     self.clip = (.1, 500.)
        #     self.lens = 50.
        # AddCameraWithTarget(scn, name='cam_'+id_name, location=self.location[0], 
        #                             fix_name='camtarget_'+id_name, fix_location=self.fix_location[0], clip=self.clip, lens=self.lens)

        # Add camera
        cam_data = bpy.data.cameras.new('cam_{}'.format(name))
        cam = bpy.ops.object.camera_add('cam_{}'.format(name), cam_data)
        scn.objects.link(cam) # Make camera object present in scene
        scn.camera = cam # Set as active camera
        cam.location = self.location[0]
        # Add fixation target
        fix = bpy.data.objects.new('camtarget_{}'.format(name), None)
        fix.location = self.fix_location[0]
        fix.empty_draw_type = 'SPHERE'
        fix.empty_draw_size = draw_size
        # Add camera constraints to look at target (both necessary...? Unclear. Currently works, tho.)
        trk1 = cam.constraints.new('TRACK_TO')
        trk1.target = fix
        trk1.track_axis = 'TRACK_NEGATIVE_Z'
        trk1.up_axis = 'UP_Z'
        trk2 = cam.constraints.new('TRACK_TO')
        trk2.target = fix
        trk2.track_axis = 'TRACK_NEGATIVE_Z'
        trk2.up_axis = 'UP_Y'
        cam.data.lens = self.lens
        cam.data.clip_start, cam.data.clip_end = self.clip

        # Set camera motion (multiple camera positions for diff. frames)
        ## !!! TODO fix make_location_animation awful function and variable names
        a = bvpu.blender.make_location_animation(self.location, self.frames, aName='CamMotion', hType='VECTOR')
        cam.animation_data_create()
        cam.animation_data.action = a
        f = bvpu.blender.make_location_animation(self.fix_location, self.frames, aName='FixMotion', hType='VECTOR')
        fix.animation_data_create()
        fix.animation_data.action = f

    def place_stereo(self, disparity, layers=None, scn=None):
        """Add two cameras for stereo rendering.

        Returns two Blender Camera objects, separated by "disparity" (in Blender units). 
        That is, left camera is at -disparity/2, right camera is at +disparity/2 from main camera 
        
        Parameters
        ----------
        disparity : scalar, float
            distance in Blender units between left and right cameras
        layers : tuple, 20 long
            boolean values for whether camera is present on each of Blender's
            20 scene layers. If `None`, defaults to present on all layers.
        scn : bpy.data.scene instance
            Scene into which to insert cameras. `None` defaults to current scene.

        Notes
        -----
        There must be a single main camera in the scene first for this to work; left and right
        cameras will be parented to current camera. 
        """
        if not is_blender:
            raise Exception("Cannot call place_stereo() while operating outside Blender!") # !!! TODO: general exception class for trying to call blender (bpy) functions while operating outside of blender        
        if scn is None:
            scn = bpy.context.scene
        if layers is None:
            layers = tuple([True for x in range(20)]) # all layers
        base_camera = [o for o in scn.objects if o.type=='CAMERA']
        if len(base_camera)==0:
            raise Exception('No camera in scene!')
        elif len(base_camera)>1:
            raise Exception('More than 1 base camera in scene!')
        else:
            base_camera = base_camera[0]
        # Get camera rotation fro) for x in rotation]

        # Parent two new cameras to the extant camera in the scene
        # Left camera 
        left_cam_vector = bmu.Vector((-disparity/2.0, 0, 0))
        left_cam_location = base_camera.matrix_local*left_cam_vector
        bpy.ops.object.camera_add(location=left_cam_location, rotation=rotation, layers=layers)
        left_cam = bpy.context.object
        left_cam.data = base_camera.data # Keep same camera props as main camera
        # Instead of the next lines, it would seem better to use `left_cam.parent = base_camera`, 
        # but that doesn't work for some reason. It messes up the transformation of left_cam. (Blender 2.77, July 2016)
        bvpu.blender.grab_only(base_camera)
        left_cam.select = True
        bpy.ops.object.parent_set()

        # Right camera
        right_cam_vector = bmu.Vector((disparity/2.0, 0, 0))
        right_cam_location = base_camera.matrix_local*right_cam_vector
        bpy.ops.object.camera_add(location=right_cam_location, rotation=rotation, layers=layers)
        #bpy.ops.transform.translate(value=(disparity/2., 0, 0), constraint_axis=(True, False, False), constraint_orientation='LOCAL')
        right_cam = bpy.context.object
        right_cam.data = base_camera.data
        bvpu.blender.grab_only(base_camera)
        right_cam.select = True
        bpy.ops.object.parent_set()
        return left_cam, right_cam