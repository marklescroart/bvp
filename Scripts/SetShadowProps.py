'''
Sets properties for all shadows (groups) in a .blend file, based on the 
text file "shadowProps.txt" in the main bvp directory.

See ListShadowProps.py for file format conventions for the text file.

ML 2012.02.12
'''
import bpy
from bvp.utils.blender import DeclareProperties
# Get groups in this file
AllGrp = bpy.data.groups
# Define RealWorldSize, SemanticCat (more?) as object properites in Blender
DeclareProperties() 
###--- Modify these lines to change object file ---###
fRead = '/auto/k6/mark/BlenderFiles/shadowProps.txt'
###--- To here ---###

with open(fRead,'r') as fid:
	f = fid.readlines()
f = [x for x in f if not '<' in x]
for ss in f:
	Tmp = [x.strip() for x in ss.split('::')]
	GrpNm,NewGrpNm,RealWorldSz,SemanticCat = Tmp
	if GrpNm in AllGrp:
		G = AllGrp[GrpNm]
		for o in G.objects:
			o.RealWorldSize = float(RealWorldSz)
			o.SemanticCat = SemanticCat
		if not NewGrpNm=='x':
			G.name = NewGrpNm
# Save file w/ new props:
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
