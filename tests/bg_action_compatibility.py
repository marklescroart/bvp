"""
    Goes through all the actions and backgrounds returned by dbi, and checks for pairwise compatibility by comparing bounding box dimensions

    Parameters:
        threshold: Backgrounds/actions with average compatibility lower than this are printed.
    Prints:
        compat: Compatiblity matrix with compat[i,j] = 1 if the act-bg pair are compatible, 0 else.
        bad_bgs: Backgrounds with average compatibility lower than threshold
        bad_actions: Actions with average compatibility lower than threshold
"""

import numpy as np
import bvp

threshold = 0.5

def check_compatibility(ob, bg, act, debug=False):
    #TODO: Action, object size
    #TODO: dealing with multiple actions

    ob.action = act
    const = bg.obConstraints
    max_pos = act.max_xyz
    min_pos = act.min_xyz
    if debug:
        print('hi!')
        print(max_pos, min_pos)
        print(ob.size3D)
        print(max_pos, min_pos)
    X_OK, Y_OK, Z_OK, r_OK = [True,True,True, True]
    if const.X:
        X_OK = (max_pos[0] - min_pos[0]) < (const.X[3] - const.X[2])
    if const.Y:
        Y_OK = (max_pos[1] - min_pos[1]) < (const.Y[3] - const.Y[2])
    if const.Z:
        if (const.Z[2] == const.Z[3]):
            if debug:
                print('Constraint Z is constant for background %s. Ignoring Z constraint'%bg.name)
            # Z_OK = (max_pos[2] - min_pos[2]) < const.Sz[3]
            Z_OK = True #TODO: Is this the best way to do it?
        else:
            Z_OK = (max_pos[2] - min_pos[2]) < (const.Z[3] - const.Z[2])
    if const.r:
        oX, oY, oZ = const.origin
        maxR = ((max_pos[0]-oX)**2+(max_pos[1]-oY)**2)**.5
        minR = ((min_pos[0]-oX)**2+(min_pos[1]-oY)**2)**.5
        rA = True if const.r[2] is None else (minR-const.Sz[3])>=const.r[2]
        rB = True if const.r[3] is None else (maxR+const.Sz[3])<=const.r[3]
        r_OK = rA and rB
    if all([X_OK, Y_OK, Z_OK, r_OK]):
        return True
    else:
        if debug:
            print("Action incompatible with bg")
            print("max pos for action", max_pos)
            print("min pos for action", min_pos)
            print("ObConstraints:")
            print("Origin:", const.origin)
            print("X", const.X)
            print("Y", const.Y)
            print("Z", const.Z)
            print("Size", const.Sz)
            print("X,Y,Z ok:", [X_OK, Y_OK, Z_OK, r_OK])
        return False


dbi = bvp.DBInterface()
all_bgs = dbi.query(type="Background")
all_actions = dbi.query(type="Action")

# bg = dbi.query(1, type='Background', name='BG_019_Tent')
# act = dbi.query(1, type='Action', name='armada_01')
ob = dbi.query(semantic_category='human')[0]

x = len(all_bgs)
y = len(all_actions)

compat = np.zeros((40,40))

for i in range(x):
    for j in range(y):
        compat[i,j] += 1*(check_compatibility(ob,all_bgs[i],all_actions[j], debug=False))

bg_compats = np.sum(compat,axis=1)
act_compats = np.sum(compat,axis=0)


bad_bg_indices = np.arange(x)[bg_compats < threshold*x]
bad_act_indices = np.arange(x)[act_compats < threshold*y]

np.set_printoptions(threshold=np.nan)
print(compat)
print([all_bgs[bg].name for bg in bad_bg_indices])
print([all_actions[act].name for act in bad_act_indices])