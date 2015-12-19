''' 
Initialization of utils.
Couple handy-dandy functions:
'''
import bvp

def set_scn():
	'''
	Quickie camera + lighting for an object
	'''
	cam = bvp.bvpCamera()
	sky = bvp.bvpSky()
	RO = bvp.RenderOptions()
	scn = bvp.bvpScene(cam=cam,sky=sky)
	scn.create()
	scn.apply_opts(render_options=RO)