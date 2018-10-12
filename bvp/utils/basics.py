"""
B.lender V.ision P.roject basic utility functions
"""

import os
import time
import subprocess
import pickle # replace with json? bson? 
import numpy as np

from ..options import config
blender_cmd = config.get('path','blender_cmd')
    
# Utility functions
def unique(seq, idfun=None): 
    """Returns only unique values in a list (with order preserved).
    (idfun can be defined to select particular values??)

    Notes
    -----
    Borrowed from https://www.peterbe.com/plog/uniqifiers-benchmark
    """
    # order preserving
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        if marker in seen: 
            seen[marker]+=1
            continue
        else:
            seen[marker] = 1
            result.append(item)         
    return result, seen


def make_blender_safe(data, Type='int'):
    """Converts numpy arrays into formats that don't break pickle/json
    
    Parameters
    ----------
    Array - numpy scalar or array
    Type - 'int' (int 32 bit) (default) or 'float' (numpy float 32bit)
    
    """
    if Type == 'int':
        Type = 'int32'
    elif Type == 'float':
        Type = 'float32'
    out = np.cast[Type](data).tolist()
    return out
    

def load_pik(pikFile):
    """Convenience function for simple loading of pickle files
    """
    with open(pikFile, 'rb') as fid:
        d = pickle.load(fid)
    return d


def save_pik(d, pikFile, protocol=2):
    """Convenience function for saving of pickle files
    Default protocol=2 for python2/3 compatibility
    """
    with open(pikFile, 'wb') as fid:
        pickle.dump(d, fid, protocol=2)


def load_exr_depth(fname):
    """load exr file that stores z (depth/distance) info"""


def load_exr_normals(fname, xflip=True, yflip=True, zflip=True, clip=True):
    """Load exr file with assumptions to map to surface normals
    
    clip : bool
        Whether to clip normals to range 0-1
    """
    try:
        import cv2
    except:
        raise ImportError('Need cv2 package to import exr files!')
    img = cv2.imread(fname, cv2.IMREAD_UNCHANGED)
    imc = img-1
    y, z, x = imc.T
    rev_x = xflip
    rev_y = yflip
    rev_z = zflip
    if rev_x: 
        x = -x
    if rev_y:
        y = -y
    if rev_z:
        z = -z
    imc = np.dstack([x.T,y.T,z.T])
    if clip:
        imc = np.clip(imc, 0, 1)
    return imc


def readEXR(fNm, isZ=True):
    """DEPRECATED. use load_exr_depth and load_exr_normals.
    Reading EXR files to numpy arrays. Principally used for Z depth files in BVP, 
    so by default this only returns the first (R of RGB) channel in an EXR image
    (R, G, B will all be the same in a Z depth image). Set isZ to False to change 
    this behavior.
    """
    import array
    import OpenEXR
    import Imath

    # Open the input file
    file = OpenEXR.InputFile(fNm)
    # Compute the size
    dw = file.header()['dataWindow']
    sz = (dw.max.x - dw.min.x + 1, dw.max.y - dw.min.y + 1)
    # Read the three color channels as 32-bit floats
    FLOAT = Imath.PixelType(Imath.PixelType.FLOAT)
    (R, G, B) = [array.array('f', file.channel(Chan, FLOAT)).tolist() for Chan in ("R", "G", "B") ]
    if isZ:
        Im = np.array(R)
        Im.shape = sz
    else:
        Im = np.array([R, G, B])
        Im.shape = [3, sz[0], sz[1]]
        Im = Im.T
    return Im


def RunScriptForAllFiles(scriptF, fNm, Is_Cluster=False, Inpts=None):
    """Run a script in all files in in some list (fNm)
    ?? Update to run on selected/all files within the library? (so, get rid of fNm input?) ??

    TO DO: allow substitutions at particular lines of the script file? This would allow different script behavior for different files...
    """
    
    if not Is_Cluster:
        for BlendFile in fNm:
            #BlendFile = os.path.join(fDir, BlendFile)
            full_cmd = [blender_cmd, '-b', BlendFile, '-P', scriptF] # Specify output? stdout? File?
            if not Inpts is None:
                full_cmd+=Inpts
            print('Calling:')
            print(full_cmd)
            subprocess.call(full_cmd)
            print('Done with %s'%BlendFile)
    else:
        nCPUs = '2'
        ClusterGrp = 'blender' # For now, GLab Slurm computers enabled to run Blender
        TempScriptDir = os.path.join(bvp.__path__[0], 'Temp') # FAAAAK fix me
        for ii, BlendFile in enumerate(fNm):
            full_cmd = [blender_cmd, '-b', BlendFile, '-P', scriptF] # Specify output? stdout? File?                
            TempScriptName = os.path.join(TempScriptDir, 'RunScriptForAllFiles_%s_%04d.sh'%(time.strftime('%Y%m%d_%m%M'), ii+1))
            with open(TempScriptName, 'wb') as fid:
                fid.write('#!/bin/sh\n')
                fid.write('#SBATCH\n')
                full_cmd = blender_cmd+' -b '+BlendFile+' -P '+BlenderPyFile
                fid.write(full_cmd)
                # Cleanup (move to .done file instead?)
                #fid.write('rm '+BlenderPyFile) 
                #fid.write('rm '+TempScriptName) 
            SlurmOut = TempScriptName.replace('.sh', '_SlurmLog.out')
            SlurmCmd = ['sbatch', '-c', nCPUs, '-p', ClusterGrp, TempScriptName, '-o', SlurmOut]
            # For call to individual cluster computer: 
            #SlurmCmd = ['sbatch', '-c', nCPUs, '-w', 'ibogaine', TempScriptName, '-o', SlurmOut]
            subprocess.call(SlurmCmd)
            print('Slurm call done for file %s'%BlendFile)


class fixedKeyDict(dict):
    """
    Class definition for a dictionary with a fixed set of keys. Works just like a normal python dictionary, 
    but the "update" method generates an error if the supplied dictionary contains a key not in the original dictionary.
    """
    def update(self, DictIn={}):
        BadField = [k for k in DictIn.keys() if not k in self.keys()]
        if BadField:
            Msg = 'Unknown field(s) in updating dictionary!\n\nBad fields: '+(len(BadField)*'"%s"\n')%tuple(BadField)
            raise AttributeError(Msg)
        else:
            for k in DictIn.keys():
                self[k] = DictIn[k]

# Move me to cluster utils
# def pySlurm(PyStr, LogDir='/auto/k1/mark/SlurmLog/', SlurmOut=None, SlurmErr=None, 
#               nCPUs='2', partition='all', memory=6000, dep=None):
#   """
#   Call a python script (formatted as one long string of commands) via slurm. Writes the string
#   to a python (.py) file, and writes a (temporary) shell script (.sh) file to call the 
#   newly-created PyFile via slurm queue.

#   Inputs: 
#       PyStr - a string that will be written in its entirety to PyFile
#       LogDir - directory to create (temporary) script files and slurm log outputs. Defaults
#           to '/tmp/' (make sure you have write permission for that directory on your machine!)
#       SlurmOut - file to which to write log
#       SlurmErr - file name to which to write error
#       nCPUs = string number of CPUs required for job
#       partition - best to leave at "all"
#       memory = numerical value, in MB, the amount of memory required for the job
#       dep = string of slurm dependenc(y/ies) for job
#   Returns: 
#       jobID = string job ID
#   """
#   import uuid, subprocess, re
#   # Get unique id string
#   u = str(uuid.uuid4()).replace('-', '')
#   PyFile = 'TempSlurm_%s.py'%u # Add datestr? 
#   PyFile = os.path.join(LogDir, PyFile)
#   with open(PyFile, 'w') as fid:
#       fid.writelines(PyStr)
#   BashFile = 'TempSlurm_%s.sh'%u
#   BashFile = os.path.join(LogDir, BashFile)
#   with open(BashFile, 'w') as fid:
#       fid.write('#!/bin/sh\n')
#       fid.write('#SBATCH\n')
#       fid.write('python '+PyFile)
#       # Cleanup (move to .done file instead?)
#       #fid.write('rm '+PyFile) 
#       #fid.write('rm '+BashFile) 
#   #SlurmOut = os.path.join(LogDir, 'Log', '%s_chunk%03d_SlurmLog_hID=%%N'%(rName, x+1))
#   if SlurmOut is None:
#       SlurmOut = os.path.join(LogDir, 'SlurmOutput_%j_hID%N.out') # Add process id -> this isn't correct syntax!
#   else:
#       SlurmOut = os.path.join(LogDir, SlurmOut)
#   #SlurmJob = "BVPrender_Chunk%03d" # Add to dict / input somehow?
#   SlurmCmd = ['sbatch', '-c', nCPUs, '-p', partition, '-o', SlurmOut, '--mem', str(memory)]
#   if dep:
#       SlurmCmd += ['-d', dep]
#   SlurmCmd += [BashFile]
#   #SlurmCmd = ['sbatch', '-c', nCPUs, '-w', 'ibogaine', BashFile, '-o', SlurmOut]
#   stdOut = subprocess.check_output(SlurmCmd)
#   jobID = re.search('(?<=Submitted batch job )[0-9]*', stdOut).group()
#   # Delete temp files??
#   return jobID
