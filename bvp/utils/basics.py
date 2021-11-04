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

def check_file_blender_version(fpath):
    """Check which version of blender saved a particular file"""
    import struct
    with open(fpath, mode='rb') as fid:
        fid.seek(7)
        bitness, endianess, major, minor = struct.unpack("sss2s", fid.read(5))
    return (int(major), int(minor))


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
