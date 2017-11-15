# Scene creation demo for .B.lender .V.ision .P.roject
# 
# Scene creation example 2: random* objects, backgrounds, skies, and camera position, with shadows!
#
# ML 2012.07.25 

# Imports
import bvp,bpy,random,os
# Library Creation
LibDir = '/auto/k6/mark/BlenderFiles/'
Lib = bvp.bvpLibrary(LibDir)
### --- Library cleanup? --- ###
# (if necessary, exclude particular categories, etc)

# Choose how long we want scene to be (in frames, @15fps)
frames = (1,44) # ~3 seconds
# Set up render options for scene
RO = bvp.RenderOptions(dict(filepath='~/Desktop/DemoSceneRenders/Scene01_##',
							BVPopts={'Type':'FirstFrame'}))
# Choose random BG for scene
BG = bvp.Background('*outdoor',Lib)
# Choose Sky for a scene based on BG sky constraints
Sky = bvp.Sky('*skies',Lib)
# Shadow
if Sky.semantic_category:
	if 'dome' in Sky.semantic_category:
		if len(Sky.lightLoc)>1:
			Shad=None
		elif len(Sky.lightLoc)==1:
			if 'sunset' in Sky.semantic_category:
				Shad = bvp.Shadow('*west',Lib)
			else:
				fn = lambda x: 'clouds' in x['semantic_category'] and not 'west' in x['semantic_category']
				Shad = bvp.Shadow(fn,Lib)
		else:
			Shad=None
else:
	Shad = None

# Choose camera positions based on BG camera constraints
# Before calling "sampleCamPos", you can update camera constraints to
# limit camera motion in several ways (pan only, zoom only, speed constriants,
# more - see bvpCamConstraint help) 
CamPos = BG.CamConstraint.sampleCamPos(frames=frames)
FixPos = BG.CamConstraint.sampleFixPos(frames=frames)
Cam = bvp.Camera(location=CamPos,fixPos=FixPos,frames=frames)
# Initialize (empty) scene
Scn = bvp.Scene(Num=1,BG=BG,Sky=Sky,Cam=Cam,FrameRange=frames,FrameRate=15)
# Get 3 objects to place in scene. Search the library with "*<semCatStr>" syntax to return
# an object with the semantic category <semCatStr>. 
obID = ['*animal','*appliance','*car']
ObList = []
for o in obID:
	ObList.append(bvp.Object(obID=o,Lib=Lib,rot3D=(0,0,random.random()*360.)))

Scn.PopulateScene(ObList)
Scn.Create(rOpts=RO)
Scn.Render(RO)