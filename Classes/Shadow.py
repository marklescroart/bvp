## NOTE! See http://western-skies.blogspot.com/2008/02/simple-complete-example-of-python.html for __getstate__() and __setstate__() methods

# Imports.
import os,types,bvp
from bvp.utils.blender import add_group
#import logger
# Blender imports
if bvp.Is_Blender:
	import bpy

# Class def
class bvpShadow(object):
	'''
	Class for abstract blender scene backgrounds
	'''
	def __init__(self,shID=None,Lib=None): 
		'''
		Usage: shadow = bvpBG(shID=None,Lib=None)

		Class to store shadows 
				
		As of 2011.10.19, there is only one shadow category (noise). May add more...
		Buildings
		Natural
		Inside
		etc.
		
		ML 2012.01.23
		'''
		# Defaults ?? Create Lib from default BG file instead ??
		self.parentFile=None
		self.grpName=None
		self.semanticCat=None
		self.realWorldSize=100.0 # size of whole space in meters
		self.nVertices=0
		self.nFaces=0

		if Lib:
			TmpSky = Lib.getSC(shID,'shadows')
			# Replace default values with values from library
			self.__dict__.update(TmpSky)
	def __repr__(self):
		S = '\n ~S~ bvpShadow "%s" ~S~\n'%self.grpName
		return S
		
	def PlaceShadow(self,Scn=None,Scale=None):
		'''
		Usage: PlaceShadow(Scn=None)

		Adds shadow object to Blender scene

		'''
		if not Scn:
			Scn = bpy.context.scene # Get current scene if input not supplied
		if self.grpName:
			# Add group of mesh object(s)
			fDir,fNm = os.path.split(self.parentFile)
			ShOb = add_group(self.grpName,fNm,fDir)
		if not Scale is None:
			if bvp.Verbosity_Level >3:
				print('Resizing shadow...')
			sz = Scale/self.realWorldSize[0] # most skies are 100x100 in area
			bpy.ops.transform.resize(value=(sz,sz,sz))
		else:
			if bvp.Verbosity_Level > 3:
				print("Shadow is empty!")
			