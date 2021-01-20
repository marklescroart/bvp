"""
.B.lender .V.ision .P.roject file operation

Lists properties for all backgrounds (groups) in a .blend file, and prints them
to a text file called "backgroundProps.txt", which is stored in the main bvp 
directory. This is useful as a human-readable reference for all the backgrounds
in a directory. Also, the text file can be amended (for example, to specify 
the true "real_world_size" of each background). The amended file can then be used 
by "SetBackgroundProps.py" to (re-) set properties of backgrounds (groups). In this 
way, it's possible to modify the properties of the groups within many files 
at once.

Each group will have its own line in the text file, thus:
name :: NewGrpName :: real_world_size :: semanticCatString :: ob

name = the name of the group in the .blend file
NewGrpName = "x" by default. If it is changed from "x", 
    then "SetBGProps" will change the name of the group 
    to the NewGrpName
real_world_size = size in meters (floating point value)
semanticCatString = hierarchical list of categories to which the object 
    belongs, from most general to most specific. 

Other related files:
SetBGProps.py - 
GetBGProps.py - creates a list of property dicts for each group in a file, 
    stored in a .pik file (Category_Blah.blend -> Category_Blah.pik)

ML 2012.02.15
"""

# Imports
import bpy,re,os,sys
###--- Change this line to change file written out! ---###
# sName = '/auto/k6/mark/BlenderFiles/objectList.txt'
# sName = bvp.settings.files.ObListFile
# sName = '/auto/k6/mark/BlenderFiles/backgroundProps.txt'
if len(sys.argv)>1:
    LibDir = sys.argv[-1]
else:
    LibDir = bvp.Settings['Paths'][LibDir]
sName = os.path.join(LibDir,'backgroundProps.txt')
###--- Change to here ---###
fName = os.path.split(bpy.data.filepath)[-1]
with open(sName,'a') as fid:
    fid.write('<%s>\n'%(fName))
    BaseCat = re.search('(?<=Category_)[A-Z,a-z,0-9]*',fName).group()
    Grps = [g for g in bpy.data.groups if 'BG' in g.name]
    for G in Grps:
        gOb = [g for g in G.objects if g.type=="EMPTY"][0]
        try:
            Sz = gOb['RealWorldSize']
        except:
            Sz = 100.000
        try:
            SemStr = gOb['semantic_category']
        except:
            SemStr = BaseCat.lower()
        try:
            obStr = gOb['ObjectSemanticCat']
        except:
            obStr = 'all'
        try:
            skyStr = gOb['sky_semantic_category']
        except:
            skyStr = 'all'
        try:
            Lens = gOb['Lens']
        except:
            Lens = 50.
        S = '%s:: x :: %.3f :: %.1f :: %s :: %s :: %s\n'%(G.name,Sz,Lens,SemStr,obStr,skyStr)
        fid.write(S)
