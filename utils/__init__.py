''' 
Initialization of utils.
Couple handy-dandy functions:
'''
import bvp

def set_scn():
	'''
	Quickie camera + lighting for an object
	'''
	bvp.bvpCamera().Place()
	bvp.bvpSky().Place()
	bvp.RenderOptions().apply_opts()