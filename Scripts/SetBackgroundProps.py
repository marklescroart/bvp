'''
Sets properties for all backgrounds (groups) in a .blend file, based on the 
text file "backgroundProps.txt" in the main bvp directory.

See ListGroupProps.py for file format conventions for the text file.

ML 2012.02.12
'''
import bpy,sys,os
from bvp.utils.blender import DeclareProperties
# Get groups in this file
AllGrp = bpy.data.groups
# Define RealWorldSize, semantic_category (more?) as object properites in Blender
DeclareProperties() 
###--- Modify these lines to change object file ---###
if len(sys.argv)>1:
	LibDir = sys.argv[-1]
else:
	LibDir = bvp.Settings['Paths'][LibDir]
fRead = os.path.join(LibDir,'backgroundProps.txt')
#fRead = '/auto/k6/mark/BlenderFiles/backgroundProps.txt'
###--- To here ---###

with open(fRead,'r') as fid:
	f = fid.readlines()
f = [x for x in f if not '<' in x]
for ss in f:
	Tmp = [x.strip() for x in ss.split('::')]
	GrpNm,NewGrpNm,RealWorldSz,Lens,semantic_category,ObjectSemanticCat,sky_semantic_category = Tmp
	if GrpNm in AllGrp:
		G = AllGrp[GrpNm]
		gOb = [g for g in G.objects if g.type=="EMPTY"]
		for o in gOb:
			print('Setting rws to: %s'%RealWorldSz)
			o.RealWorldSize = float(RealWorldSz)
			o.Lens = float(Lens) # Focal length, in mm
			o.semantic_category = semantic_category
			o.ObjectSemanticCat = ObjectSemanticCat
			o.sky_semantic_category = sky_semantic_category
		if not NewGrpNm=='x':
			G.name = NewGrpNm
# Save file w/ new props:
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
