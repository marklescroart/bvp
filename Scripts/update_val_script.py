#  Test

import bvp
dbi = bvp.DBInterface()

act_list = dbi.query(type='Action')
for i in range(10):
    act = act_list[i]
    print(act.name,act.fname)
    script = """import bvp
dbi = bvp.DBInterface()
ro = bvp.RenderOptions()
ro.BVPopts['Type'] = 'FirstAndLastFrame'
ob = dbi.query(semantic_category='human')[0]
act = dbi.query(type='Action', name = """+act.name+""")[0]
ob.action = act
ob.size3D = ob.rot3D = ob.pos3D = None
scn = bvp.Scene(objects=[ob], background=bg, sky=None, frame_range=(0,act.n_frames), fname='test_render_action_####')
scn.populate_scene([ob],RaiseError=True,nIter=200)
"""


stdout, stderr = bvp.blend(script)
print(str(stdout,'utf-8'))
print(str(stderr,'utf-8'))