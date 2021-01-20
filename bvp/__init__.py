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
import re
import os
import six
import uuid
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

## -- Useful functions -- ##
def _get_uuid():
    """Overkill for unique file names"""
    import uuid
    uu = str(uuid.uuid4()).replace('\n', '').replace('-', '')
    return uu
    
def _get_uuid():
    return str(uuid.uuid4()).replace('-','')


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

#def _cluster(script, blender_binary=None, **kwargs):
#    """Run cluster render job"""
#    kwargs.update(blender_binary=blender_binary,
#                  cmd=cmd)



def _cluster_deprecated(script, 
             logdir='~/slurm_log/', 
             slurm_out='bvprender_node_%N_job_%j.out',
             slurm_err=True, 
             job_name=None, 
             dep=None, 
             mem=30,
             ncpus=3,
             partition='regular',
             instant_buffer_write=True):
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
        error_handling = textwrap.dedent(
        """
        # Cleanup error files
        import socket, os
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
            #os.unlink(ef)
        """).format(slurm_err=errfile) # write error file locally
        
    # Create full script     
    python_script = header + script + error_handling
    if instant_buffer_write:
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
    if instant_buffer_write:
        # Force immediate buffer write
        slurm_script = textwrap.dedent(
        """#!/bin/bash
        #SBATCH
        stdbuf -o0 -e0 python {script_name}
        echo "Job finished! cleanup:"
        echo "removing {script_name}"
        rm {script_name}
        """).format(script_name=script_name)
    else:
        slurm_script = python_script

    # Call slurm
    clust = subprocess.Popen(slurm_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    if six.PY3:
        slurm_script = slurm_script.encode()    
    stdout, stderr = clust.communicate(slurm_script)
    if six.PY3:
        stdout = stdout.decode()
        stderr = stderr.decode()
    # Retrieve job ID
    try:
        job_id = re.search('(?<=Submitted batch job )[0-9]*',stdout).group()
    except:
        raise Exception('Slurm job submission failed! %s'%stderr)
    return job_id, stderr

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
            from vm_tools.slurm_utils import run_script as _cluster
        except:
            print("No cluster code available. Fix dependency on vm_tools.")

        # Call via cluster
        #if is_verbose:
        #    print('Calling via cluster: %s'%(' '.join(blender_cmd)))
        #jobid, stderr = _cluster_orig(blender_cmd, **kwargs)
        #if instant_buffer_write:
        print(script)
        pyscript = bvp_cluster_script.format(script=script, blend_file=blend_file, is_verbose=is_verbose, blender_binary=blender_binary)
        #else:
        #    pyscript = script
        #jobid, stderr = _cluster(pyscript, **kwargs)
        #cmd = ' '.join(blender_cmd[:-1])
        jobid = _cluster(pyscript, **kwargs)
        return jobid

__all__ = ['Action', 'Background', 'Camera', 'ObConstraint', 'CamConstraint', 'Material', 
           'Object', 'RenderOptions', 'Scene', 'Shadow', 'Sky', 'DBInterface',
           'utils','config', 'files'] 
