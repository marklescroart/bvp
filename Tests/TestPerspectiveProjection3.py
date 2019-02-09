# Test of inverse perspective projection with pixel coordinates

import bvp
import bpy
import numpy as np
# Define a camera w/ default parameters
cam = bvp.Camera()
cam.place()

positions = bvp.utils.math.circle_pos(200, 8, x_center=500, y_center=500)
#positions = np.vstack([positions, [0.5, 0.5]])

for im_pos in positions:
    # Distance from camera
    z = -10 
    imp = im_pos.astype(np.int)
    obj_pos = bvp.utils.math.perspective_projection_inv(imp, 
                                                        cam.location[0], 
                                                        cam.fix_location[0],
                                                        z,
                                                        camera_fov=35.5, 
                                                        camera_lens=None, 
                                                        image_size=(1920, 1080),
                                                        handedness='right')
    # Place a dummy sphere
    obj = bvp.Object(pos3D=obj_pos)
    obj.place()


# Render?
# Set render properties:
#RO = bvp.RenderOptions()
#RO.ApplyOpts()