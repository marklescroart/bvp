"""
.B.lender .V.ision .P.roject file operation

Gets properties for all objects (groups) in a .blend files. Stores properties in a list 
of dictionaries (one dict for each group in the file), and saves that list in a pickle
(.pik) file with the same name as the .blend file.

These .pik files are loaded by the bvpLibrary class.

dictionaries are of the form:
{
'fname':'/path/to/Category_Blah.blend',
'name':'001_Whoopee',
'realWorldSize':0.2,
'basicCat':'whoopie cushion',
'semantic_category':['artsm','tool','whoopie cushion']
'nVertices':1000,
'nFaces':900,
'nPoses' = None, # None for un-rigged objects
'constraints':bvpObConstraints() # Constraints on position of other objects wrt 
								 # this object, or on this object wrt background 
								 # (e.g., does this go on the wall? the ceiling?)
								 # THIS IS NOT DONE YET! (2012.02.29)
									}

Object constraints are not working yet (2012.02.29)!

ML 2012.02
"""

# Imports
import bpy,bvp,os,re,copy
from bvp.utils.basics import savePik

d = []
fName = os.path.split(bpy.data.filepath)[-1]
BaseCat = re.search('(?<=Category_)[A-Z,a-z,0-9]*',fName).group()

for G in bpy.data.groups:
	
	try:
		# slight processing of semantic categories before storage in list
		semCat = G.objects[0]['semantic_category'].split(',')
		# "*" in semantic_category list denotes the "basic level" category of the object (as in Rosch, 1976)
		basicCat = [x.replace('*','') for x in semCat if '*' in x] # better be only 1 asterisk!
		semCat = [x.replace('*','') for x in semCat]
		if basicCat:
			basicCat = basicCat[0]
	except:
		semCat = [BaseCat]
		basicCat = BaseCat
	# Add file title category to list of categories, if not present:
	if not semCat[0].lower()==BaseCat.lower():
		semCat = [BaseCat.lower()]+semCat
	# (2) Real world size
	try:
		rws = G.objects[0]['RealWorldSize'], # of the whole space
	except:
		rws = 2.
	# (3) Poses
	Rig = [o for o in G.objects if o.type=='ARMATURE']
	nPoses = None # by default
	if Rig:
		if len(Rig)>1:
			raise Exception('More than one rig present in group %s! Abort, abort!'%G.name)
		Rig = Rig[0]
		if Rig.pose_library:
			nPoses = len(Rig.pose_library.pose_markers)
	try:
		nFaces = sum([len(oo.data.faces) for oo in G.objects if oo.type=='MESH'])
	except:
		# New for version 2.63 w/ bmeshes:
		nFaces = sum([len(oo.data.polygons) for oo in G.objects if oo.type=='MESH'])
	d.append(dict(
			fname=bpy.data.filepath,
			name=G.name,
			basicCat=basicCat,
			semantic_category=semCat,
			realWorldSize=rws,
			nVertices=sum([len(oo.data.vertices) for oo in G.objects if oo.type=='MESH']),
			nFaces=nFaces,
			nPoses=nPoses,
			constraints=None, ## TO COME! ##
			))
sName = bpy.data.filepath.replace('.blend','.pik')
savePik(d,sName)
