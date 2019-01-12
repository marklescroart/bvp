# Imports
import numpy as np
from .mapped_class import MappedClass
from .constraint import CamConstraint
from .. import utils as bvpu
from ..options import config


def parse_config_str(s, fn=float, to_array=False, marker=','):
    s = [fn(x) for x in s.split(marker)]
    if to_array:
        s = np.array(s)
    return s


# Defaults
LOCATION = parse_config_str(config.get('camera', 'location'))
FIX_LOCATION = parse_config_str(config.get('camera', 'fix_location'))
LENS = float(config.get('camera', 'lens'))
CLIP = parse_config_str(config.get('camera', 'clip'))

try:
    import bpy
    import mathutils as bmu
    is_blender = True
except ImportError:
    is_blender = False


class Camera(MappedClass):
    """Class to handle placement and fixation/angle of camera in a scene."""
    def __init__(self,
                 location=LOCATION,
                 fix_location=FIX_LOCATION,
                 rotation_euler=None,
                 frames=None,
                 lens=LENS,
                 clip=CLIP,
                 ):
        """Class to handle placement and fixation/angle of camera in a scene.

        Parameters
        ----------
        location : list of tuples
            A list of positions for each of n keyframes, each specifying camera
            location as an (x, y, z) tuple.
        fix_location : list of tuples
            As location, but for the fixation target for the camera. Can be
            None, if `rotation_euler` is specified.
        rotation_euler : list of tuples
            Rotation of camera, specified in radians in an (x, y, z) tuple.
            Can be None, if `fix_location` is specified.
        frames : list | None
            A list of the keyframes at which to insert camera / fixation or
            camera angles. Position is linearly interpolated for all frames
            between the keyframes. If None, location is set for only one frame.
            Frame indices should start at 1, not zero.
        lens : scalar
            Focal length for camera lens
        clip : tuple
            Near, far clipping planes for camera
        """

        # Default camera parameters
        self.type = 'Camera'
        self._db_fields = []
        self._data_fields = ['location', 'fix_location', 'rotation_euler', 
                            'frames','lens','clip']
        self._temp_fields = []
        inpt = locals()
        for k, v in inpt.items():
            if not k in ('self', 'type'):
                setattr(self, k, v)
        if self.frames is None or all([x == 1 for x in self.frames]):
            self.frames = (1,)

    @property
    def n_loc(self):
        return 1 if self.location is None else len(self.location)

    @property
    def n_fix(self):
        return 1 if self.fix_location is None else len(self.fix_location)

    @property
    def n_frames(self):
        return max(self.frames) - min(self.frames) + 1

    @property
    def n_keyframes(self):
        return len(self.frames)

    def __repr__(self):
        S = '\n~C~ Camera ~C~\n'
        S += 'Camera lens: %s, clipping: %s, frames: %s\n %d cam location key points\n %d fix location key points'%(str(self.lens), 
            str(self.clip), str(self.frames), self.n_loc, self.n_fix)
        return S

    def place(self, name='000', draw_size=0.33, scn=None):
        """Places camera into Blender scene (only works within Blender)

        Parameters
        ----------
        name : string
            Name for Blender object. "cam_" is automatically prepended to the
            name. [get rid of "cam_" prepending??]
        draw_size : scalar
            Size of camera as drawn in scene.
        scn : bpy.data.scene instance
            Scene to which to add the camera.
        """
        if not is_blender:
            raise Exception("Cannot call place() outside blender!")
        if scn is None:
            scn = bpy.context.scene

        # Add camera
        cam_data = bpy.data.cameras.new('cam_{}'.format(name))
        cam = bpy.data.objects.new('cam_{}'.format(name), cam_data)
        # Make camera object present in scene
        scn.objects.link(cam)
        # Set as active camera
        scn.camera = cam
        cam.location = self.location[0]
        cam.data.lens = self.lens
        cam.data.clip_start, cam.data.clip_end = self.clip

        #frames = self.frames
        #if (len(self.frames) == 2) and (self.frames[0] == 0) and (len(self.location) != 2):
        #    num_frames = len(self.location)
        #    frames = np.floor(np.linspace(0, self.frames[-1], num_frames,
        #                                  endpoint=True)).astype(np.int)

        if self.fix_location is None and self.rotation_euler is not None:
            # Set camera rotation
            cam.rotation_euler = self.rotation_euler[0]
            a = bvpu.blender.make_locrotscale_animation(self.frames,
                    action_name='CamMotion', handle_type='VECTOR',
                    location=self.location, rotation_euler=self.rotation_euler)
        elif self.fix_location is not None and self.rotation_euler is None:
            # Set camera fixation target location
            fix = bpy.data.objects.new('camtarget_{}'.format(name), None)
            fix.location = self.fix_location[0]
            fix.empty_draw_type = 'SPHERE'
            fix.empty_draw_size = draw_size
            scn.objects.link(fix)
            # Add camera constraints to look at target
            trk2 = cam.constraints.new('TRACK_TO')
            trk2.target = fix
            trk2.track_axis = 'TRACK_NEGATIVE_Z'
            trk2.up_axis = 'UP_Y'

            # Set camera motion (multiple camera positions for diff. frames)
            a = bvpu.blender.make_locrotscale_animation(self.frames,
                    action_name='CamMotion', handle_type='VECTOR',
                    location=self.location)
            f = bvpu.blender.make_locrotscale_animation(self.frames,
                    action_name='FixMotion', handle_type='VECTOR',
                    location=self.fix_location)
            fix.animation_data_create()
            fix.animation_data.action = f
        else:
            raise ValueError(('To place a camera, either property `fix_location` or'
                              '`rotation_euler` must be specified!'))

        # Set camera animation action
        cam.animation_data_create()
        cam.animation_data.action = a

    def place_stereo(self, disparity, layers=None, scn=None):
        """Add two cameras for stereo rendering.

        Returns two Blender Camera objects, separated by "disparity" (in
        Blender units). That is, left camera is at -disparity/2, right camera
        is at +disparity/2 from main camera

        Parameters
        ----------
        disparity : scalar, float
            distance in Blender units between left and right cameras
        layers : tuple, 20 long
            boolean values for whether camera is present on each of Blender's
            20 scene layers. If `None`, defaults to present on all layers.
        scn : bpy.data.scene instance
            Scene into which to insert cameras. `None` defaults to current
            scene.

        Notes
        -----
        There must be a single main camera in the scene first for this to work;
        left and right cameras will be parented to current camera.
        """
        if not is_blender:
            raise Exception("Cannot call place_stereo() while operating outside Blender!")
        if scn is None:
            scn = bpy.context.scene
        if layers is None:
            layers = tuple([True for x in range(20)])
        base_camera = [o for o in scn.objects if o.type == 'CAMERA']
        if len(base_camera) == 0:
            raise Exception('No camera in scene!')
        elif len(base_camera) > 1:
            raise Exception('More than 1 base camera in scene!')
        else:
            base_camera = base_camera[0]
        # Get camera rotation fro) for x in rotation]

        # Parent two new cameras to the extant camera in the scene
        # Left camera
        left_cam_vector = bmu.Vector((-disparity/2.0, 0, 0))
        left_cam_location = base_camera.matrix_local*left_cam_vector
        bpy.ops.object.camera_add(location=left_cam_location,
                                  rotation=rotation,
                                  layers=layers)
        left_cam = bpy.context.object
        # Keep same camera props as main camera
        left_cam.data = base_camera.data
        # Instead of the next lines, it would seem better to use
        # `left_cam.parent = base_camera`, but that doesn't work for some
        # reason. It messes up the transformation of left_cam.
        # (Blender 2.77, July 2016)
        bvpu.blender.grab_only(base_camera)
        left_cam.select = True
        bpy.ops.object.parent_set()

        # Right camera
        right_cam_vector = bmu.Vector((disparity/2.0, 0, 0))
        right_cam_location = base_camera.matrix_local*right_cam_vector
        bpy.ops.object.camera_add(location=right_cam_location,
                                  rotation=rotation,
                                  layers=layers)
        right_cam = bpy.context.object
        right_cam.data = base_camera.data
        bvpu.blender.grab_only(base_camera)
        right_cam.select = True
        bpy.ops.object.parent_set()
        return left_cam, right_cam
