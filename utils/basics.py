'''
.B.lender .V.ision .P.roject basic utility functions

NOTE: Some of the functions in here are throwbacks to before numpy was
well implemented in python 3. Some cleanup may be in order.

Created by ML 2011.05
Modified by ML 2013.09.18
'''

import os,random,subprocess,time,bvp
if bvp.Is_Numpy:
	np = bvp.np
	from numpy import mod,floor
# else:
if bvp.Is_Blender:
	import bpy
	import mathutils as bmu # "B lender M ath U tilities"

# Utility functions
def unique(seq, idfun=None): 
	'''
	Usage: unique(seq, idfun=None)
	
	Returns only unique values in a list (with order preserved).
	(idfun can be defined to select particular values??)
	
	Stolen from the internets 11.29.11
	'''
	# order preserving
	if idfun is None:
		def idfun(x): return x
	seen = {}
	result = []
	for item in seq:
		marker = idfun(item)
		# in old Python versions:
		# if seen.has_key(marker)
		# but in new ones:
		if marker in seen: 
			seen[marker]+=1
			continue
		else:
			seen[marker] = 1
			result.append(item)			
	return result,seen
def linspace(a,b,n=100):
	r = b-a # range
	# create 0-1 for n values
	qq = [x/float(n-1)*r+a for x in range (0,n)]
	return qq
def gridPos(n,xL=(-5,5),yL=(-5,5),zL=(0,10)):
	# Cam Position
	p = []
	for x in linspace(xL[0],xL[1],n):
		for y in linspace(yL[0],yL[1],n):
			for z in linspace(zL[0],zL[1],n):
				p.append([x,y,z])
	return p
	
def GetHostName():
	'''
	Gets local hostname

	ML 2011.11
	'''
	HostNm = subprocess.check_output(['hostname'])
	if type(HostNm) is bytes:
		HostNm = HostNm.decode('utf-8')
	HostNm = HostNm.strip('\n')
	return HostNm

def MakeBlenderSafe(Array,Type='int'):
	'''
	Usage: ListOut = MakeBlenderSafe(ArrayIn,Type='int'):
	
	Convenience function to convert numpy arrays into formats that won't piss off Blender if loaded in a pickle file.
	
	Inputs: 
	Array - numpy scalar or array
	Type - 'int' (int 32 bit) (default) or 'float' (numpy float 32bit)
	
	ML 2011.10.29
	'''
	if Type == 'int':
		Type = 'int32'
	elif Type == 'float':
		Type = 'float32'
	Out = np.cast[Type](Array).tolist()
	return Out
def RunScriptForAllFiles(scriptF,fNm,Is_Cluster=False,Inpts=None):
	'''
	Run a script in all files in in some list (fNm)
	?? Update to run on selected/all files within the library? (so, get rid of fNm input?) ??

	TO DO: allow substitutions at particular lines of the script file? This would allow different script behavior for different files...

	ML 2012.01.30
	'''
	# Get Blender instance
	Blender = bvp.Settings['Paths']['BlenderCmd'] 
	
	if not Is_Cluster:
		for BlendFile in fNm:
			#BlendFile = os.path.join(fDir,BlendFile)
			BlenderCmd = [Blender,'-b',BlendFile,'-P',scriptF] # Specify output? stdout? File?
			if not Inpts is None:
				BlenderCmd+=Inpts
			print('Calling:')
			print(BlenderCmd)
			subprocess.call(BlenderCmd)
			print('Done with %s'%BlendFile)
	else:
		nCPUs = '2'
		ClusterGrp = 'blender' # For now, GLab Slurm computers enabled to run Blender
		TempScriptDir = os.path.join(bvp.__path__[0],'Temp')
		for ii,BlendFile in enumerate(fNm):
			BlenderCmd = [Blender,'-b',BlendFile,'-P',scriptF] # Specify output? stdout? File?				
			TempScriptName = os.path.join(TempScriptDir,'RunScriptForAllFiles_%s_%04d.sh'%(time.strftime('%Y%m%d_%m%M'),ii+1))
			with open(TempScriptName,'wb') as fid:
				fid.write('#!/bin/sh\n')
				fid.write('#SBATCH\n')
				BlenderCmd = Blender+' -b '+BlendFile+' -P '+BlenderPyFile
				fid.write(BlenderCmd)
				# Cleanup (move to .done file instead?)
				#fid.write('rm '+BlenderPyFile) 
				#fid.write('rm '+TempScriptName) 
			SlurmOut = TempScriptName.replace('.sh','_SlurmLog.out')
			SlurmCmd = ['sbatch','-c',nCPUs,'-p',ClusterGrp,TempScriptName,'-o',SlurmOut]
			# For call to individual cluster computer: 
			#SlurmCmd = ['sbatch','-c',nCPUs,'-w','ibogaine',TempScriptName,'-o',SlurmOut]
			subprocess.call(SlurmCmd)
			print('Slurm call done for file %s'%BlendFile)
def loadPik(pikFile):
	'''
	Lazy function for simple loading of pickled files (stored with ".pik" extension by ML convention)
	ML 2012.02
	'''
	with open(pikFile,'rb') as fid:
		d = bvp.pickle.load(fid)
	return d
def savePik(d,pikFile,protocol=2):
	'''
	Lazy function for simple saving of pickled files (stored with ".pik" extension by ML convention)
	Default protocol=2 for compatibility
	ML 2012.02
	'''
	with open(pikFile,'wb') as fid:
		bvp.pickle.dump(d,fid,protocol=2)
def readEXR(fNm,isZ=True):
	'''
	Reading EXR files to numpy arrays. Principally used for Z depth files in BVP, 
	so by default this only returns the first (R of RGB) channel in an EXR image
	(R,G,B will all be the same in a Z depth image). Set isZ to False to change 
	this behavior.
	'''
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
	(R,G,B) = [array.array('f', file.channel(Chan, FLOAT)).tolist() for Chan in ("R", "G", "B") ]
	if isZ:
		Im = np.array(R)
		Im.shape = sz
	else:
		Im = np.array([R,G,B])
		Im.shape = [3,sz[0],sz[1]]
		Im = Im.T
	return Im

class fixedKeyDict(dict):
	'''
	Class definition for a dictionary with a fixed set of keys. Works just like a normal python dictionary, 
	but the "update" method generates an error if the supplied dictionary contains a key not in the original dictionary. 
	
	2011.10.26 ML
	'''
	def update(self,DictIn={}):
		BadField = [k for k in DictIn.keys() if not k in self.keys()]
		if BadField:
			Msg = 'Unknown field(s) in updating dictionary!\n\nBad fields: '+(len(BadField)*'"%s"\n')%tuple(BadField)
			raise AttributeError(Msg)
		else:
			for k in DictIn.keys():
				self[k] = DictIn[k]

if not bvp.Is_Blender:
	def pySlurm(PyStr,LogDir='/auto/k1/mark/SlurmLog/',SlurmOut=None,SlurmErr=None,
					nCPUs='2',partition='all',memory=6000,dep=None):
		'''
		Call a python script (formatted as one long string of commands) via slurm. Writes the string
		to a python (.py) file, and writes a (temporary) shell script (.sh) file to call the 
		newly-created PyFile via slurm queue.

		Inputs: 
			PyStr - a string that will be written in its entirety to PyFile
			LogDir - directory to create (temporary) script files and slurm log outputs. Defaults
				to '/tmp/' (make sure you have write permission for that directory on your machine!)
			SlurmOut - file to which to write log
			SlurmErr - file name to which to write error
			nCPUs = string number of CPUs required for job
			partition - best to leave at "all"
			memory = numerical value, in MB, the amount of memory required for the job
			dep = string of slurm dependenc(y/ies) for job
		Returns: 
			jobID = string job ID
		'''
		import uuid,subprocess,re
		# Get unique id string
		u = str(uuid.uuid4()).replace('-','')
		PyFile = 'TempSlurm_%s.py'%u # Add datestr? 
		PyFile = os.path.join(LogDir,PyFile)
		with open(PyFile,'w') as fid:
			fid.writelines(PyStr)
		BashFile = 'TempSlurm_%s.sh'%u
		BashFile = os.path.join(LogDir,BashFile)
		with open(BashFile,'w') as fid:
			fid.write('#!/bin/sh\n')
			fid.write('#SBATCH\n')
			fid.write('python '+PyFile)
			# Cleanup (move to .done file instead?)
			#fid.write('rm '+PyFile) 
			#fid.write('rm '+BashFile) 
		#SlurmOut = os.path.join(LogDir,'Log','%s_chunk%03d_SlurmLog_hID=%%N'%(rName,x+1))
		if SlurmOut is None:
			SlurmOut = os.path.join(LogDir,'SlurmOutput_%j_hID%N.out') # Add process id -> this isn't correct syntax!
		else:
			SlurmOut = os.path.join(LogDir,SlurmOut)
		#SlurmJob = "BVPrender_Chunk%03d" # Add to dict / input somehow?
		SlurmCmd = ['sbatch','-c',nCPUs,'-p',partition,'-o',SlurmOut,'--mem',str(memory)]
		if dep:
			SlurmCmd += ['-d',dep]
		SlurmCmd += [BashFile]
		#SlurmCmd = ['sbatch','-c',nCPUs,'-w','ibogaine',BashFile,'-o',SlurmOut]
		stdOut = subprocess.check_output(SlurmCmd)
		jobID = re.search('(?<=Submitted batch job )[0-9]*',stdOut).group()
		# Delete temp files??
		return jobID
