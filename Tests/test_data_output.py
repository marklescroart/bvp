# Test data storage

import bvp

dbi = bvp.DBInterface()

# Humans
humans = dbi.query(type='Object', fname='Mixamo_Characters_Free_0.blend')
ob1 = humans[3]

cars = dbi.query(type='Object', semantic_category='auto')
ob2 = cars[1]
ob2.pos3D = [3, -1, 0]
ob2.size3D = 6.0

# Grab an action
actions = dbi.query(type='Action', is_translating=True, is_broken=False)
act = actions[3]

# Set an object action
ob1.action = act

# Get a background
bgs = dbi.query(type='Background', semantic_category='open')
bg = bgs[0]

cam = bvp.Camera()

# Create a scene
scn = bvp.Scene(objects=[ob1, ob2], camera=cam, background=bg)