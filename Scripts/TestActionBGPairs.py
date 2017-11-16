"""
Renders different backgrounds with different actions (Assuming actions are compatible with objects
"""

import bvp
dbi = bvp.DBInterface()

bg_list = dbi.query(type='Background')
act_list = dbi.query(type='Action', is_broken=False)
for i in range(5):
    bg = bg_list[i].name
    for j in range(5):
        act = act_list[j]. name
        print("Rendering:", i,j,bg,act)
        script = """import bvp
dbi = bvp.DBInterface()
ob = dbi.query(semantic_category='human')[0]
ro = bvp.RenderOptions()
ro.BVPopts['Type'] = 'FirstAndLastFrame'
bg = dbi.query(type='Background', name= '"""+bg+"""')[0]
act = dbi.query(type='Action', name= '"""+act+"""')[0]
ob.action = act
ob.size3D = ob.rot3D = ob.pos3D = None
scn = bvp.Scene(objects=[ob], background=bg, sky=None, 
                frame_range=(0,act.n_frames), 
                fname='test_render_action_"""+str(i)+ "_" + str(j)+ """_####')
try:
    scn.populate_scene([ob],RaiseError=True,nIter=200)
    scn.create(render_options=ro)
    scn.render(ro)
except Exception as e:
    print("Unable to populate scene! Got error:", e)
"""


        stdout, stderr = bvp.blend(script)
        print(str(stdout,'utf-8'))
        print(str(stderr,'utf-8'))

print([bg.name for bg in bg_list])
print([act.name for act in act_list])