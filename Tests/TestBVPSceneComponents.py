import bvp,bpy
Lib = bvp.bvpLibrary()
Skies = [x['name'] for x in Lib.skies]
BGs = [x['name'] for x in Lib.backgrounds]
Obs = [x['name'] for x in Lib.objects]
Shads = [x['name'] for x in Lib.shadows]

# Quickie Position Testers:
uv = bpy.ops.mesh.primitive_uv_sphere_add
cu = bpy.ops.mesh.primitive_cube_add

def SkyTest():
	Sk = bvp.Sky(Skies[0],Lib)
	Scn = bvp.Scene()
	Sk.PlaceSky(Scn)
def BGTest():
	BG = bvp.Background(BGs[1],Lib)
	BG.PlaceBG()
def ObTest():
	Ob = bvp.Object(Obs[0],Lib)
	Ob.PlaceObj()
def ShadowTest():
	Sh = bvp.Shadow(Shads[0],Lib)
	Sh.PlaceShadow()
def CamTest():
	bvpC = bvp.bvpCamConstraint(speed=(5.,.33,4,6),pan=False,r=(35,3,25,45),theta=(30,3,20,50))
	Fr = [1,30] # Vary this to see if speed is constant
	for ii in range(1):
		Cam = bvp.Camera(location=bvpC.sampleCamPos(Fr))
		Cam.PlaceCam()

#SkyTest() # Works
#BGTest() # Missing textures - need to pack textures with files!
#ObTest() # Works
#ShadowTest() # To come!
CamTest()