''' 

#######################################################

DEPRECATED / NEVER USED! 

Wanted more control of voxelization geometry / morphology, so I am now doing voxelization in Blender, and saving
directly to a binary file w/ ".vol" extension

#######################################################


Export of objects to .off files for shape skeleton processing. 

This script will import objects and set scene parameters, and then either: (1) render the scene and discard the objects, or (2) create a new scene in Blender (for inspection of objects / materials / whatever).  

requires environment variable "BVPDIR" to be set to base directory (dir containing BlenderRender/ and BlenderFiles/)

ML 2011.06.24

'''
import off_export,bvp,bpy,os,re
import pfSkel as sk
Div = '~'*40
print('%s\n~~~    Running mlOFFexportLoop.py    ~~~\n%s '%(Div,Div))
print(bvp.version)

Res = sk.Settings['VolRes'] # Default (2012.08.13) = 96
# establish memory-saving mode for multiple imports: 
#? necessary?

#LibDir = bvp.Settings['Paths']['LibDir']
#if not LibDir==sk.Settings['LibDir']:
#	raise Exception('Path problem! pfSkel settings "LibDir" does not match bvp settings "LibDir". GAAAAAA!')

Lib = bvp.bvpLibrary()
grpName = 'Reptile_005_Frog' #'Mammal_005_Cat'
#for grpName in Lib.getGrpNames():
# Get & add object
O = bvp.bvpObject(grpName,Lib,size3D=10)
O.PlaceObj()
G = bpy.context.object
# Make proxy objects & create render mesh for all objects in group
ObList = []
scn = bpy.context.scene
for o in G.dupli_group.objects:
	bvp.utils.blender.GrabOnly(G)
	bpy.ops.object.proxy_make(object=G.name,type=o.name)
	NewOb = bpy.context.object
	if NewOb.type=='MESH':
		me = NewOb.to_mesh(scn, True, 'RENDER')
		NewOb.data = me
	else:
		continue
	ObList.append(NewOb)
# Get rid of 
scn.objects.unlink(G)
# Join objects
for o in ObList:
	o.select = True
bpy.ops.object.join()
Ob = bpy.context.object
bvp.utils.blender.GrabOnly(Ob)
# Export off
OFFf = os.path.join(sk.OFFdir,grpName+'.off')
off_export.write(OFFf)
# Voxelize off @ (default) resolution
sk.preproc.Voxelize(OFFf,Res=Res)
# (No way to know what file name will be without more info; so check directory for a file with the right name / max resolution:
VOLfList = [f for f in os.listdir(sk.OFFdir) if '.vol' in f and not 'SOLID' in f and sk.utils.GetMaxDim(f)==Res]
if len(VOLfList)>1:
	raise Exception("WTF! too many files!")
DimStr = re.search('(?<=.)[\d]*x[\d]*x[\d]*(?=.)',VOLfList[0]).group()
# Make into solid volume 
VOLf = os.path.join(sk.OFFdir,VOLfList[0])
VOLfs = VOLf.replace('.'+DimStr,'_SOLID.'+DimStr)
sk.preproc.FillVol(VOLf,VOLfs)

# Call pfSkel
SKELf = os.path.join(sk.SKELdir,VOLfList[0].replace('.vol',''))
print('VOLf and SKELf are:')
print(VOLfs)
print(SKELf)
print('Trying to run pfSkel...')
sk.MakeSkel(VOLfs,SKELf, # resolution is automatically read??
				ft='PF', # Potential field (vs. Gradient Diffusion Field, "GDF")
				fs=6, # Field strength, from 3 to 10. 6 seems to work OK
				phd=50, # % high divergence points. 50% = mid range
				dc=1, # number of voxels to expand (attempts to prevent wacky shit from thin protrusions)
				hds='all')  #high divergence points selected - 'all' or 'locmin' (local minima only)
