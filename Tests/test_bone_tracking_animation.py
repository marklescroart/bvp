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
cam = bvp.Camera()
scn = bvp.Scene(objects=[ob], camera=cam)
bone_name = 'RightHandMiddle3'
scn.bake(bone_name)

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