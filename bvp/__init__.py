"""
bvp (B.lender V.ision P.roject) is a module of functions and classes for creating visual 
stimuli within Blender. bvp functions are intended to allow creation of arbitrary scenes 
using libraries of "scene elements" (objects, backgrounds, skies/lighting setups, shadows,
and cameras). 

Scene elements are all managed by classes that wrap functionality of native Blender 
objects and store meta-data about each element (for example, the semantic category or
size of an object). Each individual scene element is stored in a archival .blend files,
and managed by a database system based on mongodb (http://www.mongodb.com/).

Scene elements can be combined using a Scene class, which has methods to populate a 
given scene with objects in random locations, render the scene, and more.

All relevant information for a set of scenes is stored in the SceneList 
class, which has* methods for permanent storage* / write-out of stimulus lists to 
archival hf5 files*. 

*Still to come 2014.10.23

#?# blenrig add-on scripts (available at jpbouza.com.ar/wp/downloads/blenrig/current-release/blenrig-4-0) for some models
#?# OpenEXR for handling Z depth / normal images

"""
# Startup stuff
from __future__ import absolute_import
__version__ = '0.2a' 

# Imports
import os
import time
import textwrap
import subprocess
from . import utils 
from .options import config

# Classes
from .Classes.action import Action
from .Classes.background import Background
from .Classes.camera import Camera
from .Classes.constraint import  ObConstraint, CamConstraint
from .Classes.material import Material
from .Classes.object import Object
from .Classes.render_options import RenderOptions
from .Classes.scene import Scene
#from .Classes.SceneList import SceneList # STILL WIP
from .Classes.shadow import Shadow
#from .Classes.Shape import Shape # STILL WIP Move to Object...?
from .Classes.sky import Sky

from . import DB
from . import files
from .DB import DBInterface

# NOTE: UPDATE LIST BELOW WHEN CLASSES ARE ALL DONE

bvp_dir = os.path.dirname(__file__)

def set_scn(fname='bvp_test', ropts=None, cam=None, sky=None):
    """Quickie default setup of camera + lighting for an object
    """    
    if cam is None:
        cam = Camera()
    if ropts is None:
        ropts = RenderOptions()
    if sky is None:
        sky = Sky()

    scn = Scene(camera=cam, sky=sky, fname=fname)
    scn.create(render_options=ropts)
    return scn


## -- Cluster -- ##
bvp_cluster_script = """
import bvp
tmp_script = '''{script}'''
stdout, stderr = bvp.blend(tmp_script, is_local=True, blend_file="{blend_file}", blender_binary="{blender_binary}", is_verbose={is_verbose})
done = False
if stderr:
    break_str = '='*50
    chk = stderr.split('\\n')
    # Exclude INFO lines in error file:
    chk1 = [c for c in chk if not c=='' and not c[:5]=='INFO:']
    if len(chk1)==0:
        done = True
    else:
        # Exclude Warning lines in error file:
        chk2 = [c for c in chk1 if not c=='' and not 'Warning' in c and not 'WARNING' in c and not c[:3]=='Fra']
        print('%s\\nFiltered error output:\\n%s'%(break_str, break_str))
        for c in chk2:
            print(c)
        if len(chk2)==1:
            print('%s\\nCode output (Warning detected!):\\n%s'%(break_str, break_str))
            print(stderr)
            done = True
    if not done:
        # OK, the error was real:
        print('%s\\nCode output:\\n%s'%(break_str, break_str))
        #print(out)
        print("(Suppressed)")
        print('%s\\nError output:\\n%s'%(break_str,break_str))
        print(stderr)
        raise Exception('Python error in Blender script! See above.')

"""

def blend(script, blend_file=None, is_local=True, blender_binary=None,
          tmpdir='/tmp/', is_verbose=False, **kwargs):
    """Run Blender with a given script.

    Parameters
    ----------
    script : string file name or script
        Script to run. Scripts saved to files are read into RAM and piped to blender
        command via the --python-expr argument 
    blend_file : string (optional)
        File path to Blender file
    is_local : bool
        True = run locally, False = run on cluster (if available)
    blender_binary : str
        path to executable file for blender. Useful if you want to sometimes
        use experimental versions of blender. If None, defaults to the 
        `blender_cmd` option in your config file.

    Other Parameters
    ----------------
    tmpdir : string file path
        Where to create a temp file (if so desired). 
    kwargs are fed to _cluster, if necessary

    Returns
    -------
    jobid : string
        ID for cluster job (or None, if cluster doesn't return job ids)
    """
    # Inputs
    if blend_file is None:
        blend_file = os.path.abspath(os.path.join(bvp_dir, 'BlendFiles', 'Blank.blend'))

    # Check for existence of script
    if os.path.exists(script):
        with open(script) as fid:
            lines = fid.readlines()
        script = '\n'.join(lines)

    # Run 
    if blender_binary is None:
        blender_binary = config.get('path', 'blender_cmd') #Settings['Paths']['BlenderCmd']
    blender_cmd = [blender_binary, '-b', blend_file, '--python-expr', script]
    if is_local:
        proc = subprocess.Popen(blender_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        try:
            # Change formatting of byte objects in python3
            stdout = stdout.decode()
            stderr = stderr.decode()
        except:
            pass
        return stdout, stderr
        
    else:
        try:
            from slurm_utils import run_script as _cluster
        except:
            print("No cluster code available. Please install slurm_utils (https://github.com:piecesofmindlab/slurm_utils).")
        # Call via cluster
        print(script)
        pyscript = bvp_cluster_script.format(script=script, blend_file=blend_file, is_verbose=is_verbose, blender_binary=blender_binary)
        jobid = _cluster(pyscript, **kwargs)
        return jobid

__all__ = ['Action', 'Background', 'Camera', 'ObConstraint', 'CamConstraint', 'Material', 
           'Object', 'RenderOptions', 'Scene', 'Shadow', 'Sky', 'DBInterface',
           'utils','config', 'files'] 
