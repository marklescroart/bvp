"""
bvp (B.lender V.ision P.roject) is a module of functions and classes for creating visual 
stimuli within Blender. bvp functions are intended to allow creation of arbitrary scenes 
using libraries of "scene elements" (objects, backgrounds, skies/lighting setups, shadows,
and cameras). 

Scene elements are all managed by classes that wrap functionality of native Blender 
objects and store meta-data about each element (for example, the semantic category or
size of an object). Each individual scene element is stored in a archival .blend files, 
and managed by a database system based on mongodb (http://www.mongodb.com/).

Scene elements can be combined using a bvpScene class, which has methods to populate a 
given scene with objects in random locations, render the scene, and more.

All relevant information for a set of scenes is stored in the bvpSceneList 
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
version = '1.0' # Read from git repo??
Verbosity_Level = 3 # 0=none, 1=minimal, 2=informative status outputs, 3=basic debugging, ... 10=everything you never wanted to know
if Verbosity_Level>0:
	print('Loading BVP version %s'%version)

## -- Imports -- ##
import re
import os
import sys
import json
import math
import subprocess

# We can lose this now. Not necessary; blender now ships with Numpy.
try:
	import numpy as np
	Is_Numpy = True
except:
	Is_Numpy = False
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

## -- Default Settings -- ##
_SettingFile = os.path.join(os.path.dirname(__file__),'Settings','Settings.json')
Settings = json.load(open(_SettingFile,'r'))

## -- Useful functions -- ##
def _getuuid():
	"""Overkill for unique file names"""
	import uuid # Overkill for unique file name
	uu = str(uuid.uuid4()).replace('\n','').replace('-','')
	return uu
	
def _cluster(cmd,logfile='SlurmLog_node_%N.out',mem=15500,ncpus=2):
	"""Run a job on the cluster."""
	# Command to write to file to execute
	cmd = ' '.join(cmd)
	cmd = '#!/bin/sh\n#SBATCH\n'+cmd
	# Command to 
	slurm_cmd = ['sbatch','-c',str(ncpus),'-p','regular','--mem',str(mem),'-o',logfile]
	clust = subprocess.Popen(slurm_cmd,
		stdin=subprocess.PIPE,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE)
	stdout,stderr = clust.communicate(cmd)
	jobid = re.findall('(?<=Submitted batch job )[0-9]*',stdout)[0]
	return jobid,stderr

def blend(script,blend_file=None,is_local=True,tmpdir='/tmp/',**kwargs):
	"""Run Blender with a given script.

	Parameters
	----------
	script : string file name or script
		if `script` is a file that exists (os.path.exists), this function will open
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
		blend_file = os.path.join(__path__[0],'BlendFiles','Blank.blend')
	# Check for existence of script
	if not os.path.exists(script):
		# TO DO: look into doing this with pipes??
		del_tmp_script = True
		tmpf = os.path.join(tmpdir,'blender_temp_%s.py'%_getuuid())
		with open(tmpf,'w') as fid:
			fid.writelines(script)
		script = tmpf
	else:
		del_tmp_script = False
	# Run 
	blender = Settings['Paths']['BlenderCmd']
	blender_cmd = [blender,'-b',blend_file,'-P',script]
	if is_local:
		# To do (?) 
		# - Use subprocess.Popen and PIPE instead of writing temp script? 
		# - check output for error?
		proc = subprocess.Popen(blender_cmd,
			stdin=subprocess.PIPE,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE)
		stdout,stderr = proc.communicate()
		if del_tmp_script and not stderr:
			os.unlink(tmpf)
		return stdout,stderr
		# Raise exception if stderr? Or leave that to calling function? Optional?
	else:
		# Call via cluster
		if Verbosity_Level>3:
			print('Calling via cluster: %s'%(' '.join(blender_cmd)))
		jobid,stderr = _cluster(blender_cmd,**kwargs)
		# To do (?)
		# - Check standard error for boo-boos??
		return jobid

def save_settings(S=None,sFile=_SettingFile):
	'''
	Save any modification to bvp.Settings. This is PERMANENT across sessions - use with caution!
	'''
	if S is None:
		S = Settings
	json.dump(S,open(sFile,'w'),indent=2)

## -- Top-level class imports -- ##
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
