"""
.B.lender .V.ision .P.roject file operation

Gets properties for all skies in a .blend file. Stores properties in a list 
of dictionaries (one dict for each sky (group) in the file), and saves that 
list in a pickle (.pik) file with the same name as the .blend file.

These .pik files are loaded by the bvpLibrary class.

Critical to the sky 

dictionaries are of the form:
{
'fname':'/path/to/Category_Blah.blend',
'name':'Sky_001_Whatever',
'semantic_category':['cloudy','day']
'real_world_size':100.000, # size of whole space in meters
'nVertices':1000,
'nFaces':900,
}

ML 2012.02
"""

# Imports
import bpy,bvp,os,re
import math as bnp
from bvp.utils.basics import savePik
from bvp.utils.blender import GetConstr

d = []
fName = os.path.split(bpy.data.filepath)[-1]
BaseCat = re.search('(?<=Category_)[A-Z,a-z,0-9]*',fName).group()
for G in bpy.data.groups:
	try:
		try:
			semCat = G.objects[0]['semantic_category'].split(',')
		except:
			semCat = [BaseCat]
		# Add file title category to list of categories, if not present:
		if not semCat[0].lower()==BaseCat.lower():
			semCat = [BaseCat.lower()]+semCat
	except:
		semCat = [BaseCat]
	try:
		rws = G.objects[0]['RealWorldSize'], # of the whole space
	except:
		rws = 100.
	# Light locations and rotations
	try:
		LightLoc = [list(L.location) for L in G.objects if L.type=='LAMP']
		LightRot = [[bnp.degrees(x) for x in L.rotation_euler] for L in G.objects if L.type=='LAMP']
		LightType = [L.data.type for L in G.objects if L.type=='LAMP']
	except:
		raise Exception("Why aren't there any lamps in sky %s??"%G.name)

	d.append(dict(
			fname=bpy.data.filepath,
			name=G.name,
			semantic_category=semCat,
			real_world_size=rws,
			lightLoc=LightLoc,
			lightRot=LightRot,
			lightType=LightType,
			nVertices=sum([len(oo.data.vertices) for oo in G.objects if oo.type=='MESH']),
			nFaces=sum([len(oo.data.faces) for oo in G.objects if oo.type=='MESH']),
			))
sName = bpy.data.filepath.replace('.blend','.pik')
savePik(d,sName)