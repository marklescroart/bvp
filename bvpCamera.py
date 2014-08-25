## NOTE! See http://western-skies.blogspot.com/2008/02/simple-complete-example-of-python.html for __getstate__() and __setstate__() methods

# Imports
import bvp,time,sys # Time and sys for debugging only!
import math as bnp
from bvp.bvpCamConstraint import bvpCamConstraint
from bvp.utils.basics import fixedKeyDict
from bvp.utils.blender import AddCameraWithTarget,GrabOnly,CreateAnim_Loc
from bvp.utils.bvpMath import vec2eulerXYZ,VectorFn,MatrixFn,atand,sind,cosd
# This won't work yet! Poop!


# Blender imports
if bvp.Is_Blender:
	import bpy
	import mathutils as bmu

class bvpCamera(object):
	'''
	Usage: bvpCamera(location=[(15,-15,5)],fixPos=[(0,0,1)],frames=[1])
	
	Class to handle placement of camera and camera fixation target for a scene. 

	Inputs:
		location : a list of (x,y,z) positions for each of n keyframes, 
			specifying camera location 
		fixPos   : a list of (x,y,z) positions for each of n keyframes, 
			specifying fixation target for camera
		frames   : a list of the keyframes at which to insert camera / 
			fixation locations. Position is linearly interpolated for all 
			frames between the keyframes. 
	If location is specified to be "None", a random location for each keyframe 
		is drawn according to the defaults in bvpCamConstraint. The same is true
		for fixPos.
	
	** Tested up to 2 keyframes as of 2012.02.20 -- more may get janky!
	
	ML 2012.02.20
	'''	
	def __init__(self,location=((17.5,-17.5,8),),fixPos=((0,0,3.5),),frames=(1,),lens=50.,clip=(.1,500.)): 
		# Default camera parameters
		Inpt = locals()
		for i in Inpt:
			if not i=='self':
				if Inpt[i]:
					setattr(self,i,Inpt[i])
		camC = bvpCamConstraint() # Initialize w/ default parameters 
		if all([x==1 for x in self.frames]):
			self.frames = (1,)
		if not location:
			self.location = camC.sampleCamPos(self.frames)
		if not fixPos:
			self.fixPos = camC.sampleFixPos(self.frames)
	@property
	def nLoc(self):
		return len(self.location)
	@property
	def nFix(self):
		return len(self.fixPos)
	@property
	def nFrames(self):
		return max(self.frames)-min(self.frames)+1
	@property
	def nKeyFrames(self):
		return len(self.frames)
	@property
	def Matrix(self):

		ImDist = 32. # Blender assumption - see above!
		FOV = 2*atand(ImDist/(2*self.lens))
		camPos = self.location
		fixPos = self.fixPos
		# Convert to vector
		cPos = VectorFn(camPos[0]) # Only do this wrt first frame for now!
		fPos = VectorFn(fixPos[0])
		# Prep for shift in L,R directions (wrt camera)
		cVec = fPos-cPos
		# Compute cTheta (Euler angles (XYZ) of camera)
		cVec = fPos-cPos
		# Get anlge of camera in world coordinates 
		cTheta = vec2eulerXYZ(cVec)
		# Blender is Right-handed
		Flag = {'Handedness':'Right'} 
		x,y,z = 0,1,2
		if Flag['Handedness'].lower() == 'left':
			# X rotation
			xRot = MatrixFn([[1.,0.,0.],
				[0.,cosd(cTheta[x]),-sind(cTheta[x])],
				[0.,sind(cTheta[x]), cosd(cTheta[x])]])
			# Y rotation
			yRot = MatrixFn([[cosd(cTheta[y]),0., sind(cTheta[y])],
				[0.,1.,0.],
				[-sind(cTheta[y]), 0., cosd(cTheta[y])]])
			# Z rotation
			zRot = MatrixFn([[cosd(cTheta[z]),-sind(cTheta[z]), 0.],
				[sind(cTheta[z]), cosd(cTheta[z]), 0.],
				[0., 0., 1.]])
		elif Flag['Handedness'].lower() == 'right':
			# X rotation
			xRot = MatrixFn([[1., 0., 0.],
				[0., cosd(cTheta[x]),sind(cTheta[x])],
				[0., -sind(cTheta[x]), cosd(cTheta[x])]])
			# Y rotation
			yRot = MatrixFn([[cosd(cTheta[y]), 0., -sind(cTheta[y])],
				[0., 1., 0.],
				[sind(cTheta[y]), 0., cosd(cTheta[y])]])
			# Z rotation
			zRot = MatrixFn([[cosd(cTheta[z]),sind(cTheta[z]), 0.],
				[-sind(cTheta[z]), cosd(cTheta[z]), 0.],
				[0., 0., 1.]])
		else: 
			raise Exception('WTF are you thinking handedness should be? Options are "Right" and "Left" only!')
		# Compute camera matrix
		CamMat = xRot * yRot * zRot
		return CamMat
	def __repr__(self):
		S = '\n~C~ bvpCamera ~C~\n'
		S += 'Camera lens: %s, clipping: %s, frames: %s\n Cam location key points: %s\n Fix location key points: %s'%(str(self.lens),
			str(self.clip),str(self.frames),str([["%.2f"%x for x in Pos] for Pos in self.location]),str([["%.2f"%x for x in Pos] for Pos in self.fixPos]))
		return S
		
	def PlaceCam(self,IDname='000',Scn=None):
		'''
		Usage: PlaceCam(Scn=None,IDname='000')

		Places camera into Blender scene (only works within Blender)

		ML 2012.01.31
		'''
		if not Scn:
			Scn = bpy.context.scene
		try:
			self.clip
		except:
			print('setting lens - this is some dumb shit!')
			self.clip=(.1,500.)
			self.lens=50.
		AddCameraWithTarget(Scn,CamName='Cam'+IDname,CamPos=self.location[0],
									FixName='CamTar'+IDname,FixPos=self.fixPos[0],Clip=self.clip,Lens=self.lens)
		# Set camera motion (multiple camera positions for diff. frames)
		Cam = bpy.data.objects['Cam'+IDname]
		Scn.camera = Cam
		Tar = bpy.data.objects['CamTar'+IDname]
		a = CreateAnim_Loc(self.location,self.frames,aName='CamMotion',hType='VECTOR')
		Cam.animation_data_create()
		Cam.animation_data.action = a
		f = CreateAnim_Loc(self.fixPos,self.frames,aName='FixMotion',hType='VECTOR')
		Tar.animation_data_create()
		Tar.animation_data.action = f

	def PlaceStereoCam(self,Disparity,Scn=None):
		'''
		Usage: CamL,CamR = Cam.PlaceStereoCam(Disparity,Scn=None)
		
		Add Stereo rendering cameras. Returns two Blender Camera objects, separated
		by "Disparity" (in Blender units). That is, left camera is at -Disparity/2, 
		right camera is at +Disparity/2 from main camera 
		
		There must be (one!) main camera in the scene first for this to work!

		ML 2012.02
		'''
		if not Scn:
			Scn = bpy.context.scene
		CamBase = [o for o in Scn.objects if o.type=='CAMERA']
		if not CamBase:
			raise Exception('No camera in scene!')
		if len(CamBase)>1:
			raise Exception('More than 1 base camera in scene!')
		CamBase = CamBase[0]
		# Parent two new cameras to the extant camera in the scene
		# Get camera rotation from vector from camera->fixation target (@first frame)
		camTheta = vec2eulerXYZ(bmu.Vector(self.fixPos[0])-bmu.Vector(self.location[0]))
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
		GrabOnly(CamBase)
		CamL.select = True
		bpy.ops.object.parent_set()

		CamRvec = bmu.Vector((Disparity/2.0,0,0))
		CamRloc = CamBase.matrix_local*CamRvec
		bpy.ops.object.camera_add(location=CamRloc,rotation=camTheta,layers=Lay)
		#bpy.ops.transform.translate(value=(Disparity/2.,0,0),constraint_axis=(True,False,False),constraint_orientation='LOCAL')
		CamR = bpy.context.object
		CamR.data = CamBase.data
		GrabOnly(CamBase)
		CamR.select = True
		bpy.ops.object.parent_set()
		return CamL,CamR
