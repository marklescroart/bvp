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


