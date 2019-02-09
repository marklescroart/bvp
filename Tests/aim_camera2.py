import bvp
import bpy
import numpy as np

# Define a camera 
cam_location = (-6, 5, 3)

# Place a dummy object
obj = bvp.Object(pos3D=(2, 3, 0), size3D=0.5)
obj_fix = (2, 3, 0.25)
obj.place()

# Where the object should appear
image_position = (0.25, 0.75)
image_size = (1.77777, 1)

fix_location = bvp.utils.math.aim_camera(obj_fix,
                                         image_position, 
                                         cam_location, 
                                         camera_fov=35.5, 
                                         camera_lens=None, 
                                         image_size=image_size,)
# Place the camera
cam = bvp.Camera(location=[cam_location], fix_location=[fix_location])
cam.place()

# Place a dummy sphere


# Render?
# Set render properties:
#RO = bvp.RenderOptions()
#RO.ApplyOpts()