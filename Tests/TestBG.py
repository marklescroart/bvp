'''
Script to test out a background (to see if constraints are working properly)
'''
# Imports
import bvp
import bpy
import random
import os
import re
from bvp.Classes.constraint import get_constraint

# Get database of objects
dbi = bvp.DBInterface()

# Misc. scene parameters
n_objects = 3 # why not?
frames = (1,15) # one sec of video
ro = bvp.RenderOptions()
scn = bpy.context.scene

# Choose random objects for scene
obIdx = [random.randint(0,Lib.n_objects) for x in range(n_objects)]
ObList = [bvp.Object(Lib.objects[o]['name'],Lib) for o in obIdx]

# Get position constraints for objects, camera
Eob = [o for o in bpy.context.scene.objects if o.type=='EMPTY' and o.users_group]
G = Eob[0].users_group[0]
CamC,ObC = GetConstr(G)
print('Decided group name is %s.'%G.name)

# TO COME: Get sky w/ sky constraints!
Sky = bvp.Sky()
# TO COME: Get camera focal length from constraints!
# Camera re-set w/ scene! 
# Background
BG = bvp.Background()
BG.obConstraints = ObC
BG.CamConstraint = CamC
fName = os.path.split(bpy.data.filepath)[-1]
BaseCat = re.search('(?<=Category_)[A-Z,a-z,0-9]*',fName).group()
# Semantic category of background
try:
	semCat = G.objects[0]['semantic_category'].split(',')
except:
	semCat = [BaseCat.lower()]
# Add file title category to list of categories, if not present:
if not semCat[0].lower()==BaseCat.lower():
	semCat = [BaseCat.lower()]+semCat
BG.semantic_category = semCat
# Allowable semantic categories for objects / skies / **Shadows!** (TO DO)
try:
	obCat = G.objects[0]['ObjectSemanticCat'].split(',')
except:
	obCat = ['all']
BG.obSemanticCat = obCat
try:
	skyCat = G.objects[0]['sky_semantic_category'].split(',')
except:
	skyCat = ['all']
BG.sky_semantic_category = skyCat
try:
	rws = G.objects[0]['RealWorldSize'], # of the whole space
except:
	rws = 100.
BG.realWorldSize = rws

# Create scene
# TO DO: shadow?
scn.layers = [True]+[False]*19
bvp_scn = bvp.Scene(0,BG=BG,Sky=Sky,FrameRange=frames)
bvp_scn.PopulateScene(ObList)

bvp_scn.Cam.PlaceCam(IDname='%03d'%bvp_scn.Num)
Sky.PlaceSky()
for o in bvp_scn.Obj:
	o.PlaceObj()
bvp_scn.ApplyOpts(ro)
scn.layers = [True]*20