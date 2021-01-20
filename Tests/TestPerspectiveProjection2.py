# Test of inverse perspective projection with fraction coordinates

import bvp
import bpy
import numpy as np
# Define a camera w/ default parameters
cam = bvp.Camera()
cam.place()

positions = bvp.utils.math.circle_pos(0.25, 8, x_center=0.5, y_center=0.5)
positions = np.vstack([positions, [0.5, 0.5]])

for im_pos in positions:
    # Distance from camera
    z = -10 
    obj_pos = bvp.utils.math.perspective_projection_inv(im_pos, 
                                                        cam.location[0], 
                                                        cam.fix_location[0],
                                                        z,
                                                        camera_fov=35.5, 
                                                        camera_lens=None, 
                                                        image_size=(1., 1.),
                                                        handedness='right')
    # Place a dummy sphere
    obj = bvp.Object(pos3D=obj_pos)
    obj.place()


# Render?
# Set render properties:
#RO = bvp.RenderOptions()
#RO.ApplyOpts()