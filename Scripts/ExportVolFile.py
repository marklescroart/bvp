'''
Exports all groups in a file to voxelized .vol files, for later processing of shape skeleton (medial axis structure)

ML 2012.02
'''
# Imports
import bpy,bvp,os,re
# Path setup
fBase = os.path.join(bvp.Settings['Paths']['LibDir'],'Objects','VOL_Files','%s')
# Parameters
bvp.Verbosity_Level = 5
Is_Overwrite=False
vRes = 96.
buf = 4.
# Warm-up for stupid Blender: 
Scn = bpy.context.scene
gOb = [o for o in Scn.objects if o.users_group]
Gx = bpy.data.groups[gOb[0].users_group[0].name]
vL,vN = bvp.utils.blender.getVoxelizedVertList(Gx,size=10./vRes)

# Get objects!
for G in bpy.data.groups:
	# File name
	fDir,blendF = os.path.split(bpy.data.filepath)
	Cat = re.search('(?<=Category_)[^_^.]*',blendF).group()
	Res = '%dx%dx%d'%(vRes+buf,vRes+buf,vRes+buf*2)
	ff = Cat+'_'+G.name+'.'+Res+'.verts'
	fNm = fBase%(ff)
	if os.path.exists(fNm):
		if Is_Overwrite:
			vL,nL = bvp.utils.blender.getVoxelizedVertList(G,size=10./vRes,fNm=fNm)
		else:
			print('Skipping %s!'%G.name)
	else:
		vL,nL = bvp.utils.blender.getVoxelizedVertList(G,size=10./vRes,fNm=fNm)