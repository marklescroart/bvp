import bvp
if bvp.Is_Numpy:
    import numpy as np

# Define a camera w/ default parameters
C = bvp.Camera()
# Define an empty object (sphere)
O = bvp.Object()
# Test inverse perspective projection:
ImPos = (.9,.1) # x,y, as proportion of image
Z = -10 # Distance from camera
ObPos = bvp.utils.bvpMath.PerspectiveProj_Inv(ImPos,C,Z)
print(ObPos)

if bvp.Is_Blender:
    # Set render properties:
    #RO = bvp.RenderOptions()
    #RO.ApplyOpts()
    # Place Objects:
    O.pos3D = ObPos
    O.PlaceObj()
    #C.PlaceCam()
    
'''
# Set Blender scene fix position to these, render
cPos = [-5.3,-32.67,12.8] # cTheta was perfect: 74.5,0,-14.8
fPos = [3.289,-.098,3.454]
## - Q1, low fixation
# cPos = [15.,15.,5.] # 
# fPos = [2.,2.,2.] 
## - Q2, low fixation
# cPos = [15.,-20.,5.] # cTheta was perfect: [83.3,0,30.6]
# fPos = [2.,2.,2.] 
## - Q3, low fixation 
# cPos = [-12.,13.,5.] # cTheta was perfect: []
# fPos = [2.,2.,2.] 
## -Q4, low fixation
# cPos = [-24.,-8.,5.] # cTheta was perfect: [ 83.9,0,-69.0]
# fPos = [2.,2.,2.] 

oPos = [0.,0.,0.]
C = test.bvp.Camera({'location':[cPos],'fixPos':[fPos]})
O = test.bvp.Object({'pos3D':oPos})

imPos = PerspectiveProj(O,C)
'''