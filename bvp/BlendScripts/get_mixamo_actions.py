"""
Import all characters and actions from DLdir

Load all actions and characters from two directories: 

<blah>/Actions/
<blah>/Characters/

Creates .blend files for each character in "Objects" 


Unzip all files first. 

Will ignore all files that unzip directly to a .dae for CHARACTERS. 

"""

import bvp
import os

dldir = '/Users/mark/Projects/Mixamo_Downloads/'
libdir = '/Users/mark/Documents/BVPlib_Mixamo/'
# For recovering downloaded characters from collada (*.dae) files
char_dir = os.path.join(dldir,'Characters')
# For recovering downloaded actions from collada (*.dae) files
actdl_dir = os.path.join(dldir,'Actions')
# For storing characters in .blend file(s) in BVP library
obj_dir = os.path.join(libdir,'Objects')
# For storing actions in .blend file(s) in BVP library
act_dir = os.path.join(libdir,'Actions')

### --- Assure that sub-directories of libdir exist --- ###
for fd in [obj_dir,act_dir]:
	if not os.path.exists(fd):
		os.mkdir(fd)
# All had better be directories, not zip files. (stand-alone *daes do not appear to work, FOR CHARACTERS)
obj = sorted([os.path.join(char_dir,f) for f in os.listdir(char_dir) if ((not '.zip' in f) and os.path.isdir(os.path.join(char_dir,f)))])

act = sorted([os.path.join(actdl_dir,f) for f in os.listdir(actdl_dir) if not '.zip' in f])

## From here: action import script
# Imports
import bpy 
import bvp
import sys
import re 

### --- add to bpy.utils.blender --- ###
	
if __name__=='__main__':
	fnm,act_name,new_fname = sys.argv[1:]
	bvp.utils.blender.get_collada_action(fnm,act_name,new_fname) 
