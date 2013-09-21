'''
bvp (B.lender V.ision P.roject) is a module of functions and classes for creating and 
manipulating scenes within Blender. bvp functions are intended to allow creation of 
arbitrary scenes using libraries of objects and backgrounds (and skies/lighting setups). 

Objects (class bvpObject), backgrounds (class bvpBG), skies (class bvpSky) and shadows 
(class bvpShadow) are imported from archival .blend files. A database of all available 
objects / bgs / skies / shadows is stored in the bvpLibrary class. All of these 
elements are contained in a bvpScene class, which has methods to to place the objects
in random locations, 

All relevant information for a set of stimuli (scenes) is stored in the bvpSceneList 
class, which has* methods for permanent storage* / write-out of stimulus lists to 
archival hf5 files*. 

*Still to come 2012.02.12

Dependencies:
Numpy (for use outside of Blender's python interpreter)
Pylab (for plot functions, which are not strictly necessary)
blenrig add-on scripts (available at jpbouza.com.ar/wp/downloads/blenrig/current-release/blenrig-4-0) for some models
OpenEXR for handling Z depth / normal images
'''
# Startup stuff:
version = '1.0'
Verbosity_Level = 3 # 0=none, 1=minimal, 2=informative status outputs, 3=basic debugging, ... 10=everything you never wanted to know
if Verbosity_Level>0:
	print('Loading BVP version %s'%version)
# Basic Imports:
import os
import sys
import json
import math
import numpy as np
Is_Numpy = True
# Pickle
try:
	import cPickle as pickle
except ImportError:
	if Verbosity_Level > 2: 
		print('NO CPICKLE FOR YOU!')
	import pickle
# Blender imports
try:
	import bpy
	import mathutils as bmu
	Is_Blender = True
except ImportError: 
	# In case we're working in the console outside of Blender
	Is_Blender = False
# Default Settings
_SettingFile = os.path.join(os.path.dirname(__file__),'Settings','Settings.json')
Settings = json.load(open(_SettingFile,'r'))
def SaveSettings(S=None,sFile=_SettingFile):
	'''
	Save any modification to bvp.Settings. This is PERMANENT across sessions - use with caution!
	'''
	if S is None:
		S = Settings
	json.dump(S,open(sFile,'w'),indent=2)
# Top-level class imports
for module in os.listdir(os.path.dirname(__file__)):
	if module == '__init__.py' or not module.endswith('.py'):
		continue
	if Verbosity_Level>3: 
		print('loading ' + module)
	#logger.info("Loading bvp class: %s" % module[:-3])
	temp = __import__(module[:-3], locals(), globals(), fromlist=[module[:-3]],level=1)
	locals()[module[:-3]] = temp.__getattribute__(module[:-3])
# Misc. cleanup
del module
del temp
