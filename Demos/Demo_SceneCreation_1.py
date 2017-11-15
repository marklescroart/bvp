# Scene creation demo for .B.lender .V.ision .P.roject
# 
# Scene creation example 2: random* objects, backgrounds, skies, and camera position, with shadows!
#
# ML 2012.03.06 # STILL WORKING! NO DIFF FROM Demo_SceneCreation_1.py!

# Imports
import bvp,bpy,random,os

# Library Creation
LibDir = '/auto/k6/mark/BlenderFiles/'
#LibDir = '/Users/mark/Documents/BlenderFiles/'
Lib = bvp.bvpLibrary(LibDir)
# Choose how long we want scene to be (in frames, @15fps)
frames = (1,44) # ~3 seconds
# Set up render options for scene
RO = bvp.RenderOptions(dict(BVPopts={'Type':'FirstFrame','BasePath':'/Users/mark/Desktop/DemoSceneRenders/Scene01_##',}))
# Choose random BG for scene
BG = bvp.Background('*outdoor',Lib)
# Choose Sky based on BG constraints for sky
Sky = bvp.Sky('*'+BG.sky_semantic_category[0],Lib)
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
ObList = [bvp.Object(o,Lib,rot3D=(0,0,random.random()*360.)) for o in obID]
Scn.PopulateScene(ObList)
Scn.Create(rOpts=RO)
#Scn.Render(RO)