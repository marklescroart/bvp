## NOTE! See http://western-skies.blogspot.com/2008/02/simple-complete-example-of-python.html for __getstate__() and __setstate__() methods

# Imports
import os, bvp
from bvp.utils.basics import fixedKeyDict
from bvp.utils.blender import add_group, AddLamp, set_layers, grab_only
import math as bnp
# Numpy imports
# Blender imports
if bvp.Is_Blender:
	import bpy

class bvpSky(object):
	'''Class for skies and lighting (sun, lamps, world) for scenes

	Fields in skyParams are:
	  .parentFile - parent .blend file housing this sky
	  .grpName - group name to be imported from category file, e.g. 'BG_Sky001'
	  .semanticCat - semantic category of this sky - a list, e.g. ['dome', 'day', 'sunny']
	  .lightLoc - location of light(s) for scene.
	  .lightRot - rotation of light(s) for scene. Single lights should always be on the y=0, x<0 half-plane, w/ rotation (x, 0, 90) (w/ a negative x value)
	Usually, world parameters and lighting parameters for skies are stored in the library .blend files for each sky. However, those parameters can be optionally over-ridden by the following fields:
	  .WorldParams - dictionary specifying Blender world parameters, with fields (default values shown):
				'horizon_color':(.55, .65, .75)
				'use_sky_paper':False
				'use_sky_blend':False
				'use_sky_real':False
	  .WorldLighting - dictionary specifying lighting parameters, with fields:
				'use_ambient_occlusion':True
				'ao_factor':1.0
				'use_indirect_light':True
				'indirect_factor':1.0
				'use_environment_light':True
				'environment_energy':0.7
	To over-ride whatever has been imported from sky files with above values, set this to True:
	  .OverrideWorldProps = False 
	
	'''
	def __init__(self, skyID=None, Lib=None):
		'''
		Initialization.
		'''
		# Defaults ?? Create Lib from default BG file instead ??
		self.parentFile=None
		self.grpName=None
		self.semanticCat=None
		self.lightLoc=[[0., 0., 35.]] # lamp location (default = straight up)
		self.lightRot=[[bnp.degrees(x) for x in (0.6503279805183411, 0.055217113345861435, 1.8663908243179321)]]
		self.lightType='SUN' # Type of Blender lamp that is in this sky/light setup. 
		self.realWorldSize=100.0 # size of whole space lit (in meters)
		self.nVertices=0
		self.nFaces=0
		self.OverrideWorldProps = False # Over-ride properties imported from sky files with WorldParams, WorldLighting below
		# Special cases of skyID:
		SkipUpdate = False
		try:
			IsStr = isinstance(skyID, (str, unicode))
		except NameError:
			IsStr = isinstance(skyID, str)
		if not skyID is None and IsStr:
			if skyID.lower() in ['none', '*none']:
				self.lightType='none'
				SkipUpdate = True
			elif skyID.lower() in ['indoorlights', '*indoorlights']:
				self.lightType='indoorLights'
				self.lightLoc = [[0, 0, 25]]
				self.lightRot = [[0, 0, 0]]
				SkipUpdate = True
			elif skyID.lower() in ['all', '*all']:
				# pick a random sky
				skyID=lambda x: x
		elif not skyID is None and isinstance(skyID, (list, tuple)):
			# note 2012.12.30: not clear why this elif is here; why should skyID be a list/tuple??
			if 'none' in skyID:
				self.lightType='none'
				SkipUpdate = True
			elif 'indoorlights' in [sID.lower() for sID in skyID]:
				self.lightType='indoorLights'
				self.lightLoc = [[0, 0, 25]]
				self.lightRot = [[0, 0, 0]]
				SkipUpdate = True
			elif 'all' in [sID.lower() for sID in skyID]:
				# pick a random sky
				skyID=lambda x: x
				
		if not Lib is None and not SkipUpdate:
			TmpSky = Lib.getSC(skyID, 'skies')
			# Replace default values with values from library
			self.__dict__.update(TmpSky)
		if isinstance(self.realWorldSize, (list, tuple)):
			self.realWorldSize = self.realWorldSize[0]

		if self.grpName is None:
			if self.lightType.lower()=='sun':
				self.OverrideWorldProps = True
				self.WorldParams = fixedKeyDict({
						# Sky color
						'horizon_color':(.55, .65, .75), # bluish
						'use_sky_paper':False, 
						'use_sky_blend':False, 
						'use_sky_real':False, 
						})
						# Stars? Mist? 
				self.WorldLighting = fixedKeyDict({
						# World lighting settings (defaults for no bg, no sky, no lights, just blank scene + camera)
						# AO
						'use_ambient_occlusion':True, 
						'ao_factor':.3, 
						# Indirect lighting
						'use_indirect_light':False, # Nice, but expensive
						'indirect_factor':0.5, 
						'indirect_bounces':2, 
						'gather_method':'APPROXIMATE', 
						# Environment lighting
						'use_environment_light':True, 
						'environment_energy':0.55, 
						'environment_color':'SKY_COLOR', 
						})
			elif self.lightType.lower()=='indoorlights':
				# Light settings for indoor lighting
				# Don't add any lamps?
				self.OverrideWorldProps = True
				self.WorldParams = fixedKeyDict({
						# Sky color
						'horizon_color':(.6, .55, .43), #brownish
						'use_sky_paper':False, 
						'use_sky_blend':False, 
						'use_sky_real':False, 
						})
						# Stars? Mist? 
				self.WorldLighting = fixedKeyDict({
						# World lighting settings (defaults for no bg, no sky, no lights, just blank scene + camera)
						# AO
						'use_ambient_occlusion':True, 
						'ao_factor':.3, 
						# Indirect lighting
						'use_indirect_light':False, # Nice, but expensive
						'indirect_factor':0.5, 
						'indirect_bounces':2, 
						'gather_method':'APPROXIMATE', 
						# Environment lighting
						'use_environment_light':True, 
						'environment_energy':0.4, # Most have other light sources in the scene
						'environment_color':'SKY_COLOR', 
						})
			elif self.lightType.lower()=='none':
				# No lights, just environment settings
				self.OverrideWorldProps = True
				self.WorldParams = fixedKeyDict({
						# Sky color
						'horizon_color':(.5, .5, .5), #flat gray
						'use_sky_paper':False, 
						'use_sky_blend':False, 
						'use_sky_real':False, 
						})
						# Stars? Mist? 
				self.WorldLighting = fixedKeyDict({
						# World lighting settings (defaults for no bg, no sky, no lights, just blank scene + camera)
						# AO
						'use_ambient_occlusion':True, 
						'ao_factor':.3, 
						# Indirect lighting
						'use_indirect_light':False, # Nice, but expensive
						'indirect_factor':0.5, 
						'indirect_bounces':2, 
						'gather_method':'APPROXIMATE', 
						# Environment lighting
						'use_environment_light':True, 
						'environment_energy':0.5, 
						'environment_color':'SKY_COLOR', 
						})

	def Place(self, num=0, Scn=None, Scale=None):
		'''
		Adds sky to Blender scene
		'''
		LampOb = []
		if not Scn:
			Scn = bpy.context.scene # Get current scene if input not supplied
		if not self.grpName is None:
			# Add proxies of mesh objects
			fDir, fNm = os.path.split(self.parentFile)
			SkyOb = add_group(self.grpName, fNm, fDir)
			if not Scale is None:
				print('Resizing...')
				sz = Scale/self.realWorldSize # most skies are 100x100 in area
				bpy.ops.transform.resize(value=(sz, sz, sz))
			for o in SkyOb.dupli_group.objects:
				grab_only(SkyOb)
				bpy.ops.object.proxy_make(object=o.name) #, object=SkyOb.name, type=o.name)
				NewOb = bpy.context.object
				if NewOb.type=='MESH': # This better be the sky dome
					set_layers(NewOb, [9])
					NewOb.name=SkyOb.name
					NewOb.pass_index = 100
				else:
					# Save lamp objects for more below
					LampOb.append(NewOb)
			# Get rid of linked group now that mesh objects and lamps are imported
			bpy.context.scene.objects.unlink(SkyOb)
			# Rename lamps
			for l in LampOb:
				l.name = 'BG_Lamp%04d'%(num)
			# Add world
			W = self.AddWorld() # Relies on world being named same thing as sky group... Could be problematic, but anything else is a worse pain
			Scn.world.name = 's%04dworld'%(num) 
			
			Scn.update()
			
		else:
			# Add simple lamp and set OverrideWorldProps to True
			## MOVE ALL THIS TO SETTINGS??
			if self.lightType.lower()=='sun':
				# Clear other lamps
				for L in bpy.context.scene.objects: 
					if L.type=='LAMP':
						bpy.context.scene.objects.unlink(L)
				bpy.ops.object.lamp_add(type='SUN')
				L = [lo for lo in bpy.context.scene.objects if lo.type=="LAMP"]
				O = L[0] #grab_only(L[0]) 
				O.rotation_euler = (0.6503279805183411, 0.055217113345861435, 1.8663908243179321)
				O.location = (0., 0., 35.) # Doesn't actually matter since it's a sun lamp
		# (Other possibilities for lightType taken care of in initialization)

		if not Scn.world:
			W = bpy.data.worlds.new('s%04dworld'%num)
			Scn.world = W

		if self.OverrideWorldProps:
			for k in self.WorldParams.keys():
				setattr(Scn.world, k, self.WorldParams[k])
			for j in self.WorldLighting.keys():
				setattr(Scn.world.light_settings, j, self.WorldLighting[j])
		# (TEMP?) over-ride of AO (for more efficient renders):
		Scn.world.light_settings.gather_method = 'RAYTRACE'
		Scn.world.light_settings.use_ambient_occlusion = False 
		Scn.update()
		# END (temp?) over-ride of AO
		
	def AddWorld(self, Scn=None):
		'''
		Usage: AddWorld(self, bvpScn, Scn=None):
		
		Adds a specified world from a specified file, as in add_group()

		NOTE! Currently (2012.02) worlds and sky groups must have the same (unique) name!
		'''
		if not Scn:
			Scn = bpy.context.scene
		fPath, fName = os.path.split(self.parentFile)
		WorldName = self.grpName
		bpy.ops.wm.link_append(
			directory=os.path.join(fPath, fName)+"\\World\\", # i.e., directory WITHIN .blend file (Scenes / Objects / World / etc)
			filepath="//"+fName+"\\World\\"+WorldName, # local filepath within .blend file to the world to be imported
			filename=WorldName, # "filename" being the name of the data block, i.e. the name of the world.
			link=False, 
			relative_path=False, 
			autoselect=True)
		Scn.world = bpy.data.worlds[self.grpName]

	def __repr__(self):
		S = '\n ~S~ bvpSky "%s" ~S~\n'%(self.grpName)
		if self.parentFile:
			S+='Parent File: %s\n'%self.parentFile
		if self.semanticCat:
			S+=self.semanticCat[0]
			for s in self.semanticCat[1:]: S+=', %s'%s
			S+='\n'
		if self.nVertices:
			S+='%d Verts; %d Faces'%(self.nVertices, self.nFaces)
		return(S)
