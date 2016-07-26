''' 
Initialization of utils.
Couple handy-dandy functions:
'''

from . import basics
from . import blender
from . import bvpMath
#from . import plot # ? necessary? NO. Kill me.

def set_scn():
	'''Quickie default setup of camera + lighting for an object
	'''
	cam = bvp.Camera()
	sky = bvp.Sky()
	ropts = bvp.RenderOptions()
	scn = bvp.Scene(cam=cam, sky=sky)
	scn.create()
	scn.apply_opts(render_options=ropts)