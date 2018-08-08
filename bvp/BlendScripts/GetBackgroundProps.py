"""
.B.lender .V.ision .P.roject file operation

Gets properties for all backgrounds in a .blend file. Stores properties in a list 
of dictionaries (one dict for each background (group) in the file), and saves that 
list in a pickle (.pik) file with the same name as the .blend file.

These .pik files are loaded by the bvpLibrary class.

dictionaries are of the form:
{
'fname':'/path/to/Category_Blah.blend',
'name':'BG_001_Whatever',
'semantic_category':['outside','natural']
'real_world_size':100.000, # size of whole space in meters
'lens':50., # focal length for scene camera, in mm
'nVertices':1000,
'nFaces':900,
'obConstraints':bvpObConstraints(), # Derived from empty objects in the scene
'CamConstraint':bvpCamConstraints(),
'obstacles':None # To come!
'obSemanticCat':'all', ## List of object categories that can (reasonably) populate this scene
'sky_semantic_category': 'all', ## List of sky categories that can go with this background.
'obstacles':None, ## TO DO! background objects  ##

}


ML 2012.02
"""

# Imports
import bpy,bvp,os,re
from bvp.utils.basics import save_pik
from bvp.utils.blender import GetConstr

d = []
fName = os.path.split(bpy.data.filepath)[-1]
BaseCat = re.search('(?<=Category_)[A-Z,a-z,0-9]*',fName).group()
Grp = [g for g in bpy.data.groups if 'BG' in g.name] # Exclude other groups!
for G in Grp:
	gOb = [g for g in G.objects if g.type=="EMPTY"][0]
	Obst = [g for g in G.objects if g.type=="MESH" and 'obst' in g.name.lower()]
	print(Obst)
	# Semantic category of background
	try:
		semCat = gOb['semantic_category'].split(',')
	except:
		semCat = [BaseCat.lower()]
	# Add file title category to list of categories, if not present:
	if not semCat[0].lower()==BaseCat.lower():
		semCat = [BaseCat.lower()]+semCat
	# Allowable semantic categories for objects / skies
	try:
		obCat = gOb['ObjectSemanticCat'].split(',')
	except:
		obCat = ['all']
	try:
		skyCat = gOb['sky_semantic_category'].split(',')
	except:
		skyCat = ['all']
	
	# Camera & object position constraints 
	if len([x for x in G.objects if x.type=='EMPTY']) > 0:
		try:
			print('LOOKING FOR TF!!!\n\n')
			TF = bvp.Settings['LibDefaults']['LockZtoFloor']
			print("FOUND THE FUCKER!")
			if TF:
				print('Objects LOCKED THE FUCK DOWN!')
			else:
				print("Objects are FREEEEEE!")
			camConstr,obConstr = GetConstr(G,LockZtoFloor=TF)
		except:
			# Fill in None values for now...
			camConstr = None # Size=...
			obConstr = None # Size=...			
	else:
		# Needs modification! defaults should depend on real world size / size of floor mesh / something...
		# OR: simply raise error, and demand that all files have pos constraints.
		camConstr = bvp.CamConstraint() # Size=...
		obConstr = bvp.bvpObConstraint() # Size=...
	try:
		rws = gOb['RealWorldSize'], # of the whole space
	except:
		rws = 100.
	try:
		Lens = gOb['Lens']
	except:
		Lens = 50.
	d.append(dict(
			fname=bpy.data.filepath,
			name=G.name,
			semantic_category=semCat,
			real_world_size=rws,
			lens=Lens,
			nVertices=sum([len(oo.data.vertices) for oo in G.objects if oo.type=='MESH']),
			nFaces=sum([len(oo.data.polygons) for oo in G.objects if oo.type=='MESH']),
			obConstraints=obConstr,
			CamConstraint=camConstr,
			obSemanticCat=obCat, ## List of object categories that can (reasonably) populate this scene
			sky_semantic_category=skyCat, ## List of sky categories that can go with this background.
			obstacles=[bvp.Object(pos3D=list(o.location),size3D=max(o.dimensions)) for o in Obst], ## To come! ##
			))
sName = bpy.data.filepath.replace('.blend','.pik')
save_pik(d,sName)