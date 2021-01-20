# Simple script to test basic functionality in BVP
# (To see if your Blender install is working properly)

import bvp,random
# Get host computer name
host = bvp.utils.basics.GetHostName()
# Set up basic scene
B = bvp.Background('*outdoor')
C = bvp.Camera()
S = bvp.Scene(Num=1,BG=B,Cam=C,FrameRange=(1,1),fPath='BlendTest_%s_%06d_##'%(host,random.randint(1,10000)))
# Populate from library
a = bvp.Object('*vehicle')
#b = bvp.Object('*animal')
#c = bvp.Object('*furniture')
OL = [a]
S.PopulateScene(OL,ObOverlap=.25,MinSz2D=.1)
# Create & render 
RO = bvp.RenderOptions()
RO.resolution_percentage = 50
RO.BVPopts['BasePath']+=('Scenes/%s')
RO.BVPopts['LogFileAdd'] = host
SL = bvp.SceneList(ScnList=[S],RenderOptions=RO)
SL.Render(RenderType=('Image','ObjectMasks','Normals','Zdepth'),RenderGroupSize=1)