'''
.B.lender .V.ision .P.roject file operation

Gets properties for all shadows in a .blend file. Stores properties in a list 
of dictionaries (one dict for each shadow (group) in the file), and saves that 
list in a pickle (.pik) file with the same name as the .blend file.

These .pik files are loaded by the bvpLibrary class.

dictionaries are of the form:
{
'parentFile':'/path/to/Category_Blah.blend',
'grpName':'Shadow_001_Whatever',
'semanticCat':['noise','clouds'] # More semantic categories for shadows??
'realWorldSize':100.000, # size of whole shadow in meters
'nVertices':1000,
'nFaces':900,
}

ML 2012.02
'''

# Imports
import bpy,bvp,os,re
from bvp.utils.basics import savePik
from bvp.utils.blender import GetConstr

d = []
fName = os.path.split(bpy.data.filepath)[-1]
BaseCat = re.search('(?<=Category_)[A-Z,a-z,0-9]*',fName).group()
for G in bpy.data.groups:
	try:
		try:
			semCat = G.objects[0]['SemanticCat'].split(',')
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
	d.append(dict(
			parentFile=bpy.data.filepath,
			grpName=G.name,
			semanticCat=semCat,
			realWorldSize=rws,
			nVertices=sum([len(oo.data.vertices) for oo in G.objects if oo.type=='MESH']),
			nFaces=sum([len(oo.data.faces) for oo in G.objects if oo.type=='MESH']),
			))
sName = bpy.data.filepath.replace('.blend','.pik')
savePik(d,sName)