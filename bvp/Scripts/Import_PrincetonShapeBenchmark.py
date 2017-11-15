"""
TODO 20140222ML_dustnav from James' database

Import and save Princeton Shape Benchmark shapes, upload and save
as separate BVP database.

Princeton shape benchmark shapes downloaded from http://shape.cs.princeton.edu/benchmark/

Currently (2014.09) assumes that all shapes have been unzipped and stored
in the same file, thus:
<parent folder>
  benchmark/ 
	db/
	  0/
	  	m0/
	  	m1/
	  	...
	  	m99/
	  1/
	  ...
	  18/

see https://docs.python.org/2/howto/regex.html
"""
## -- Imports -- ##
import numpy as np
import pymongo
import bvp
import re
import os

# Parsing functions: 
# Array pattern
pat = re.compile(r'(?<=\()[^\s\(\)][\d,\.\-]*(?=\))')
def parse_array(s):
	"""Get array via a regular expression
	"""
	arr = pat.findall(s)
	if len(arr)>1:
		arr = [[np.float(a) for a in b.split(',')] for b in arr]
	elif len(arr)==1:
		arr = [np.float(a) for a in arr[0].split(',')]
	return np.array(arr)

def parse_info(fname):
	"""Parse information in m<n>_info.txt files
	"""
	finfo = {}
	# Specific fields
	to_float = ['scale','avg_depth','average_dihedral_angle']
	to_array = ['principle_axes','principle_values','center']
	to_int = ['polygons','pid','mid']
	# Special case: Bounding box
	with open(fname,'r') as fid:
		for L in fid:
			try:
				k,v = L.strip().split(': ')
			except ValueError:
				k = L.strip().strip(':')
				v = None
			if k in to_float:
				finfo[k] = float(v)
			elif k in to_int:
				finfo[k] = int(v)
			elif k in to_array:
				finfo[k] = parse_array(v)
			else:
				finfo[k] = v
	return finfo
off_object_import = """
import bpy
import bvp
# Set scene
scn = bpy.data.scenes.new('{new_name}')
# Import object & rename
bpy.ops.import_mesh.off(filepath='{off_file}')
ob = bpy.data.objects['{old_name}']
ob.name = '{new_name}'
# prettify
bpy.ops.object.shade_smooth()
# Link to new scene? Unnecessary? 
# Establish a blender group
bvp.utils.blender.set_up_group([ob])
# Save file
bpy.ops.wm.save_mainfile(filepath='{blend_file}')
# Done!
"""
def import_psb(sdir,psd_dir,dbname='bvp_psb',port=9194):
	client = pymongo.MongoClient(port=port)
	# Check for existence of database
	if dbname in client.database_names():
		raise Exception('Database "%s" already exists! Aborting.'%dbname)
	dbi = client[dbname]
	n_shapes_per_file=100 # Better off fixed; lame numbering w/ no zero-padding, it's easier this way.
	fdirs = [os.path.join(psd_dir,'benchmark','db',str(n)) for n in range(19)]
	fdirs = [fd for fd in fdirs if os.path.isdir(fd)]
	# Check length of directory - should have 19 folders in <blah>/benchmark/db
	if len(fdirs) != 19:
		raise Exception('Princeton Shape Benchmark does not seem to be downloaded/set up properly!\n'+
			'Check help in %s!'%__file__)
	for f_ct,fd in enumerate(fdirs):
		if f_ct==0:
			continue # Done already!
		blend_file = 'PrincetonShapeBenchmark_%03d.blend'%f_ct
		blend_file = os.path.join(sdir,blend_file)
		for f in range(100):
			n = f_ct*100+f
			mm = 'm%d'%n
			mdir = os.path.join(fd,mm)
			if not os.path.exists(mdir):
				print('WTF! Skipping object: %s'%mm)
				continue
			# Get object info
			ob_dict=parse_info(os.path.join(mdir,mm+'_info.txt'))
			# Run script to insert object into Blender file
			name = 'psb%04d_%s'%(n, os.path.split(ob_dict['url'])[-1])
			# TO DO : Construct database representation
			dbob = dict(name=name,basicCat=None,semantic_category=None,
				wordnet_label=None,real_world_size=[ob_dict['scale']],
				nFaces=ob_dict['polygons'],nVertices=None,nPoses=None,
				constraints=None,verified=False,fname=blend_file)
			dbi.objects.insert([dbob])
			script = off_object_import.format(blend_file=blend_file,
				off_file=os.path.join(mdir,mm+'.off'),
				old_name=mm,new_name=name)
			if f==0:
				bvp.blend(script)
			else:
				bvp.blend(script,blend_file=blend_file)

if __name__=='__main__':
	## -- Parameters & setup -- ##
	dbname = 'bvp_psb' # B.lender V.ision P.roject P.rinceton S.hape B.enchmark
	port = 9194 # BVP default for mongodb
	n_shapes_per_file = 100 # Seems reasonable
	# Define these two as sys.argv inputs
	sdir = '/auto/k7/mark/BVP_PSB/Objects'
	psd_dir = '/auto/k6/mark/BlenderFiles/Object_Working/PrincetonDatabase_off_format/'

	## -- Bidness -- ##
	import_psb(sdir,psd_dir,dbname=dbname,port=port)


# """
# TODO 20140222ML_dustnav from James' database

# Import and save Princeton Shape Benchmark shapes, upload and save
# as separate BVP database.

# Princeton shape benchmark shapes downloaded from http://shape.cs.princeton.edu/benchmark/

# Currently (2014.09) assumes that all shapes have been unzipped and stored
# in the same file, thus:
# <parent folder>
#   benchmark/ 
# 	db/
# 	  0/
# 	  	m0/
# 	  	m1/
# 	  	...
# 	  	m99/
# 	  1/
# 	  ...
# 	  18/

# see https://docs.python.org/2/howto/regex.html
# """
# ## -- Imports -- ##
# import numpy as np
# import pymongo
# import bvp
# import re
# import os

# # Parsing functions: 
# # Array pattern
# pat = re.compile(r'(?<=\()[^\s\(\)][\d,\.\-]*(?=\))')
# def parse_array(s):
# 	"""Get array via a regular expression
# 	"""
# 	arr = pat.findall(s)
# 	if len(arr)>1:
# 		arr = [[np.float(a) for a in b.split(',')] for b in arr]
# 	elif len(arr)==1:
# 		arr = [np.float(a) for a in arr[0].split(',')]
# 	return np.array(arr)

# def parse_info(fname):
# 	"""Parse information in m<n>_info.txt files
# 	"""
# 	finfo = {}
# 	# Specific fields
# 	to_float = ['scale','avg_depth','average_dihedral_angle']
# 	to_array = ['principle_axes','principle_values','center']
# 	to_int = ['polygons','pid','mid']
# 	# Special case: Bounding box
# 	with open(fname,'r') as fid:
# 		for L in fid:
# 			try:
# 				k,v = L.strip().split(': ')
# 			except ValueError:
# 				k = L.strip().strip(':')
# 				v = None
# 			if k in to_float:
# 				finfo[k] = float(v)
# 			elif k in to_int:
# 				finfo[k] = int(v)
# 			elif k in to_array:
# 				finfo[k] = parse_array(v)
# 			else:
# 				finfo[k] = v
# 	return finfo
# off_object_import = """
# import bpy
# import bvp
# # Set scene
# scn = bvp.utils.blender.new_scene('{new_name}')
# # Import object & rename
# bpy.ops.import_mesh.off(filepath='{off_file}')
# ob = bpy.data.objects['{old_name}']
# ob.name = '{new_name}'
# # prettify
# bpy.ops.object.shade_smooth()
# # Link to new scene? Unnecessary? 
# # Establish a blender group
# bvp.utils.blender.SetUpGroup([ob])
# # Save file
# bpy.ops.wm.save_mainfile(filepath='{blend_file}')
# # Done!
# """
# def import_psb(sdir,psd_dir,dbname='bvp_psb',port=9194):
# 	client = pymongo.MongoClient(port=port)
# 	# Check for existence of database
# 	if dbname in client.database_names():
# 		raise Exception('Database "%s" already exists! Aborting.'%dbname)
# 	dbi = client[dbname]
# 	n_shapes_per_file=100 # Better off fixed; lame numbering w/ no zero-padding, it's easier this way.
# 	fdirs = [os.path.join(psd_dir,'benchmark','db',str(n)) for n in range(19)]
# 	fdirs = [fd for fd in fdirs if os.path.isdir(fd)]
# 	# Check length of directory - should have 19 folders in <blah>/benchmark/db
# 	if len(fdirs) != 19:
# 		raise Exception('Princeton Shape Benchmark does not seem to be downloaded/set up properly!\n'+
# 			'Check help in %s!'%__file__)
# 	for f_ct,fd in enumerate(fdirs):
# 		blend_file = 'PrincetonShapeBenchmark_%03d.blend'%f_ct
# 		blend_file = os.path.join(sdir,blend_file)
# 		for f in range(100):
# 			n = f_ct*100+f
# 			mm = 'm%d'%n
# 			mdir = os.path.join(fd,mm)
# 			# Get object info
# 			ob_dict=parse_info(os.path.join(mdir,mm+'_info.txt'))
# 			# Run script to insert object into Blender file
# 			name = 'psb%04d_%s'%(n, os.path.split(ob_dict['url'])[-1])
# 			# TO DO : Construct database representation
# 			dbob = dict(name=name,basicCat=None,semantic_category=None,
# 				wordnet_label=None,real_world_size=[ob_dict['scale']],
# 				nFaces=ob_dict['polygons'],nVertices=None,nPoses=None,
# 				constraints=None,verified=False,fname=blend_file)
# 			dbi.objects.insert([dbob])
# 			script = off_object_import.format(blend_file=blend_file,
# 				off_file=os.path.join(mdir,mm+'.off'),
# 				old_name=mm,new_name=name)
# 			if n==0:
# 				bvp.blend(script)
# 			else:
# 				bvp.blend(script,blend_file=blend_file)

# if __name__=='__main__':
# 	## -- Parameters & setup -- ##
# 	dbname = 'bvp_psb' # B.lender V.ision P.roject P.rinceton S.hape B.enchmark
# 	port = 9194 # BVP default for mongodb
# 	n_shapes_per_file = 100 # Seems reasonable
# 	# Define these two as sys.argv inputs
# 	sdir = '/auto/k7/mark/BVP_PSB/Objects'
# 	psd_dir = '/auto/k6/mark/BlenderFiles/Object_Working/PrincetonDatabase_off_format/'

# 	## -- Bidness -- ##
# 	import_psb(sdir,psd_dir,dbname=dbname,port=port)	
