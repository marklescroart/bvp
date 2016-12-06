"""
Renders different backgrounds with different actions (Assuming actions are compatible with objects
"""

#  Test

import bvp
dbi = bvp.DBInterface()

script = """import bvp
from bvp.Classes import SceneList
dbi = bvp.DBInterface()
ro = bvp.RenderOptions()
# ro.BVPopts['Type'] = 'FirstAndLastFrame'
ro.BVPopts['Type'] = 'All'
bg = dbi.query(type='Background')[0]
ob = dbi.query(semantic_category='human')[0]
act = dbi.query(type='Action',is_broken=False)[0]

ob.action = act
ob.size3D = ob.rot3D = ob.pos3D = None

scn = bvp.Scene(objects=[ob], background=bg, sky=None, frame_range=(0,act.n_frames), fname='test_render_action_####')
scn.populate_scene([ob],RaiseError=True,nIter=200)
scn.create(render_options=ro)

scn.render(ro)"""


stdout, stderr = bvp.blend(script)
print(str(stdout,'utf-8'))
print(str(stderr,'utf-8'))