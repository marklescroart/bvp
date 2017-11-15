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
# Startup stuff
from __future__ import absolute_import
__version__ = '0.2a' 

# Imports
import re
import os
import uuid
import time
import subprocess
from . import utils 
from .options import config

# Classes
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

## -- Useful functions -- ##
def _getuuid():
    """Overkill for unique file names"""
    import uuid
    uu = str(uuid.uuid4()).replace('\n', '').replace('-', '')
    return uu
    
def _cluster_orig(cmd, logfile='SlurmLog_node_%N.out', mem=30000, ncpus=3):
    """Run a job on the cluster."""
    # Command to write to file to execute
    cmd = ' '.join(cmd)
    cmd = '#!/bin/sh\n#SBATCH\n'+cmd
    print(cmd)
    # Command to 
    slurm_cmd = ['sbatch', '-c', str(ncpus), '-p', 'regular', '--mem', str(mem), '-o', logfile]
    clust = subprocess.Popen(slurm_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    stdout, stderr = clust.communicate(cmd)
    print(stdout)
    print(stderr)
    jobid = re.findall('(?<=Submitted batch job )[0-9]*', stdout)[0]
    return jobid, stderr

def _get_uuid():
    return str(uuid.uuid4()).replace('-','')


## -- Cluster -- ##
bvp_cluster_script = """
import bvp
tmp_script = '''{script}'''
bvp.blend(tmp_script, is_local=True, blend_file="{blend_file}", is_verbose={is_verbose})
"""

def _cluster(script, logdir='/auto/k1/mark/SlurmLog/', slurm_out='bvp_render_node_%N_job_%j.out',
    slurm_err=True, job_name=None, dep=None, mem=30, ncpus=3, partition='regular'):
    """Run a python script on the cluster.
    
    Parameters
    ----------
    script : string
        Either a full script (as a string, probably in triple quoters) or a path to a script file
    logdir : string
        Directory in which to store slurm logs
    slurm_out : string
        File name for slurm log file. For slurm outputs, %j is job id; %N is node name
    slurm_err : string 
        File name for separate error file (if desired - if slurm_err is None, errors are 
        written to the `slurm_out` file)
    job_name : string
        Name that will appear in the slurm queue
    dep : string | None
        String job numbers for dependencies, e.g. '78823,78824,78825' (for 
        3 slurm job dependencies with those job id numbers). default=None
    mem : scalar
        Memory usage in gigabytes 
    ncpus : scalar {1 OR 3}
        Number of CPUs requested. Glab convention is to request 1 cpu per ~8GB of memory
    partition : string
        Either 'regular' or 'big' (regular = 32GB memory max, big = 64GB memory max)
    """
    if os.path.exists(script):
        with open(script,'r') as fid:
            script=fid.read()
    if slurm_err is True:
        slurm_err = 'Error_'+slurm_out
    if job_name is None:
        job_name = 'glab_script_'+time.strftime('%Y_%m_%d_%H%M',time.localtime())
    logfile = os.path.join(logdir, slurm_out)
    header = '#!/usr/bin/env python\n#SBATCH\n\n'
    if slurm_err is None:
        error_handling = ""
    else:
        errfile = os.path.join(logdir, slurm_err)
        error_handling = """
        # Cleanup error files
        import socket,os
        ef = '{slurm_err}'.replace('%j',os.getenv('SLURM_JOB_ID'))
        ef = ef.replace('%N',socket.gethostname())
        with open(ef,'r') as fid:
            output=fid.read()
        if len(output)>0:
            print('Warnings detected!')
            print(output)
            os.unlink(ef)
        else:
            print('Cleanup -> removing ' + ef)
            os.unlink(ef)
        """.format(slurm_err=errfile) # write error file locally
        
    # Create full script     
    python_script = header + script + error_handling
    script_name = os.path.join(logdir, "{}_{}.py".format(job_name, _get_uuid()))
    with open(script_name, "w") as fp:
        fp.write(python_script)

    # Create slurm command
    slurm_cmd = ['sbatch', 
                 '-c', str(ncpus),
                 '-p', partition,
                 '--mem', str(mem)+'G',
                 '-o', logfile,
                 '-J', job_name]
    if not dep is None:
        slurm_cmd += ['-d', dep]
    if not slurm_err is None:
        slurm_cmd += ['-e', errfile]

    # Force immediate buffer write
    slurm_script = """#!/bin/bash
    #SBATCH
    stdbuf -o0 -e0 python {script_name}
    echo "Job finished! cleanup:"
    echo "removing {script_name}"
    rm {script_name}
    """.format(script_name=script_name)

    # Call slurm
    clust = subprocess.Popen(slurm_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    stdout, stderr = clust.communicate(slurm_script)

    # Retrieve job ID
    try:
        job_id = re.search('(?<=Submitted batch job )[0-9]*',stdout).group()
    except:
        raise Exception('Slurm job submission failed! %s'%stderr)
    return job_id, stderr

def blend(script, blend_file=None, is_local=True, tmpdir='/tmp/', is_verbose=False, **kwargs):
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
            lines = script.readlines()
        script = '\n'.join(lines)

    # Run 
    blender = config.get('path', 'blender_cmd') #Settings['Paths']['BlenderCmd']
    blender_cmd = [blender, '-b', blend_file, '--python-expr', script]
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
        # Call via cluster
        #if is_verbose:
        #    print('Calling via cluster: %s'%(' '.join(blender_cmd)))
        #jobid, stderr = _cluster_orig(blender_cmd, **kwargs)
        pyscript = bvp_cluster_script.format(script=script, blend_file=blend_file, is_verbose=is_verbose)
        jobid, stderr = _cluster(pyscript, **kwargs)
        return jobid, stderr

__all__ = ['Action', 'Background', 'Camera', 'ObConstraint', 'CamConstraint', 'Material', 
           'Object', 'RenderOptions', 'Scene', 'Shadow', 'Sky', 'DBInterface',
           'utils','config', 'files'] 
