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

Dependencies - non python:
mongodb server (binaries avialable for *nix, OSX, and windows at )

Dependencies - python 3.X (X depends on your version of blender):
numpy 
matplotlib 
scipy
pymongo # MOVE to optional dependency...

#?# blenrig add-on scripts (available at jpbouza.com.ar/wp/downloads/blenrig/current-release/blenrig-4-0) for some models
#?# OpenEXR for handling Z depth / normal images

"""
## -- Startup stuff -- ##
from __future__ import absolute_import
__version__ = '0.2a' 

## -- Imports -- ##
import re as _re
import os as _os
import subprocess
from . import utils 
from .options import config

# Classes
# Annoyingly, this makes python 2 sad.
from .Classes.Action import Action
from .Classes.Background import Background
from .Classes.Camera import Camera
from .Classes.Constraint import  ObConstraint, CamConstraint
from .Classes.Material import Material
from .Classes.Object import Object
from .Classes.RenderOptions import RenderOptions
from .Classes.Scene import Scene
#from .Classes.SceneList import SceneList # STILL WIP
from .Classes.Shadow import Shadow
#from .Classes.Shape import Shape # STILL WIP Move to Object...?
from .Classes.Sky import Sky

from . import DB
from .DB import DBInterface

# NOTE: UPDATE LIST BELOW WHEN CLASSES ARE ALL DONE

bvp_dir = _os.path.dirname(__file__)

def set_scn(fname='bvp_test'):
    """Quickie default setup of camera + lighting for an object
    """    
    scn = Scene(camera=Camera(), sky=Sky(), fname=fname)
    scn.create()
    scn.apply_opts(render_options=RenderOptions())
    return scn

## -- Useful functions -- ##
def _getuuid():
    """Overkill for unique file names"""
    import uuid
    uu = str(uuid.uuid4()).replace('\n', '').replace('-', '')
    return uu
    
def _cluster(cmd, logfile='SlurmLog_node_%N.out', mem=15500, ncpus=2):
    """Run a job on the cluster."""
    # Command to write to file to execute
    cmd = ' '.join(cmd)
    cmd = '#!/bin/sh\n#SBATCH\n'+cmd
    # Command to 
    slurm_cmd = ['sbatch', '-c', str(ncpus), '-p', 'all', '--mem', str(mem), '-o', logfile]
    clust = subprocess.Popen(slurm_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    stdout, stderr = clust.communicate(cmd)
    jobid = _re.findall('(?<=Submitted batch job )[0-9]*', stdout)[0]
    return jobid, stderr

def blend(script, blend_file=None, is_local=True, tmpdir='/tmp/', **kwargs):
    """Run Blender with a given script.

    Parameters
    ----------
    script : string file name or script
        if `script` is a file that exists (_os.path.exists), this function will open
        an instance of Blender and run that file in Blender. If it is a string, it 
        will create a dummy temp file, write the string to it, and delete the dummy 
        file once it has run (or failed). 
    blend_file : string (optional)
        File path to Blender file
    is_local : bool
        True = run locally, False = run on cluster (if available)

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
        blend_file = _os.path.abspath(_os.path.join(bvp_dir, 'BlendFiles', 'Blank.blend'))
    # Check for existence of script
    if not _os.path.exists(script):
        # TO DO: look into doing this with pipes??
        del_tmp_script = True
        tmpf = _os.path.join(tmpdir, 'blender_temp_%s.py'%_getuuid())
        with open(tmpf, 'w') as fid:
            fid.writelines(script)
        script = tmpf
    else:
        del_tmp_script = False
    # Run 
    blender = config.get('path', 'blender_cmd') #Settings['Paths']['BlenderCmd']
    blender_cmd = [blender, '-b', blend_file, '-P', script]
    if is_local:
        # To do (?) 
        # - Use subprocess.Popen and PIPE instead of writing temp script? 
        # - check output for error?
        proc = subprocess.Popen(blender_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        if del_tmp_script and not stderr:
            _os.unlink(tmpf)
        try:
            # Change formatting of byte objects in python3
            stdout = stdout.decode()
            stderr = stderr.decode()
        except:
            pass
        # Raise exception if stderr? 
        # Or leave that to calling function? 
        # Optional?
        return stdout, stderr
        
    else:
        # Call via cluster
        if verbosity_level>3:
            print('Calling via cluster: %s'%(' '.join(blender_cmd)))
        jobid, stderr = _cluster(blender_cmd, **kwargs)
        # Check stderr for presence of errors? 
        # Raise them if they exist?
        return jobid

__all__ = ['Action', 'Background', 'Camera', 'ObConstraint', 'CamConstraint', 'Material', 
           'Object', 'RenderOptions', 'Scene', 'Shadow', 'Sky', 'DBInterface',
           'utils','config'] 
