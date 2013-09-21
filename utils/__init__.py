''' 
Initialization of utils.
Couple handy-dandy functions:
'''
import bvp

def setScn():
	'''
	Quickie camera + lighting for an object
	'''
	bvp.bvpCamera().PlaceCam()
	bvp.bvpSky().PlaceSky()
	bvp.RenderOptions().ApplyOpts()