'''
.B.lender .V.ision .P.roject utils for functions to be used within Blender
(at Blender command line or in scripts run through Blender)
'''

import os
import random
import subprocess
import warnings
# import bvp seems like bad practice. 
# Only here for global (package-wide) variables, 
# e.g. verbosity_level, is_blender. REMOVE.
import bvp 
import copy
import re
import math as bnp
from .bvpMath import circ_dst # 

if bvp.Is_Blender:
	import bpy

def xyz2constr(xyz, ConstrType, originXYZ=(0., 0., 0.)):
	'''
	Convert a cartesian (xyz) location to a constraint on azimuth 
	angle (theta), elevation angle (phi) or radius (rho).
	
	originXYZ is the origin of the coordinate system (default=(0, 0, 0))

	Returns angles in degrees.
	'''
	X, Y, Z = xyz
	oX, oY, oZ = originXYZ
	X = X-oX
	Y = Y-oY
	Z = Z-oZ
	if ConstrType.lower() == 'phi':
		Out = bnp.degrees(bnp.atan2(Z, bnp.sqrt(X**2+Y**2)))
	elif ConstrType.lower() == 'theta':
		Out = bnp.degrees(bnp.atan2(Y, X))
	elif ConstrType.lower() == 'r':
		Out = (X**2+Y**2+Z**2)**.5
	return Out

def GetConstr(Grp, LockZtoFloor=True): #self, bgLibDir='/auto/k6/mark/BlenderFiles/Scenes/'):
	'''Get constraints on object & camera position for a particular background
	
	Parameters
	----------


	* Camera constraints must have "cam" in their name
	* Object constraints must have "ob" in their name

	For Cartesian (XYZ) constraints: 
	* Empties must have "XYZ" in their name
	Interprets empty cubes as minima/maxima in XYZ
	Interprets empty spheres as means/stds in XYZ (not possible to have 
	non-circular Gaussians as of 2012.02)

	For polar (rho, phi, theta) constraints:
	* Empties must have "rho", "phi", or "theta" in their name, as well as _min
	Interprets empty arrows as 

	returns obConstraint, camConstraint

	TODO: 
	Camera focal length and clipping plane should be determined by "RealWorldSize" property 
	'''

	'''
	NOTE: 
	Starting off, this seemed like an elegant idea. In practice, it has proven to be an ugly
	pain in the ass. There must be a better way to do this.
	ML 2012.02.29
	'''

	# Get camera constraints
	ConstrType = [['cam', 'fix'], ['ob']]
	thetaOffset = 270
	fn = [bvp.bvpCamConstraint, bvp.bvpObConstraint]
	Out = list()
	for cFn, cTypeL in zip(fn, ConstrType):
		cParams = [dict()]
		for cType in cTypeL:
			cParams[0]['origin'] = [0, 0, 0]
			if cType=='fix':
				dimAdd = 'fix'
			else:
				dimAdd = ''
			ConstrOb = [o for o in Grp.objects if o.type=='EMPTY' and cType in o.name.lower()] 
			# Size constraints (object only!)
			SzConstr =  [n for n in ConstrOb if 'size' in n.name.lower() and cType=='ob']
			if SzConstr:
				cParams[0]['Sz'] = [None, None, None, None]
			for sz in SzConstr:
				# obsize should be done with spheres! (min/max only for now!)
				if sz.empty_draw_type=='SPHERE' and '_min' in sz.name:
					cParams[0]['Sz'][2] = sz.scale[0]
				elif sz.empty_draw_type=='SPHERE' and '_max' in sz.name:
					cParams[0]['Sz'][3] = sz.scale[0]	
			# Cartesian position constraints (object, camera)
			XYZconstr = [n for n in ConstrOb if 'xyz' in n.name.lower()]
			if XYZconstr:
				print('Found XYZ cartesian constraints!')
				cParams = [copy.copy(cParams[0]) for r in range(len(XYZconstr))]
				
			for iE, xyz in enumerate(XYZconstr):
				for ii, dim in enumerate(['X', 'Y', 'Z']):
					cParams[iE][dimAdd+dim] = [None, None, None, None]
					if xyz.empty_draw_type=='CUBE':
						# Interpret XYZ cubes as minima / maxima
						if dim=='Z' and cType=='ob' and LockZtoFloor:
							# Lock to height of bottom of cube
							cParams[iE][dimAdd+dim][2] = xyz.location[ii]-xyz.scale[ii] # min
							cParams[iE][dimAdd+dim][3] = xyz.location[ii]-xyz.scale[ii] # max
							cParams[iE]['origin'][ii] = xyz.location[ii]-xyz.scale[ii]
						else:
							cParams[iE][dimAdd+dim][2] = xyz.location[ii]-xyz.scale[ii] # min
							cParams[iE][dimAdd+dim][3] = xyz.location[ii]+xyz.scale[ii] # max
							cParams[iE]['origin'][ii] = xyz.location[ii]
					elif xyz.empty_draw_type=='SPHERE':
						# Interpret XYZ spheres as mean / std
						cParams[iE][dimAdd+dim][0] = xyz.location[ii] # mean
						cParams[iE][dimAdd+dim][1] = xyz.scale[0] # std # NOTE! only 1 dim for STD for now!
			# Polar position constraints (object, camera)
			if cType=='fix':
				continue
				# Fixation can only have X, Y, Z constraints for now!
			pDims = ['r', 'phi', 'theta']
			# First: find origin for spherical coordinates. Should be sphere defining radius min / max:
			OriginOb = [o for o in ConstrOb if 'r_' in o.name.lower()]
			if OriginOb:
				rptOrigin = OriginOb[0].location
				if not all([o.location==rptOrigin for o in OriginOb]):
					raise Exception('Inconsistent origins for spherical coordinates!')
				#rptOrigin = tuple(rptOrigin)
				cParams['origin'] = tuple(rptOrigin)
			
			# Second: Get spherical constraints wrt that origin
			for dim in pDims:
				# Potentially problematic: IF xyz is already filled, fill nulls for all cParams in list of cParams
				for iE in range(len(cParams)):
					cParams[iE][dimAdd+dim] = [None, None, None, None]
					ob = [o for o in ConstrOb if dim in o.name.lower()]
					for o in ob:
						# interpret spheres or arrows w/ "_min" or "_max" in their name as limits
						if '_min' in o.name.lower() and o.empty_draw_type=='SINGLE_ARROW':
							cParams[iE][dimAdd+dim][2] = xyz2constr(list(o.location), dim, rptOrigin)
							if dim=='theta':
								cParams[iE][dimAdd+dim][2] = circ_dst(cParams[iE][dimAdd+dim][2]-thetaOffset, 0.)
						elif '_min' in o.name.lower() and o.empty_draw_type=='SPHERE':
							cParams[iE][dimAdd+dim][2] = o.scale[0]
						elif '_max' in o.name.lower() and o.empty_draw_type=='SINGLE_ARROW':
							cParams[iE][dimAdd+dim][3] = xyz2constr(list(o.location), dim, rptOrigin)
							if dim=='theta':
								cParams[iE][dimAdd+dim][3] = circ_dst(cParams[iE][dimAdd+dim][3]-thetaOffset, 0.)
						elif '_max' in o.name.lower() and o.empty_draw_type=='SPHERE':
							cParams[iE][dimAdd+dim][3] = o.scale[0]
						elif o.empty_draw_type=='SPHERE':
							# interpret sphere w/out "min" or "max" as mean+std
							## Interpretation of std here is a little fucked up: 
							## the visual display of the sphere will NOT correspond 
							## to the desired angle. But it should work.
							cParams[iE][dimAdd+dim][0] = xyz2constr(list(o.location), dim, rptOrigin)
							if dim=='theta':
								cParams[iE][dimAdd+dim][0] = circ_dst(cParams[iE][dimAdd+dim][0]-thetaOffset, 0.)
							cParams[iE][dimAdd+dim][1] = o.scale[0]
					if not any(cParams[iE][dimAdd+dim]):
						# If no constraints are present, simply ignore
						cParams[iE][dimAdd+dim] = None
		toAppend = [cFn(**cp) for cp in cParams]
		if len(toAppend)==1:
			toAppend = toAppend[0]
		Out.append(toAppend)
	return Out

def GetScene(*args, **kwargs):
	warnings.warn("Deprecated! use get_scene()")
	S = get_scene(*args, **kwargs)
	return S
def get_scene(num, Scn=None, Lib=None):
	"""Gathers all elements present in a blender scene into a Scene.

	Gets the background, objects, sky, shadows, and camera of the current scene
	for saving in a Scene. 
	
	Parameters
	----------
	num : int
		0-first index for scene in scene list. (Sets render path for scene to be 'Sc%04d_##'%(Num+1))

	"""
	if not Scn:
		Scn = bpy.context.scene
	if not Lib:
		Lib = bvp.bvpLibrary()
	# Initialize scene:
	S = bvp.Scene()
	# Scroll through scene component types:
	Ctype = ['objects', 'backgrounds', 'skies', 'shadows']
	# Get bvp components:
	vL = copy.copy(bvp.Verbosity_Level)
	bvp.Verbosity_Level=1 # Turn off warnings for not-found library objects
	for o in Scn.objects:
		for ct in Ctype:
			Ob = Lib.getSC(o.name, ct)
			if Ob and ct=='objects':
				if 'ARMATURE' in [x.type for x in o.dupli_group.objects]:
					Pob = [x for x in Scn.objects if o.name in x.name and 'proxy' in x.name]
					if len(Pob)>1:
						raise Exception('WTF is up with more than one armature for %s??'%Ob.name)
					elif len(Pob)==0:
						print('No pose has been set for poseable object %s'%o.name)
					elif len(Pob)==1:
						print('Please manually enter the pose for object %s Scn.Obj[%d]'%(o.name, len(S.Obj)+1))
				S.Obj.append(bvp.Object(o.name, Lib, 
					size3D=o.scale[0]*10., 
					rot3D=list(o.rotation_euler), 
					pos3D=list(o.location), 
					pose=None
					))

			elif Ob and ct=='backgrounds':
				S.BG = bvp.Background(o.name, Lib)
			elif Ob and ct=='skies':
				# Note: This will take care of lights, too
				S.Sky = bvp.Sky(o.name, Lib)
			elif Ob and ct=='shadows':
				S.Shadow = bvp.Shadow(o.name, Lib)
	bvp.Verbosity_Level=vL
	# Get camera:
	C = [c for c in bpy.context.scene.objects if c.type=='CAMERA']
	if len(C)>1 or len(C)==0:
		raise Exception('Too many/too few cameras in scene! (Found %d)'%len(C))
	C = C[0]
	CamAct = C.animation_data.action
	# lens
	S.Cam.lens = C.data.lens
	# frames
	S.Cam.frames = tuple(CamAct.frame_range)
	# location
	xC = [k for k in CamAct.fcurves if 'location'==k.data_path and k.array_index==0][0]
	yC = [k for k in CamAct.fcurves if 'location'==k.data_path and k.array_index==1][0]
	zC = [k for k in CamAct.fcurves if 'location'==k.data_path and k.array_index==2][0]
	def cLoc(fr):
		# Get x, y, z location given time
		return (xC.evaluate(fr), yC.evaluate(fr), zC.evaluate(fr))
	S.Cam.location = [cLoc(fr) for fr in CamAct.frame_range]
	# Fixation position
	Fix = [c for c in bpy.context.scene.objects if "CamTar" in c.name][0]
	# (Possible danger - check for multiple fixation points??)
	FixAct = Fix.animation_data.action
	xF = [k for k in FixAct.fcurves if 'location'==k.data_path and k.array_index==0][0]
	yF = [k for k in FixAct.fcurves if 'location'==k.data_path and k.array_index==1][0]
	zF = [k for k in FixAct.fcurves if 'location'==k.data_path and k.array_index==2][0]
	def fLoc(fr):
		# Get x, y, z location given time
		return (xF.evaluate(fr), yF.evaluate(fr), zF.evaluate(fr))
	S.Cam.fixPos = [fLoc(fr) for fr in FixAct.frame_range]
	# Last scene props: 
	S.FrameRange = tuple(CamAct.frame_range)
	S.ScnParams['frame_end'] = S.FrameRange[-1]
	S.fPath = 'Sc%04d_##'%(Num+1)
	S.Num = Num+1
	print('Don''t forget to set sky and poses!')
	return S

def CreateAnim_Loc(Pos, Frames, aName='ObjectMotion', hType='VECTOR'):
	'''
	Create an location-changing action in Blender from a list of frames and XYZ coordinates.
	Inputs:
	  Pos - list of [x, y, z] coordinates for each frames
	  Frames - list of keyframes
	  aName - name for action
	  hType - either a string or nFrames-long list of strings
	'''
	# Make hType input into a list of lists for use below
	if type(hType) is type('string'):
		hType = [hType]*len(Frames)
	for ih, h in enumerate(hType):
		if type(h) is type('string'):
			hType[ih] = [h]*2
		elif type(h) is type(['list']):
			if len(h)==1:
				hType[ih] = h*2
	a = bpy.data.actions.new(aName)
	for iXYZ in range(3):
		a.fcurves.new('location', index=iXYZ, action_group="LocRotScale")
		a.fcurves[iXYZ].extrapolation = 'LINEAR'
		for ifr, fr in enumerate(Frames):
			a.fcurves[iXYZ].keyframe_points.insert(fr, Pos[ifr][iXYZ])
			a.fcurves[iXYZ].keyframe_points[ifr].handle_left_type = hType[ifr][0]
			a.fcurves[iXYZ].keyframe_points[ifr].handle_right_type = hType[ifr][1]
		a.fcurves[iXYZ].extrapolation = 'CONSTANT'
	return a

def AddSelectedToGroup(gNm):
	'''
	Adds all selected objects to group named gNm
	'''
	Scn = bpy.context.scene
	G = bpy.data.groups[gNm]
	Ob = [o for o in Scn.objects if o.select]
	for o in Ob:
		G.objects.link(o)

def GetScenesToRender(SL):
	'''Check on which scenes within a scene list have already been rendered.

	DEPRECATED?? Overlapping in function with something else? 
	'''
	# Get number of scenes to render in one job:
	RenderGrpSize = SL.RenderOptions.BVPopts['RenderGrpSize']
	# Check on which scenes have been rendered:
	fPath, PathEnd = os.path.split(SL.RenderOptions.filepath[:-1]) # Leave out ending "/"
	# Modify PathEnd to accomodate all render types
	
	for iChk in range(1, SL.nScenes, RenderGrpSize):
		# For now: Only check images. Need to check masks, zdepth, etc...
		if not os.path.exists(os.path.join(fPath, PathEnd, 'Sc%04d_01.png'%(iChk))):
			ScnToRender = range(iChk-1, iChk+RenderGrpSize-1)
			return ScnToRender

def SetNoMemoryMode(nThreads=None, nPartsXY=6, Revert=False):
	'''
	Usage: SetNoMemoryMode(nThreads=None, nPartsXY=6, Revert=False)
	During rendering, sets mode to no undos, allows how many threads 
	to specify for rendering (default = auto detect, maybe not the 
	nicest thing to do if rendering is being done on a cluster)
	Setting Revert=True undoes the changes.
	'''
	Scn = bpy.context.scene
	if not Revert:
		bpy.context.user_preferences.edit.use_global_undo = False
		bpy.context.user_preferences.edit.undo_steps = 0
	else:
		bpy.context.user_preferences.edit.use_global_undo = True
		bpy.context.user_preferences.edit.undo_steps = 32

	# Set threading to 1 for running multiple threads on multiple machines:
	if not nThreads:
		Scn.render.threads_mode = 'AUTO'
	else: 
		Scn.render.threads_mode = 'FIXED'
		Scn.render.threads = nThreads
	# More parts to break up rendering...
	Scn.render.tile_x = nPartsXY
	Scn.render.tile_y = nPartsXY

def RemoveMeshFromMemory(MeshName):
	'''
	Removes meshes from memory. Be careful with the use of this function; it can crash Blender to have meshes removed with objects that still rely on them.
	'''
	Mesh = bpy.data.meshes[MeshName]
	Mesh.user_clear()
	bpy.data.meshes.remove(Mesh)

def RemoveActionFromMemory(ActionName):
	'''
	Removes actions from memory. Called to clear scenes between loading / rendering scenes. Be careful, this can crash Blender! 
	'''
	Act = bpy.data.actions[ActionName]
	Act.user_clear()
	bpy.data.actions.remove(Act)

def SetLayers(Ob, LayerList):
	warnings.warn('Deprecated! Use set_layers instead!')
	set_layers(Ob, LayerList)
def set_layers(Ob, LayerList):
	''' 
	Convenience function to set layers. Note that active layers affect what will be selected with bpy select_all commands. 
	Ob = blender object data structure
	LayerList = list of numbers of layers you want the object to appear on, e.g. [0, 9] (ZERO-BASED)
	'''
	if not bvp.Is_Blender:
		print("Sorry, won't run outside of Blender!")
		return
	LL = [False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]
	for L in LayerList:
		LL[L] = True
	LL = tuple(LL)
	grab_only(Ob)
	bpy.ops.object.move_to_layer(layers=LL)

def GetCursor():	
	warnings.warn("Deprecated! Use get_cursor() instead!")
	return get_cursor()
def get_cursor():
	'''Convenience function to get 3D cursor position in Blender (3D cursor marker, not mouse)

	Returns
	-------
	CursorPos : blender Vector
		X, Y, Z location of 3D cursor
	'''
	# Now this is some serious bullshit. Look where Blender hides the cursor information. Just look.
	V = [x for x in bpy.data.window_managers[0].windows[0].screen.areas if x.type=='VIEW_3D'][0]
	return V.spaces[0].cursor_location

def SetCursor(CursorPos):
	warnings.warn("Deprecated! Use set_cursor() instead!")
	set_cursor(CursorPos)
def set_cursor(CursorPos):
	'''Sets 3D cursor to specified location in VIEW_3D window

	Useful to have a function for this because there is an irritatingly
	complex data structure for the cursor position in Blender's API

	Inputs
	------
	CursorPos : list or bpy Vector
		Desired position of the cursor
	'''
	V = [x for x in bpy.data.window_managers[0].windows[0].screen.areas if x.type=='VIEW_3D'][0]
	V.spaces[0].cursor_location=CursorPos

def GrabOnly(Ob):
	warnings.warn('Deprecated! use grab_only()')
	grab_only(Ob)
def grab_only(Ob):
	'''Selects the input object `Ob` and and deselects everything else

	Inputs
	------
	Ob : bpy class object
		Object to be selected
	'''
	bpy.ops.object.select_all(action='DESELECT')
	Ob.select = True
	bpy.context.scene.objects.active = Ob

def GetMeOb(Scn=None, Do_Select=True):
	'''Returns a list of - and optionally, selects - all mesh objects in a scene
	'''
	if Scn is None:
		Scn = bpy.context.scene
	bpy.ops.object.select_all(action='DESELECT')
	MeOb = [Ob for Ob in Scn.objects if Ob.type=='MESH']
	if Do_Select:
		for Ob in MeOb:
			Ob.select = True
	return MeOb

def CheckModifiers(ObList):
	'''
	Usage: CheckModifiers(ObList)
	
	Prints a list of modifiers for each object in the list of objects "ObList"
	'''
	for o in ObList:
		m = o.modifiers
		if len(m)>0:
			print('Object %s has modifiers:\n%s'%(o.name, o.modifiers.keys()))

def CommitModifiers(ObList, mTypes=['Mirror', 'EdgeSplit']):
	'''
	Usage: CommitModifiers(ObList, mTypes=['Mirror', 'EdgeSplit'])
	
	Commits mirror / subsurf / other modifiers to meshes (use before joining meshes)
	
	Modifier types to commit are specified in "mTypes"

	NOTE: This is shitty and probably broken. Fix me.
	'''
	Flag = {'Verbose':False}
	print('Committing modifiers...')
	for o in ObList:
		if Flag['Verbose']:
			print("Checking %s"%(o.name))
		#[any (value in item for value in v) ]
		PossMods = ['Mirror', 'EdgeSplit']
		Mods = [x for x in mTypes if x in PossMods]
		for mf in Mods:
			if mf in o.modifiers.keys():
				grab_only(o)
				m = o.modifiers[mf]
				#m.show_viewport = True # Should not be necessary - we don't want to commit any un-shown modifiers
				print("Applying %s modifier to %s"%(mf, o.name))	
				bpy.ops.object.modifier_apply(modifier=m.name)
		if 'Subsurf' in o.modifiers.keys() and 'Subsurf' in mTypes:
			grab_only(o)
			m = o.modifiers['Subsurf']
			m.show_viewport = True 
			m.levels = m.render_levels
			if m.levels > 1:
				# no need for more than 2 subsurf levels...
				m.levels = 2 
			if Flag['Verbose']:
				print("Modifier is: %s"%(m.name))
				print("Applying Subsurf modifier to %s"%(o.name))
			bpy.ops.object.modifier_apply(modifier=m.name)

def getVoxelizedVertList(obj, size=10/96., smooth=1, fNm=None, showVox=False):
	'''
	Returns a list of surface point locations for a given object (or group of objects) in a regular grid. 
	Grid size is specified by "size" input.

	Inputs: 
	obj : a blender object, a blender group, or a list of objects
	size : distance between surface points. default = .2 units
	smooth : whether to smooth or not (default = 1) ## suavizado: 0 no deforma al subdividir, 1 formas organicas
	'''
	bvp.Verbosity_Level = 5
	#print('Verbosity Level: %d'%bvp.Verbosity_Level)
	import time
	t0 = time.time()
	## Get current scene:
	scn = bpy.context.scene
	# Set up no memory mode: 
	if not showVox:
		if bvp.Verbosity_Level>5:
			print('Setting no memory mode!')
		SetNoMemoryMode()
	# Recursive call to deal with groups with multiple objects:
	if isinstance(obj, bpy.types.Group):
		Ct = 0
		verts = []
		norms = []
		for o in obj.objects:
			v, n = getVoxelizedVertList(o, size=size, smooth=smooth, showVox=showVox)
			verts += v
			norms += n
		if fNm:
			if Ct==0:
				todo = 'w' # create / overwrite
			else:
				todo = 'a' # append
			with open(fNm, todo) as fid:
				for v in verts:
					fid.write('%.5f, %.5f, %.5f\n'%(v[0], v[1], v[2]))
			# Skip normal output! These are fucked anyway!
			#with open(fNm, todo) as fid:
			#	for n in norms:
			#		fid.write('%.5f, %.5f, %.5f\n'%(n[0], n[1], n[2]))
			Ct+=1
		return verts, norms
	## fix all transforms & modifiers:
	if showVox:
		obj.hide = obj.hide_render = True
	if not obj.type in ('MESH', 'CURVE', 'SURFACE'):
		# Skip any non-mesh(able) objects
		return [], []

	me = obj.to_mesh(scn, True, 'RENDER')
	me.transform(obj.matrix_world)
	dup = bpy.data.objects.new('dup', me)
	scn.objects.link(dup)
	dup.dupli_type = 'VERTS'
	scn.objects.active = dup

	## Cut long edges in successive passes 
	bpy.ops.object.mode_set()#
	ver = me.vertices
	nPasses = 50
	for ii in range(nPasses):
		fin = True
		dd = []
		for i in dup.data.edges:
			# Vector subtraction btw vertices to get vector from vertex 1 -> 2
			d = ver[i.vertices[0]].co - ver[i.vertices[1]].co
			dd.append(d.length)
			if d.length > size:
				ver[i.vertices[0]].select = True
				ver[i.vertices[1]].select = True
				fin = False
		print('max length of a side is: %.2f'%max(dd))
		print('%.2f pct of edges are longer than "size"'%(sum([q>size for q in dd])/float(len(dd))*100))
		print('%.2f pct of vertices are selected for deletion'%(sum([q.select for q in dup.data.vertices])/float(len(dup.data.vertices))))
		bpy.ops.object.editmode_toggle()
		bpy.ops.mesh.subdivide(number_cuts=1, smoothness=smooth)
		bpy.ops.mesh.select_all(action='DESELECT')
		bpy.ops.object.editmode_toggle()
		if fin: 
			if bvp.Verbosity_Level>3:
				print('took %d edge cut passes'%ii)
			break
	if not fin:
		print('took all %d edge cut passes!'%nPasses)
	## Place all vertices on a grid 
	for i in ver:
		i.co[0] -= divmod(i.co[0]+.5*size, size)[1] # X coord
		i.co[1] -= divmod(i.co[1]+.5*size, size)[1] # Y
		i.co[2] -= divmod(i.co[2]+.5*size, size)[1] # Z

	## Clean the vertex of all duplicated vertices, edges, & faces (limpiar la malla de verts duplicados caras y edges)
	bpy.ops.object.mode_set(mode='EDIT', toggle=False)
	bpy.ops.mesh.select_all(action='SELECT')
	try:
		#@$!ing stupid: kwarg name changes from "limit" to "mergedist" in 2.63. STOOPID
		bpy.ops.mesh.remove_doubles(limit=0.0001) 
	except:
		bpy.ops.mesh.remove_doubles(mergedist=0.0001) 
	bpy.ops.mesh.normals_make_consistent()
	bpy.ops.mesh.delete(type='EDGE_FACE')
	bpy.ops.object.mode_set()
	verts = [list(x.co) for x in dup.data.vertices]
	norms = [list(x.normal) for x in dup.data.vertices]
	if fNm:
		with open(fNm, 'w') as fid:
			for v in verts:
				fid.write('%.5f, %.5f, %.5f\n'%(v[0], v[1], v[2]))
		# Skip normal write-out - these are fucked anyway!
		#with open(fNm+'_Normals.txt', 'w') as fid:
		#	for n in norms:
		#		fid.write('%.5f, %.5f, %.5f\n'%(n[0], n[1], n[2]))
	if not showVox:
		scn.objects.unlink(dup)
		RemoveMeshFromMemory(me.name)
		#SetNoMemoryMode(Revert=True)
	if bvp.Verbosity_Level>4:
		t1=time.time()
		print('getVoxelizedVertList took %d mins, %.2f secs'%divmod((t1-t0), 60))
	return verts, norms

def add_img_material(name, imfile, imtype):
	"""Add a texture containing an image to Blender.

	Is this optimal? May require different materials/textures w/ different uv mappings 
	to fully paint all the shit in a scene. Better to just load an image?

	Parameters
	----------
	name : string
		Name of texture to be added. Blender image object will be called <name>, 
		Blender texture will be called <name>_tex, and Blender material will be 
		<name>_mat
	imfile : string
		full path to movie or image to add
	imtype : string
		one of : 'sequence', 'file', 'generated', 'movie'
	"""
	# Load image
	from bpy_extras.image_utils import load_image
	img = load_image(imfile)
	img.source = imtype.upper()
	# Link image to new texture 
	tex = bpy.data.textures.new(name=name+'_image', type='IMAGE')
	tex.image = img
	if imtype.upper()=='MOVIE':
		tex.image_user.use_cyclic = True
		bpy.ops.image.match_movie_length()
	# Link texture to new material
	mat = bpy.data.materials.new(name=name)
	mat.texture_slots.create(0)
	mat.texture_slots[0].texture = tex
	return mat

def set_material(proxy_ob, mat):
	"""Creates proxy objects for all sub-objects in a group & assigns a specific material to each"""
	for g in proxy_ob.dupli_group.objects:
		grab_only(proxy_ob)
		if not g.type=='MESH':
			continue
		bpy.ops.object.proxy_make(object=g.name)
		o = bpy.context.object
		for ms in o.material_slots:
			ms.material = mat
		# Get rid of proxy now that material is set
		bpy.context.scene.objects.unlink(o)

def set_scene(scene_name=None):
	"""Sets all blender screens in an open Blender session to scene_name
	"""
	if scene_name is None:
		Scn = bpy.context.scene
	else:
		SL = [s.name for s in bpy.data.scenes]
		if not scene_name in SL:
			Scn = bpy.data.scenes.new(scene_name)
		else:
			Scn = bpy.data.scenes[scene_name]
		# Set all screens to this scene
		for scr in bpy.data.screens:
			scr.scene = Scn
			
	return Scn
def apply_action(target_object, action_file, action_name):
	""""""
	pass
	# (character must already have been imported)
	# import action & armature from action_file
	# get list of matching bones
	# for all matching bones, apply (matrix? position?) of first frame

def set_up_group(ObList=None, Scn=None):
	'''
	Usage: SetUpGroup(ObList=None, Scn=None)
	
	Set a group of objects to canonical position (centered, facing forward, max dimension = 10)
	Position is defined relative to the BOTTOM, CENTER of the object (defined by the  bounding 
	box, irrespective of the object's origin) Origins are set to (0, 0, 0) as well.

	WARNING: NOT SUPER RELIABLE. There is a great deal of variability in the way in which 3D model 
	objects are stored in the myriad free 3D sites online; thus a GREAT MANY conditional statements
	would be necesary to have a reliably working function. If you want to write such a function, 
	be my guest. This works... OK. In many cases. Use with caution. ML
	
	ML 2011.10.25
	'''
	
	bvp.Verbosity_Level > 3
	if not Scn:
		Scn = bpy.context.scene # (NOTE: think about making this an input!)
	if not ObList:
		for o in Scn.objects:
			# Clear out cameras and (ungrouped) 
			if o.type in ['CAMERA', 'LAMP'] and not o.users_group:
				Scn.objects.unlink(o)
				Scn.update()
		ObList = list(Scn.objects)
	ToSet_Size = 10.0
	ToSet_Loc = (0.0, 0.0, 0.0)
	ToSet_Rot = 0.0
	# FIRST: Clear parent relationships
	p = [o for o in ObList if not o.parent and not 'ChildOf' in o.constraints.keys()]
	if len(p)>1:
		raise Exception('More than one parent in group! Now I commit Seppuku! Hi-YA!')
	else:
		p = p[0]
	np = [o for o in ObList if o.parent or 'ChildOf' in o.constraints.keys()]
	if p:
		for o in np:
			GrabOnly(o)
			bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
			if 'ChildOf' in o.constraints.keys():
				o.constraints.remove(o.constraints['ChildOf'])
	
	# SECOND: Reposition all object origins 
	(MinXYZ, MaxXYZ) = get_group_bounding_box(ObList)
	BotMid = [(MaxXYZ[0]+MinXYZ[0])/2, (MaxXYZ[1]+MinXYZ[1])/2, MinXYZ[2]]
	set_cursor(BotMid)
	
	SzXYZ = []
	for Dim in range(3):
		SzXYZ.append(MaxXYZ[Dim]-MinXYZ[Dim])
	
	if not ToSet_Size==max(SzXYZ):
		ScaleF = ToSet_Size/max(SzXYZ)
	if bvp.Verbosity_Level > 3:	
		print('resizing to %.2f; scale factor %.2f x orig. size %.2f'%(ToSet_Size, ScaleF, max(SzXYZ)))
	
	for o in ObList:
		GrabOnly(o)
		bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
		o.scale = o.scale * ScaleF
		o.location = ToSet_Loc

	Scn.update()
	# Re-parent everything
	for o in np:
		GrabOnly(p)
		o.select = True
		bpy.ops.object.parent_set()
	# Create group (if necessary) and name group
	if not ObList[0].users_group:
		for o in ObList:
			o.select=True
		bpy.ops.group.create(name=Scn.name)

def get_group_bounding_box(ob_list=None):
	'''Returns the maximum and minimum X, Y, and Z coordinates of a set of objects

	Parameters
	----------
	ob_list : list or tuple 
		list of Blender objects for which to get bounding box

	Returns
	-------
	minxyz, maxxyz : lists
		min/max x, y, z coordinates for all objects. Think about re-structuring this to be a
		more standard format for a bounding box. 
	'''
	bb_types = ['MESH', 'LATTICE', 'ARMATURE'] 
	if ob_list is None:
		ob_list = [o for o in bpy.context.scene.objects if o.select]
	BBx = list()
	BBy = list()
	BBz = list()
	for ob in ob_list: 
		bvp.utils.blender.grab_only(ob)
		if ob.type in bb_types:
			bpy.ops.object.transform_apply(rotation=True)
		for ii in range(8):
			BBx.append(ob.bound_box[ii][0] * ob.scale[0] + ob.location[0]) 
			BBy.append(ob.bound_box[ii][1] * ob.scale[1] + ob.location[1])
			BBz.append(ob.bound_box[ii][2] * ob.scale[2] + ob.location[2])
	MinXYZ = [min(BBx), min(BBy), min(BBz)]
	MaxXYZ = [max(BBx), max(BBy), max(BBz)]
	# Done
	return MinXYZ, MaxXYZ

def get_collada_action(collada_file, act_name=None, scale=1.0):
	"""Imports an armature and its associated action from a collada (.dae) file.

	Imports armature and rescales it to be standard Blender size (when the armature 
	is in a basic T pose)


	Inputs
	------
	collada_file : string filename
		file name from which to import action(s)(?). 
	act_name : string
		name for action to create. defaults to title of collada file, without .dae extension
	scale : float
		amount by which to scale 
	"""
	if act_name is None:
		act_name = os.path.split(collada_file)[1].replace('.dae', '')
	# Work in a new scene
	scn = set_scene(act_name)
	# Get list of extant actions, objects
	ext_act = [a.name for a in bpy.data.actions]
	ext_obj = [o.name for o in bpy.data.objects]
	# Import new armature
	bpy.ops.wm.collada_import(filepath=collada_file)
	# Find new objects (armature & parented meshes)
	arm_ob = [o for o in bpy.data.objects if isinstance(o.data, bpy.types.Armature) and not o.name in ext_obj]
	mesh_ob = [o for o in bpy.data.objects if isinstance(o.data, bpy.types.Mesh) and not o.name in ext_obj]
	print(mesh_ob)
	if len(arm_ob)>1:
		# Perhaps more subtlety will be required
		from pprint import pprint
		print('=========================================')
		print('Multiple armatures found for %s:'%act_name)
		print('New armatures:')
		pprint(arm_ob)
		print('=========================================')
		#raise Exception("WTF! TOO MANY NEW ARMATURES!")
		# Skip error, just go with it:
		#arm_ob = arm_ob[0]
		# Rename armature object, armature, bones
	# else:
	# 	arm_ob = arm_ob[0]
	# 	# Used to be outside if/else	
	# 	# Rename armature object, armature, bones
	# 	arm_ob.name = act_name+'_armature_ob'
	# 	arm_ob.data.name = act_name+'_armature'
	# 	for b in arm_ob.data.bones:
	# 		xx = re.search('_', b.name).start()
	# 		b.name = act_name+b.name[xx:]
	for iao, ao in enumerate(arm_ob):
		ao.name = act_name+'_%d_armature_ob'%iao
		ao.data.name = act_name+'_%d_armature'%iao
		if not ao.data.bones is None:
			for b in ao.data.bones:
				#print(b.name)
				grp = re.search('_', b.name)
				if not grp is None:
					xx = grp.start()+1
				else:
					xx = 0
				b.name = b.name[xx:]
				#print(b.name)
	# Find new action
	arm_act = [a for a in bpy.data.actions if not a.name in ext_act]
	if len(arm_act)>1:
		# Perhaps more subtlety will be required
		#raise Exception("WTF! TOO MANY NEW ACTIONS!")
		print('Keeping first action only!')
	arm_act = arm_act[0]
	arm_ob = arm_ob[0]
	# Rename new action
	arm_act.name = act_name
	# Adjust size to standard 10 units (standing straight up in rest pose)
	arm_ob.data.pose_position = "REST"
	#try:
	# Create parent relationship btw. armature and object

	set_up_group()
	#except:
	#	print('Automatic bounding box scaling failed for action;%s\nMultiplying by scale %.2f'%(act_name, scale))
	#	arm_ob.scale*=scale
	arm_ob.data.pose_position = "POSE"

###########################################################
### ---       Adding BVP elements to a scene        --- ###
###########################################################

def AddCameraWithTarget(Scn=None, CamName='CamXXX', CamPos=[25, -25, 5], FixName='CamTarXXX', FixPos=[0., 0., 0.], Lens=50., Clip=(.1, 300.)):
	'''
	Usage: AddCameraWithTarget(Scn, CamName='CamXXX', CamPos=[25, -25, 5], FixName='CamTarXXX', FixPos=[0., 0., 0.])
	Adds a camera to a scene with an empty named <FixName> 
	This is a bit quick & dirty - make sure it grabs the right "camera" data, that it's not duplicating names; also that the scene is handled well
	ML 2011.06.16
	'''
	if not Scn:
		Scn = bpy.context.scene
	# Add camera	
	bpy.ops.object.camera_add(location=CamPos)
	Cam = [o for o in Scn.objects if o.type=='CAMERA'][0] # better be only 1
	Cam.name = CamName
	# Add fixation target
	bpy.ops.object.add(type='EMPTY', location=FixPos)
	# Is this legit? Is there another way to do this??
	Fix = [o for o in Scn.objects if o.type=='EMPTY'][0]
	Fix.empty_draw_type = 'SPHERE'
	Fix.empty_draw_size = .33
	Fix.name = FixName
	# Add camera constraint
	grab_only(Cam)
	bpy.ops.object.constraint_add(type='TRACK_TO')	
	bpy.ops.object.constraint_add(type='TRACK_TO')
	Cam.data.lens = Lens
	Cam.data.clip_start = Clip[0]
	Cam.data.clip_end = Clip[1]
	Cam.constraints[0].target = Fix
	Cam.constraints[0].track_axis = 'TRACK_NEGATIVE_Z'
	Cam.constraints[0].up_axis = 'UP_Z'
	Cam.constraints[1].target = Fix
	Cam.constraints[1].track_axis = 'TRACK_NEGATIVE_Z'
	Cam.constraints[1].up_axis = 'UP_Y'	

def AddLamp(fname, scname, fPath=bvp.Settings['Paths']['LibDir']+'/Scenes/'):
	'''Add all the lamps and world settings from a given file to the current .blend file.

	Relies on ML's file structure (see ML notes on file structure in overall document)

	Parameters
	----------
	fname : string
		.blend file name (including .blend extension)
	scname : string
		name of scene within file to import lamps/world from
	fPath : string
		path to directory with all .blend files in it

	''' 
	# PERMISSIBLE TYPES OF OBJECTS TO ADD:
	AllowedTypes = ['LAMP']	# No curves for now...'CURVE', 
	# ESTABLISH SCENE TO WHICH STUFF MUST BE ADDED, STATE OF .blend FILE
	Scn = bpy.context.scene # (NOTE: think about making this an input!)
	# This is dumb too... ???
	ScnNum = len(bpy.data.scenes)
	ScnListOld = [s.name for s in bpy.data.scenes]
	# APPEND SCENE CONTAINING LAMPS TO BE ADDED
	bpy.ops.wm.link_append(
		directory=fPath+fname+"\\Scene\\", # i.e., directory WITHIN .blend file (Scenes / Objects)
		filepath="//"+fname+"\\Scene\\"+scname, # local filepath within .blend file to the scene to be imported
		filename=scname, # "filename" being the name of the data block, i.e. the name of the scene.
		link=False, 
		relative_path=False, 
		autoselect=True)
	ScnListNew = [s.name for s in bpy.data.scenes]
	nScn = [s for s in ScnListNew if not s in ScnListOld]
	nScn = bpy.data.scenes[nScn[0]]

	LampOb = [L for L in nScn.objects if (L.type in AllowedTypes)]

	LampOut = list()
	# Make parent / master object the first object in the list:	
	LampCt = 1
	for L in LampOb:
		Scn.objects.link(L)
		LampOut.append(L)
		LampCt += 1
	Scn.world = nScn.world
	Scn.update()
	bpy.data.scenes.remove(nScn)
	bpy.ops.object.select_all(action = 'DESELECT')
	for L in LampOut:
		L.select = True
	return LampOut

def add_action(action_name, fname, fPath=bvp.Settings['Paths']['LibDir']+'/Actions/'):
	'''Import an action into the current .blend file

	'''
	if action_name in bpy.data.actions:
		# Group already exists in file, for whatever reason
		print('Action already exists!')
	else:
		bpy.ops.wm.link_append(
			directory=os.path.join(fPath, fname)+"\\Action\\", # i.e., directory WITHIN .blend file (Scenes / Objects / Groups)
			filepath="//"+fname+"\\Action\\"+action_name, # local filepath within .blend file to the scene to be imported
			filename=action_name, # "filename" is not the name of the file but the name of the data block, i.e. the name of the group. This stupid naming convention is due to Blender's API.
			link=True, 
			relative_path=False, 
			autoselect=True)
	a = bpy.data.actions[action_name]
	return a

def add_group(name, fname, fPath=bvp.Settings['Paths']['LibDir']+'/Objects/', proxy=True):
	'''Add a proxy object for a Blender group to the current scene.	

	Add a group of Blender objects (all the parts of a single object, most likely) from another 
	file to the current scene. 

	Parameters
	----------
	fname : string
		.blend file name (including .blend extension)
	name : string
		Name of group to import 
	fPath : string
		Path of directory in which .blend file resides
	
	Notes
	-----
	Counts objects currently in scene and increments count.
	''' 

	if name in bpy.data.groups:
		
		# TO DO: add:
		# if proxy:
		# else:

		# Group already exists in file, for whatever reason
		print('Found group! adding new object...')
		# Add empty
		bpy.ops.object.add() 
		# Fill empty with dupli-group object of desired group
		G = bpy.context.object
		G.dupli_type = "GROUP"
		G.dupli_group = bpy.data.groups[name]
		G.name = name
	else:
		print('Did not find group! adding...')
		bpy.ops.wm.append(
			directory=os.path.join(fPath, fname)+"\\Group\\", # i.e., directory WITHIN .blend file (Scenes / Objects / Groups)
			filepath="//"+fname+"\\Group\\"+name, # local filepath within .blend file to the scene to be imported
			filename=name, # "filename" is not the name of the file but the name of the data block, i.e. the name of the group. This stupid naming convention is due to Blender's API.
			link=proxy, 
			#relative_path=False, 
			autoselect=True, 
			instance_groups=proxy)
		G = bpy.context.object
	return G
def meshify(ob):
	"""
	Create a single (water-tight?) mesh from a multi-mesh group
	"""
	raise NotImplementedError('Not yet!')
	# Select object
	grab_only(ob)
	# Prep list of new objects to be joined later
	new_obs = []
	for oo in list(ob.dupli_group.objects):
		try:
			grab_only(o)
			bpy.ops.object.proxy_make(object=oo.name)
			N = bpy.context.object
			# Apply all modifiers in stack? 

			# Re-mesh once to assure quality no shady bits in mesh
			bpy.ops.object.modifier_add(type='REMESH')
			# Must be precise or it looks awful
			N.modifiers['Remesh'].octree_depth = 8 #??
			N.modifiers['Remesh'].scale = .8 # ??
			N.modifiers['Remesh'].mode = "SHARP"
			bpy.ops.object.modifier_apply(as_type='DATA', modifier='REMESH')
			# T
			new_obs.append(N.name)
		except:
			print("Failed for %s"%oo.name)

def make_cube(name, mn, mx):
	xn, yn, zn = mn
	xx, yx, zx = mx
	
	#Define vertices, faces, edges
	verts = [(xn, yn, zn), (xn, yx, zn), (xx, yx, zn), (xx, yn, zn), (xn, yn, zx), (xn, yx, zx), (xx, yx, zx), (xx, yn, zx)]
	faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
	 
	#Define mesh and object
	mesh = bpy.data.meshes.new(name)
	ob = bpy.data.objects.new(name, mesh)
	 
	#Set location and scene of object
	#ob.location = bpy.context.scene.cursor_location
	bpy.context.scene.objects.link(ob)
	 
	#Create mesh
	mesh.from_pydata(verts, [], faces)
	mesh.update(calc_edges=True)

