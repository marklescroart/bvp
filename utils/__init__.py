""" 
Initialization of utils.
Couple handy-dandy functions:
"""

from . import basics
from . import blender
from . import bvpMath
#from . import plot # ? necessary? NO. Kill me.

def set_scn():
    """Quickie default setup of camera + lighting for an object
    """
    from ..Classes.Camera import Camera
    from ..Classes.Background import Background
    from ..Classes.Scene import Scene
    from ..Classes.RenderOptions import RenderOptions
    
    cam = Camera()
    sky = Sky()
    ropts = RenderOptions()
    scn = Scene(cam=cam, sky=sky)
    scn.create()
    scn.apply_opts(render_options=ropts)