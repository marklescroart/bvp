## NOTE! See http://western-skies.blogspot.com/2008/02/simple-complete-example-of-python.html for __getstate__() and __setstate__() methods

# Imports
import math as bnp
from .Constraint import CamConstraint
from ..utils.basics import fixedKeyDict
from ..utils.blender import AddCameraWithTarget,grab_only,CreateAnim_Loc
from ..utils.bvpMath import vec2eulerXYZ

# Blender imports
try:
	import bpy
	import mathutils as bmu
	is_blender = True
except ImportError:
	is_blender = False

class Camera(object):
	"""Class to handle placement of camera and camera fixation target for a scene."""
	def __init__(self,location=((17.5,-17.5,8),),fix_pos=((0,0,3.5),),frames=(1,),lens=50.,clip=(.1,500.)): 
		"""
		Parameters
		----------
		location : list of tuples
			a list of positions for each of n keyframes, each specifying camera 
			location as an (x,y,z) tuple
		fix_pos : list of tuples
			as location, but for the fixation target for the camera
		frames : list
			a list of the keyframes at which to insert camera / fixation locations. 
			Position is linearly interpolated for all frames between the keyframes. 
		
		Notes
		-----
		If location is specified to be "None", a random location for each keyframe 
			is drawn according to the defaults in CamConstraint. The same is true
			for fix_pos.
		
		Tested up to 2 keyframes as of 2012.02.20 -- more may fail
		"""
		# Default camera parameters
		Inpt = locals()
		for i in Inpt:
			if not i=='self':
				if Inpt[i]:
					setattr(self,i,Inpt[i])
		camC = CamConstraint() # Initialize w/ default parameters 
		if all([x==1 for x in self.frames]):
			self.frames = (1,)
		if not location:
			self.location = camC.sampleCamPos(self.frames)
		if not fix_pos:
			self.fix_pos = camC.sampleFixPos(self.frames)
	@property
	def n_loc(self):
		return len(self.location)
	@property
	def n_fix(self):
		return len(self.fix_pos)
	@property
	def n_frames(self):
		return max(self.frames)-min(self.frames)+1
	@property
	def n_keyframes(self):
		return len(self.frames)
	def __repr__(self):
		S = '\n~C~ Camera ~C~\n'
		S += 'Camera lens: %s, clipping: %s, frames: %s\n cam location key points: %s\n Fix location key points: %s'%(str(self.lens),
			str(self.clip),str(self.frames),str([["%.2f"%x for x in Pos] for Pos in self.location]),str([["%.2f"%x for x in Pos] for Pos in self.fix_pos]))
		return S
		
	def place(self,id_name='000',scn=None):
		'''Places camera into Blender scene (only works within Blender)

		Parameters
		----------
		id_name : string
			Name for Blender object. "cam_" is automatically prepended to the name.
		scn : Blender Scene object
			Scene to which to add the camera.
		'''
		if not scn:
			scn = bpy.context.scene
		try:
			self.clip
		except:
			print('setting lens - this is some dumb shit!')
			self.clip=(.1,500.)
			self.lens=50.
		AddCameraWithTarget(scn,CamName='cam_'+id_name,CamPos=self.location[0],
									FixName='camtarget_'+id_name,FixPos=self.fix_pos[0],Clip=self.clip,Lens=self.lens)
		# Set camera motion (multiple camera positions for diff. frames)
		cam = bpy.data.objects['cam_'+id_name]
		scn.camera = cam
		tar = bpy.data.objects['camtarget_'+id_name]
		a = CreateAnim_Loc(self.location,self.frames,aName='CamMotion',hType='VECTOR')
		cam.animation_data_create()
		cam.animation_data.action = a
		f = CreateAnim_Loc(self.fix_pos,self.frames,aName='FixMotion',hType='VECTOR')
		tar.animation_data_create()
		tar.animation_data.action = f

	def place_stereo(self,Disparity,scn=None):
		'''Add two cameras for stereo rendering.

		Returns two Blender Camera objects, separated
		by "Disparity" (in Blender units). That is, left camera is at -Disparity/2, 
		right camera is at +Disparity/2 from main camera 
		
		There must be a single main camera in the scene first for this to work!
		'''
		if not scn:
			scn = bpy.context.scene
		CamBase = [o for o in scn.objects if o.type=='CAMERA']
		if not CamBase:
			raise Exception('No camera in scene!')
		if len(CamBase)>1:
			raise Exception('More than 1 base camera in scene!')
		CamBase = CamBase[0]
		# Parent two new cameras to the extant camera in the scene
		# Get camera rotation from vector from camera->fixation target (@first frame)
		camTheta = vec2eulerXYZ(bmu.Vector(self.fix_pos[0])-bmu.Vector(self.location[0]))
		camTheta = [bnp.radians(x) for x in camTheta]
		Lay = tuple([True for x in range(20)]) # all layers
		
		CamLvec = bmu.Vector((-Disparity/2.0,0,0))
		CamLloc = CamBase.matrix_local*CamLvec
		bpy.ops.object.camera_add(location=CamLloc,rotation=camTheta,layers=Lay)
		#bpy.ops.transform.translate(value=(-Disparity/2.,0,0),constraint_axis=(True,False,False),constraint_orientation='LOCAL')
		CamL = bpy.context.object
		CamL.data = CamBase.data # Keep same camera props as main camera
		# I would prefer to use:
		# CamL.parent = CamBase # But this doesn't work for some reason. Fucks up transformation of CamL.
		grab_only(CamBase)
		CamL.select = True
		bpy.ops.object.parent_set()

		CamRvec = bmu.Vector((Disparity/2.0,0,0))
		CamRloc = CamBase.matrix_local*CamRvec
		bpy.ops.object.camera_add(location=CamRloc,rotation=camTheta,layers=Lay)
		#bpy.ops.transform.translate(value=(Disparity/2.,0,0),constraint_axis=(True,False,False),constraint_orientation='LOCAL')
		CamR = bpy.context.object
		CamR.data = CamBase.data
		grab_only(CamBase)
		CamR.select = True
		bpy.ops.object.parent_set()
		return CamL,CamR