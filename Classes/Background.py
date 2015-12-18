## NOTE! See http://western-skies.blogspot.com/2008/02/simple-complete-example-of-python.html for __getstate__() and __setstate__() methods

# Imports.
import os
import math as bnp
from ..utils.blender import add_group
from .Constraint import ObConstraint, CamConstraint
from .Object import Object as O

try:
	import bpy
	import mathutils as bmu
	is_blender = True
except ImportError:
	is_blender = False

class Background(object):
	"""Backgrounds for scenes"""
	def __init__(self,name=None,dbi=None): # Add BGinfo? (w/ obstacles, camera constraints)
		"""Class to store (abstraction of) scene backgrounds.

		Backgrounds consist of a floor, background objects, Object/Camera constraints, possibly lights. 
		Backgrounds should be stored as scenes in one or more .blend files. File titles should be 
		"Category_BG_<BGtype>.blend", e.g. "Category_BG_Floor.blend", and all elements of the background (floor, multiple
		levels of floor, any objects) should be put into the same group (the import command used imports a group). Group 
		titles should be sensible.
		
		Parameters
		----------
		bgID: string 
			a unique identifier for the BG in question. Either a string 
				(interpreted to be the name of the BG group) or a lambda function
				(See bvpLibrary "getSceneComponent" function)
		Notes
		-----
		name is a group name, not an individual blender object. Necessary; backgrounds are multiple things.

		"""
		# Defaults ?? Create Lib from default BG file instead ??
		self.parentFile=None
		self.name=None
		self.semanticCat=None
		# Kill? These should be probability distributions over all of WordNet, which will be complex
		# enough to need their own classes. 
		self.objectSemanticCat='all'
		self.skySemanticCat='all'
		self.realWorldSize=100.0 # size of whole space in meters
		self.lens=50.
		self.n_vertices=0
		self.n_faces=0
		# Camera position constraints w/ default values
		self.camConstraints = CamConstraint()
		# Object position constraints w/ default values
		self.obConstraints = ObConstraint()
		# Obstacles (positions to avoid for objects)
		self.obstacles=None # list of bvpObjects
		# if not bgID is None:
		# 	if Lib is None:
		# 		Lib = bvp.bvpLibrary()
		# 	TmpBG = Lib.getSC(bgID,'backgrounds')
		# 	if not TmpBG is None:
		# 		# Replace default values with values from library
		# 		self.__dict__.update(TmpBG)

		# lameness:
		# Real world size (??)
		# if isinstance(self.realWorldSize,(list,tuple)):
		# 	self.realWorldSize = self.realWorldSize[0]
	def __repr__(self):
		S = '\n ~B~ Background "%s" ~B~\n'%(self.grpName)
		if self.parentFile:
			S+='Parent File: %s\n'%self.parentFile
		if self.semanticCat:
			S+=self.semanticCat[0]
			for s in self.semanticCat[1:]: S+=', %s'%s
			S+='\n'
		# Add object semantic cat? (not done in most all scenes as of 2012.09.12)
		if self.skySemanticCat:
			S+='Skies allowed: %s'%self.skySemanticCat[0]
			for s in self.skySemanticCat[1:]: S+=', %s'%s
			S+='\n'
		S+='Size: %.2f; Camera lens: %.2f'%(self.realWorldSize,self.lens)
		if self.nVertices:
			S+='%d Verts; %d Faces'%(self.nVertices,self.nFaces)
		return(S)

	def place(self,Scn=None):
		'''
		Adds background to Blender scene
		'''
		if not Scn:
			Scn = bpy.context.scene # Get current scene if input not supplied
		if self.grpName:
			# Add group of mesh object(s)
			fDir,fNm = os.path.split(self.parentFile)
			add_group(self.grpName,fNm,fDir)
		else:
			print("BG is empty!")
			
	def test_background(self,frames=(1,1),ObL=(),nObj=0,EdgeDist=0.,ObOverlap=.50):
		'''
		Tests object / camera constraints to see if they are working
		** And shadows??

		Should be grouped with other testing functions, not here. Move.
		'''
		Lib = bvp.bvpLibrary('/Users/mark/Documents/BlenderFiles/')
		Cam = bvp.bvpCamera(frames=frames)
		Sky = bvp.bvpSky('*'+self.skySemanticCat[0],Lib) # Choose a sky according to semantic category of BG ## RELIES ON ONLY ONE ENTRY FOR SKY SEMANTIC CAT! Should be most specific specifier...
		Scn = bvp.bvpScene(0,BG=self,Cam=Cam,Sky=Sky,FrameRange=frames)
		if not ObL and not nObj:
			ObL = [O('*animal',Lib,size3D=None),O('*vehicle',Lib,size3D=None),O('*appliance',Lib,size3D=None)]
			nObj = 0
		elif not ObL and nObj:
			ObL = [O(None,None,size3D=None) for x in range(nObj)]
		Scn.populate_scene(ObList=ObL,ResetCam=True,RaiseError=True,nIter=100,EdgeDist=EdgeDist,ObOverlap=ObOverlap)
		if bvp.Is_Blender:
			RO = bvp.RenderOptions()
			Scn.Create(RO)
			# Add spheres if there are blank objects:
			uv = bpy.ops.mesh.primitive_uv_sphere_add
			for o in range(nObj):
				print('Sz of obj %d = %.2f'%(o,Scn.Obj[o].size3D))
				ObSz = Scn.Obj[o].size3D/2.
				pos = bmu.Vector(Scn.Obj[o].pos3D) + bmu.Vector([0,0,ObSz])
				uv(location=pos,size=ObSz)
