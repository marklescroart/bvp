'''
.B.lender .V.ision .P.roject file operation

Lists properties for all shadows (groups) in a .blend file, and prints them
to a text file called "shadowProps.txt", which is stored in the main bvp 
directory. This is useful as a human-readable reference for all the shadows
in a directory. Also, the text file can be amended (for example, to specify 
the true "realWorldSize" of each shadow). The amended file can then be used 
by "SetShadowProps.py" to (re-) set properties of shadows (groups). In this 
way, it's possible to modify the properties of the groups within many files 
at once.

Each group will have its own line in the text file, thus:
GrpName :: NewGrpName :: realWorldSize :: semanticCatString

GrpName = the name of the group in the .blend file
NewGrpName = "x" by default. If it is changed from "x", 
	then "SetGroupProps" will change the name of the group 
	to the NewGrpName
realWorldSize = size in meters (floating point value)
semanticCatString = hierarchical list of categories to which the shadow 
	belongs, from most general to most specific. 

Other related files:
SetShadowProps.py - uses the (modified) file saved by this script to (re-) set 
	shadow properties in a .blend file.
GetShadowProps.py - creates a list of property dicts for each group in a file, 
	stored in a .pik file (Category_Blah.blend -> Category_Blah.pik)

ML 2012.02.15
'''

# Imports
import bpy,re,os
###--- Change this line to change file written out! ---###
#sName = '/auto/k6/mark/BlenderFiles/objectList.txt'
# sName = bvp.Settings.Files.skyPropFile
sName = '/auto/k6/mark/BlenderFiles/shadowProps.txt'
###--- Change to here ---###
fName = os.path.split(bpy.data.filepath)[-1]
with open(sName,'a') as fid:
	fid.write('<%s>\n'%(fName))
	BaseCat = re.search('(?<=Category_)[A-Z,a-z,0-9]*',fName).group()
	for G in bpy.data.groups:
		try:
			Sz = G.objects[0]['RealWorldSize']
		except:
			Sz = 1.000
		try:
			SemStr = G.objects[0]['SemanticCat']
		except:
			SemStr = BaseCat.lower()
		S = '%s:: x :: %.3f :: %s\n'%(G.name,Sz,SemStr)
		fid.write(S)
