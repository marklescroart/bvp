import bvp
dbi = bvp.DBInterface()

# Get an action that moves
dance = dbi.query(1, type='Action', name='booty_hip_hop_dance_01')
# Get a body to add it to
humans = dbi.query(semantic_category='human')
ob = humans[-2]
# Add action
ob.action = dance

# Create a scene
n_frames = int(ob.action.n_frames)
cam = bvp.Camera(location=[[8, -8, 3]] * n_frames, fix_location=[[0,0,1.6]], frames=(0, n_frames))
scn = bvp.Scene(objects=[ob], camera=cam, frame_range=(1, n_frames+1))
bone_name = 'RightHandMiddle3'
# Number of values for cam.location needs to match frames. Lame.

scn.bake(bone_name, change_camera_position=False)

scn.create()

"""
NOTE! This works! 

Super fussy about frames (needs fixing), location for camera, but in general this looks very implementable. 

bvp.camera.frames needs to be set by scene at import
bv.scene.bake() depends annoyingly on initial position of camera, which it should not (should be able to define all positions froma  clean slate)

focal length of camera is set in sub-optimal fashion

Bone name query may be impossible (??) from proxy object, which is annoying. 

A 3D offset parameter would be good.
A 2D offset parameter (to control visual field position of desired bone) would be amazing. 

"""