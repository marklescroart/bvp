'''
BVP Math utilities

Designed to work with either numpy or Blender's mathutils

NOTE: Lots of this is out-dated, now we're running with numpy + other 3rd party packages.
CLEAN ME UP!

ML 2012.01.31
'''

import bvp,random
import math as bnp
from bvp.utils.basics import MakeBlenderSafe
# Alternative runtime environments
if bvp.Is_Numpy:
	import numpy as np
	MatrixFn = np.matrix
	def VectorFn(a):
		b = np.array(a)
		b.shape = (len(a),1)
		return b
	GetInverse = np.linalg.pinv
	def lst(a):
		a = np.array(a)
		return list(a.flatten())
	pi = np.pi
else:
	# Better be working within Blender...
	import mathutils as bmu
	from math import pi
	MatrixFn = bmu.Matrix
	VectorFn = bmu.Vector
	GetInverse = lambda x: x.inverted()
	lst = list

# Math functions
def listMean(a):
	'''
	mean function for lists
	'''
	return sum(a)/float(len(a))

def circ_avg(a,b):
	'''
	Circular average of two values (in DEGREES)
	'''
	Tmp = bnp.e**(1j*a/180.*bnp.pi)+bnp.e**(1j*b/180.*bnp.pi)
	Mean = bnp.atan2(Tmp.imag,Tmp.real)/bnp.pi*180.
	return Mean

def circ_dst(a,b):
	'''
	Angle between two angles
	'''
	cPh = bnp.e**(1j*a/180*bnp.pi) / bnp.e**(1j*b/180*bnp.pi)
	cDst = bnp.degrees(bnp.atan2(cPh.imag,cPh.real))
	return cDst

def vecDist(a,b):
	if bvp.Is_Numpy:
		d = np.linalg.norm(np.array(a)-np.array(b))
		d = MakeBlenderSafe(d,'float')
	else:
		d = (bmu.Vector(a)-bmu.Vector(b)).length
	return d

def cosd(theta):
	theta = bnp.radians(theta)
	return bnp.cos(theta)

def sind(theta):
	theta = bnp.radians(theta)
	return bnp.sin(theta)

def tand(theta):
	theta = bnp.radians(theta)
	return bnp.tan(theta)

def atand(theta):
	return bnp.degrees(bnp.atan(theta))

def sph2cart(r,az,elev):
	'''
	Usage: x,y,z = sph2cart(r,az,elev)
	Or:    x,y,z = sph2cart(r,theta,phi)
	Converts spherical to cartesian coordinates. Azimuth and elevation angles in degrees.

	ML 2011.10.13
	'''
	z = r * sind(elev);
	rcoselev = r * cosd(elev);
	x = rcoselev * cosd(az);
	y = rcoselev * sind(az);
	return x,y,z

def cart2sph(x,y,z):
	'''
	Usage: r,theta,phi = cart2sph(x,y,z)
	Convert cartesian to spherical coordinates (degrees)
	'''
	r = (x**2+y**2+z**2)**.5
	theta = bnp.degrees(bnp.atan2(y,x))
	phi = bnp.degrees(bnp.asin(z/r))
	return r,theta,phi

def AddLists(a,b):
	'''
	element-wise addition of two lists. Uses either numpy or Blender's mathutils
	'''
	if len(b) != len(a):
		if len(a[0]==len(b)):
			b = [b]*len(a)
		elif len(b[0]==len(a)):
			a = [a]*len(b)
		else:
			raise Exception('Incompatible list sizes!')
	#if bvp.Is_Numpy:
	c = [(np.array(aa)+np.array(bb)).tolist() for aa,bb in zip(a,b)]
	#elif bvp.Is_Blender:
	#	c = [list(bmu.Vector(aa)+bmu.Vector(bb)) for aa,bb in zip(a,b)]
	return c

def CirclePos(radius,nPos,x_center=0,y_center=0,Direction='BotCCW'):
		'''
		Usage: Pos = mlCirclePos(radius,nPos [,x_center,y_center,Direction])
		
		Returns coordinates for [nPos] points around a circle of radius [radius], 
		centered on [x_center,y_center]. Coordinates returned in [Pos], an nPos 
		by 2 matrix of [x,y] values. 
		
		Inputs: radius = Radius of the circle. Either one value or nPos values.
		          nPos = number of positions around the circle
		      x_center = duh (defaults to 512)
		      y_center = duh (defaults to 384)
		     Direction = String specifying direction of points around circle - 
						either 'BotCCW' (botom Counter-Clockwise), 'BotCW'
						(bottom Clockwise), 'TopCCW', or 'TopCW' (Defaults to
						'BotCCW')
						* Note that Right and Left CW or CCW can be obtained
						by switching x and y
		
		See function text at the bottom for example usage.
		
		Created by ML on ??/??/2007
		Adapted for python by ML on 06/01/2011
		No-Numpy version by ML on 2012.02.01
		'''
		
		if (isinstance(radius,type(list())) and len(radius)==1):
			radius = radius*nPos #np.tile(radius,(nPos,1))
		elif isinstance(radius,(type(1.0),type(1))):
			radius = [radius]*nPos
		
		#iPos = 0;
		Deg = 360./nPos
		Ticks = [ii*Deg for ii in range(nPos)]
		#Pos = np.nan * np.ones((nPos,2))
		PosX = []
		PosY = []
		for iPos,tt in enumerate(Ticks):
			PosX.append(radius[iPos]*sind(tt) + x_center)
			PosY.append(-radius[iPos]*cosd(tt) + y_center)
			#iPos += 1
		del tt
		del iPos
		
		if Direction.upper()=='BOTCCW':
			0; # Do nothing - it's set this way anyway.
		elif Direction.upper()=='BOTCW':
			# reverse order of Y values
			PosY.reverse()
		elif Direction.upper()=='TOPCCW':
			# Keep top position (Pos[1,:]), and invert the rest of the Y values
			pxRev = copy.copy(PosX)
			pxRev.reverse()			
			pyRev = copy.copy(PosY)
			pyRev.reverse()

			PosX = [PosX[0]]+pxRev[:-1]
			PosY = [PosY[0]]+pyRev[:-1]
			'''
			Pos = np.concatenate(
				(Pos[0,:],Pos[::-1,:]),
				axis=0)
			Pos[:,1] = -(Pos[:,1]-y_center) + y_center;
			'''
		elif Direction.upper()=='TOPCW':
			Pos[:,1] = -(Pos[:,2]-y_center) + y_center;
			#Pos(:,2) = -Pos(:,2);
		Pos = [[x,y] for x,y in zip(PosX,PosY)]
		return Pos

def PerspectiveProj(bvpObj,bvpCam,ImSz=(1.,1.)): 
	'''
	Usage: imPos_Top,imPos_Bot,imPos_L,imPos_R = PerspectiveProj(bvpObj,bvpCam,ImSz=(1.,1.))
	
	Gives image coordinates of an object (Bottom,Top,L,R) given the 3D position of the object and a camera.
	Assumes that the origin of the object is at the center of its base (BVP convention!)
	
	UNIVERSAL version...		
	
	Parameters
	----------
	bvpObj : bvpObject class
		Should contain object position (x,y,z) and size
	bvpCam : bvpCamera class
		Should contain a list of (x,y,z) camera and fixation positions for n frames
	ImSz : tuple or list
		Image size (e.g. [500,500]) default = (1.,1.) (for pct of image computation)
	

	Created by ML 2011.10.06
	'''

	"""
	NOTE: 
	Note: Blender seems to convert focal length in mm to FOV by assuming a particular
	(horizontal/diagonal) distance, in mm, across an image. This is not
	exactly correct, i.e. the rendering effects will not necessarily match
	with real rectilinear lenses, etc... See
	http://www.metrocast.net/~chipartist/BlensesSite/index.html
	for more discussion.

	Test run:
	fL  = [10 15 25 35 50 100 182.881]; # different settings for focal length in Blender
	FOV = [115.989 93.695 65.232 49.134 35.489 18.181 10] # corresponding values for FOV (computed by Blender)
	ImDist = 32.; # 
	FOVcomputed = 2*atand(ImDist./(2*fL)); # Focal length equation, from
	# http://kmp.bdimitrov.de/technology/fov.html and http://www.bobatkins.com/photography/technical/field_of_view.html
	plot(fL,FOV,'bo',fL,FOVcomputed,'r')
	
	"""
	ImDist = 32. # Blender assumption - see above!
	FOV = 2*atand(ImDist/(2*bvpCam.lens))

	objPos = bvpObj.pos3D
	camPos = bvpCam.location
	fixPos = bvpCam.fixPos
	# Convert to vector
	cPos = VectorFn(camPos[0]) # Only do this wrt first frame for now!
	#cPos.shape = (3,1) 
	fPos = VectorFn(fixPos[0])
	#fPos.shape = (3,1)
	oPos = VectorFn(objPos) #np.array(bvpObj.pos3D) 
	# Prep for shift in L,R directions (wrt camera)
	cVec = fPos-cPos
	
	# Made consistent w/ non-numpy version 2012.10.23
	##cVec.normalize() # bmu (mathutils) function!!
	#Lshift = VectorFn([-cVec[1],cVec[0],0])*bvpObj.size3D/2.
	#Rshift = VectorFn([cVec[1],-cVec[0],0])*bvpObj.size3D/2.
	#
	## Get other bounds...
	#oPos_Top = oPos+VectorFn([0,0,bvpObj.size3D])
	#oPos_L = oPos+Lshift
	#oPos_R = oPos+Rshift
	
	# Get other bounds...
	oPos_Top = oPos+VectorFn([0,0,bvpObj.size3D])
	oPos_L = oPos-VectorFn([bvpObj.size3D/2.,0,0])
	oPos_R = oPos+VectorFn([bvpObj.size3D/2.,0,0])

	#oPos.shape = (3,1)
	# Compute cTheta (Euler angles (XYZ) of camera)
	cVec = fPos-cPos
	#u,s,v = np.linalg.svd(cVec)
	# Get anlge of camera in world coordinates 
	cTheta = vec2eulerXYZ(cVec)
	#print(cTheta)
	Flag = {'Handedness':'Right'} # Blender is Right-handed
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
	# Managing different libraries inside / outside Blender:
	# if bvp.Is_Numpy:
	CamMat = xRot * yRot * zRot
	d = np.array(CamMat*(oPos-cPos))
	# Other positions:
	d_Top = np.array(CamMat*(oPos_Top-cPos))
	d_L = np.array(CamMat*(oPos_L-cPos))
	d_R = np.array(CamMat*(oPos_R-cPos))
	xc = (x,0)
	yc = (y,0)
	zc = (z,0)
	# elif bvp.Is_Blender:
	# 	CamMat = xRot * yRot * zRot
	# 	d = CamMat*(oPos-cPos)
	# 	# Other positions:
	# 	d_Top = CamMat*(oPos_Top-cPos)
	# 	d_L = CamMat*(oPos_L-cPos)
	# 	d_R = CamMat*(oPos_R-cPos)
	# 	xc = x
	# 	yc = y
	# 	zc = z
	#print(CamMat)
	# For above, see eqns from Wikipedia page:
	#bx = (d[x]-ee[x])*(ee[z]/d[z]);
	#by = (d[y]-ee[y])*(ee[z]/d[y]);

	ImX_Bot = ImSz[x]/2. - d[xc]/d[zc] * (ImSz[x]/2.) / (tand(FOV/2.));
	ImY_Bot = d[yc]/d[zc] * (ImSz[y]/2.) / (tand(FOV/2.)) + ImSz[y]/2.;

	ImX_Top = ImSz[x]/2. - d_Top[xc]/d_Top[zc] * (ImSz[x]/2.) / (tand(FOV/2.))
	ImY_Top = d_Top[yc]/d_Top[z] * (ImSz[y]/2.) / (tand(FOV/2.)) + ImSz[y]/2.

	ImX_L = ImSz[x]/2. - d_L[xc]/d_L[zc] * (ImSz[x]/2.) / (tand(FOV/2.))
	ImY_L = d_L[yc]/d_L[z] * (ImSz[y]/2.) / (tand(FOV/2.)) + ImSz[y]/2.

	ImX_R = ImSz[x]/2. - d_R[xc]/d_R[zc] * (ImSz[x]/2.) / (tand(FOV/2.))
	ImY_R = d_R[yc]/d_R[z] * (ImSz[y]/2.) / (tand(FOV/2.)) + ImSz[y]/2.

	imPos_Bot = [ImX_Bot,ImY_Bot]
	imPos_Top = [ImX_Top,ImY_Top]
	imPos_L = [ImX_L,ImY_L]
	imPos_R = [ImX_R,ImY_R]

	#if bvp.Is_Numpy:
	mbs = lambda x: MakeBlenderSafe(x,'float')
	return mbs(imPos_Top),mbs(imPos_Bot),mbs(imPos_L),mbs(imPos_R) #,d,CamMat
	#elif bvp.Is_Blender:
	#	return imPos_Top,imPos_Bot,imPos_L,imPos_R #,d,CamMat

def PerspectiveProj_Inv(ImPos,bvpCam,Z):
	'''
	Usage: oPos = PerspProj_Inv(ImPos,bvpCam,Z)
	
	Inputs:
	    ImPos = x,y image position as a pct of the image (in range 0-1)
	    bvpCam = bvpCamera class, which contains all camera info (position, lens/FOV, angle)
	    Z = distance from camera for inverse computation
	
	Created by ML 2011.10.06
	'''

	'''
	NOTES: 

	Blender seems to convert focal length(in mm) to FOV by assuming a particular
	(horizontal/diagonal) distance, in mm, across an image. This is not
	exactly correct, i.e. the rendering effects will not necessarily match
	with real rectilinear lenses, etc... See
	http://www.metrocast.net/~chipartist/BlensesSite/index.html
	for more discussion.
	
	Test run:
	fL  = [10 15 25 35 50 100 182.881]; # different settings for focal length in Blender
	FOV = [115.989 93.695 65.232 49.134 35.489 18.181 10] # corresponding values for FOV (computed by Blender)
	ImDist = 32; # found by regression w/ values above and equation below:
	FOVcomputed = 2*atand(ImDist./(2*fL)); # Focal length equation, from
	# http://kmp.bdimitrov.de/technology/fov.html and http://www.bobatkins.com/photography/technical/field_of_view.html
	plot(fL,FOV,'bo',fL,FOVcomputed,'r')
	'''

	# Blender uses right-handed coordinates
	Handedness = 'Right'
	ImDist = 32. # Blender assumption - see above!
	FOV = 2*atand(ImDist/(2*bvpCam.lens))
	x,y,z = 0,1,2
	if Z>0:
		# ensure that Z < 0
		Z = -Z
	cPos = VectorFn(bvpCam.location[0]) 
	fixPos = VectorFn(bvpCam.fixPos[0])
	cTheta = vec2eulerXYZ(lst(fixPos-cPos))
	cTheta = VectorFn(cTheta)
	# Complication?: zero rotation in blender is DOWN, zero rotation for this computation seems to be UP
	if Handedness == 'Left':
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
	elif Handedness == 'Right':
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
	CamMat = xRot*yRot*zRot
	xP,yP = ImPos
	ImSz = [1,1]
	#if bvp.Is_Blender:
	#	CamMatInv = CamMat.inverted()
	#if bvp.Is_Numpy:
	CamMatInv = np.linalg.pinv(CamMat);
	# sample one point at Z units from camera
	# This calculation is basically: PctToSideOfImage * x/f * Z = X  # (tand(FOV/2.) = x/f)
	d = [0,0,Z]; 
	d[x] = -(xP-ImSz[x]/2.) * tand(FOV/2.)/(ImSz[x]/2.) * d[z] 
	d[y] = (yP-ImSz[y]/2.) * tand(FOV/2.)/(ImSz[y]/2.) * d[z]
	d = VectorFn(d)
	# So: d is a vector pointing straight from the camera to the object, with the camera at (0,0,0) pointing DOWN (?)
	# d needs to be rotated and shifted, according to the camera's real position, to have d point to the location
	# of the object in the world.
	oPos = CamMatInv*d+cPos
	return lst(oPos)

# if bvp.Is_Blender:
# 	def linePlaneInt(L0,L1,P0=(0.,0.,0.),n=(0.,0.,1.)):
# 		'''
# 		Usage: IntPt = linePlaneInt(L0,L1,P0=(0.,0.,0.),n=(0.,0.,1.))

# 		Find intersection of line with a plane.
		
# 		Line is specified by two points L0 and L1, each of which is a 
# 		list / tuple of (x,y,z) values.
# 		P0 is a point on the plane, and n is the normal of the plane.
# 		default is a flat floor at z=0 (P0 = (0,0,0), n = (0,0,1))
		
# 		For formulas / more description, see:
# 		http://en.wikipedia.org/wiki/Line-plane_intersection
		
# 		ML 2012.02.21
# 		'''
# 		L0 = VectorFn(L0)
# 		L1 = VectorFn(L1)
# 		P0 = VectorFn(P0) # point on the plane (floor - z=0)
# 		n = VectorFn(n) #Plane normal vector (straight up)
# 		L = L1-L0
# 		#d = (P0-L0)*n / (L*n)
# 		# So...:
# 		d = ((P0-L0)*n)/(L*n)
# 		# Intersection should be at [0,-2,-0]...
# 		# Take that, multiply it by L, add it to L0
# 		Intersection = lst(L*d + L0)
# 		return Intersection
# 	def vec2eulerXYZ(vec):
# 		'''
# 		converts from X,Y,Z vector (vector from CAMERA to ORIGIN - fixPos-camPos - to euler angles of rotation (X,Y,Z)

# 		ML 2012.01
# 		'''
# 		X,Y,Z = vec
# 		zR = -bnp.degrees(bnp.atan2(X,Y)) # Always true?? #np.sign(X)*np.sign(Y)*
# 		yR = 0. # ASSUMED - no roll of camera
# 		xR = bnp.degrees(bnp.atan(-(X**2+Y**2)**.5/Z))
# 		return xR,yR,zR
# 	class ImPosCount(object):
# 		'''
# 		Dummy class for now, just samples randomly...
# 		'''
# 		def __init__(self,xBin,yBin,ImSz,nBins=None,e=1):
# 			print('Warning! ImPosCount is not fully functional in Blender yet!')
# 			self.ImSz = ImSz
# 		def updateXY(self,X,Y):
# 			pass
# 		def sampleXY(self):
# 			X = random.random()*self.ImSz
# 			Y = random.random()*self.ImSz
# 			return X,Y
#else:
def concatVoxels(fDir,mode='sum'):
	"""
	Aggregate all 360 degree fisheye rendered images to a voxelization of an object
	Inputs:
		fDir = directory for 

	"""
	import matplotlib.pyplot as plt
	import re,os
	from scipy.io import savemat
	try:
		IsStr = isinstance(fDir,(str,unicode))
	except NameError:
		IsStr = isinstance(fDir,str)

	if IsStr and '*' in fDir:
		# Support wild-card directory structure
		fD,fP = os.path.split(fDir)
		fDir = sorted([f for f in os.listdir(fD) if fp.strip('*') in f])
	elif IsStr and not '*' in fDir:
		fDir = [fDir]

	dt = np.bool if mode=='inside' else np.float32

	# Get resolution from directory name
	mm = re.search('(?<=res)[0-9]*',fDir[0])
	res = int(mm.group())
	vox = np.zeros((res**3,),dt)

	for fD in fDir:
		fNm = sorted([os.path.join(fD,f) for f in os.listdir(fD) if 'png' in f])
		for f in fNm:
			mm = re.search('(?<=vox)[0-9]*',f)
			idx = int(mm.group())-1
			tmp = plt.imread(f)
			if mode=='inside':
				vox[idx] = np.all(tmp.flatten()==np.max(tmp))
			elif mode=='sum':
				vox[idx] = np.sum(tmp)
	return MakeBlenderSafe(vox,'float')

class ImPosCount(object):
	'''
	Class to store a count of how many times objects have appeared in each of (n x n) bins in an image
	Counts are used to draw new positions (the probability of drawing a given position is inversely 
	proportional to the number of times that position has occurred already)

	Inputs:
	xBin - x bin edges (or, r bin edges)
	yBin - y bin edges (or, theta bin edges)

	ImSz - size of each dimesion of the image (scalar) (thus, the image is assumed to be square)
	nBins - number of bins per dimension of image (scalar) (image is assumed to be square)
	e - am't (exponent) by which to increase the probability of drawing an under-represented location

	NOTES: 
	* for now, nBins and ImSz are both scalar** 2012.03.15
	* it seems that this could be used for radial bins as well with some minor modification
	** i.e., just by specifying r and theta values for xBin,yBin instead of x,y values
	'''
	def __init__(self,xBin,yBin,ImSz,nBins=None,e=1):
		if not bvp.Is_Numpy:
			raise Exception('Sorry, only runs in numpy!')
		if nBins:
			self.xBin = np.linspace(0,ImSz,nBins+1)
			self.yBin = np.linspace(0,ImSz,nBins+1)
			self.nBins = nBins**2
		else:
			self.nBins = (len(xBin)-1)*(len(yBin)-1)
			self.xBin = xBin
			self.yBin = yBin
		self.e = e
		self.hst = np.zeros((len(self.xBin)-1,len(self.yBin)-1))

	def updateXY(self,X,Y):
		'''
		Update 2D histogram count with one X,Y value pair
		'''
		if not isinstance(X,list):
			X = [X]
		if not isinstance(Y,list):
			Y = [Y]
		hstNew = np.histogram2d(Y,X,(self.xBin,self.yBin))[0]
		self.hst += hstNew

	def sampleXYnoWt(self):
		'''
		DEPRECATED!
		'''
		raise Exception("Deprecated! (I didn't think anyone used this shit!)")
		# One: pull one random sample within each spatial bin
		xl = [np.random.rand()*self.xBin[1]+x for x in self.xBin[:-1]]
		yl = [np.random.rand()*self.yBin[1]+x for x in self.yBin[:-1]]
		xp,yp = np.meshgrid(xl,yl)
		keep = np.random.randint(0,len(xp.flatten()))
		return xp.flatten()[keep],yp.flatten()[keep]

	def sampleXY(self):
		# One: pull one random sample within each spatial bin
		# NOTE: This won't work with non-uniform bins! fix??
		xp = np.random.rand()*(self.xBin[1]-self.xBin[0])
		yp = np.random.rand()*(self.yBin[1]-self.yBin[0])
		# Two: Choose one of those values with probability self.<one of the p values>
		# (look up efficient sampling of multinomial distributions:)
		# http://psiexp.ss.uci.edu/research/teachingP205C/205C.pdf
		# Take cumulative dist:
		#cumP = np.cumsum(self.pInv)
		#cumP = np.cumsum(self.adjPinv)
		idx = np.arange(self.nBins) # necessary?
		cumP = np.cumsum(self.noisyAdjPinv)
		# ... and sample that:
		r = np.random.rand()
		i = min(np.nonzero(r<cumP)[0])
		keep = idx[i]
		yAdd = self.yBin[np.floor(keep/(len(self.yBin)-1))]
		xAdd = self.xBin[np.mod(keep,len(self.xBin)-1)]
		x = xp+xAdd
		y = yp+yAdd
		return MakeBlenderSafe(x,'float'),MakeBlenderSafe(y,'float')

	@property
	def p(self):
		if np.all(self.hst==0):
			#return MakeBlenderSafe(np.ones(self.hst.shape)/float(np.sum(np.ones(self.hst.shape))))
			return np.ones(self.hst.shape)/float(np.sum(np.ones(self.hst.shape)))
		else:
			return self.hst/float(np.sum(self.hst))
	@property
	def pInv(self):
		pI = np.max(self.p)-self.p
		if np.all(pI==0):
			return np.ones(self.hst.shape)/float(self.nBins)
		else:
			pInv = pI/np.sum(pI)
			return pInv

	@property
	def adjP(self):
		'''
		Adjusted p value (p is raised to exponent e and re-normalized). The 
		higher the exponent (1->5 is a reasonable range), the more the
		overall distribution will stay flat.
		'''
		aa = (self.p**self.e)
		bb = np.sum(self.p**self.e)
		return aa/bb

	@property
	def adjPinv(self):
		aa = (self.pInv**self.e)
		bb = np.sum(self.pInv**self.e)
		return aa/bb

	@property
	def noisyPinv(self):
		# Add noise to allow not exactly flat distribution
		# (A flat distribution would REQUIRE filling in one of each bin each iteration
		# through the bins, which would be too strict a condition for scenes with stuff
		# in them.)
		p = self.pInv + np.random.randn(self.nBins**.5,self.nBins**.5)*.001
		p -= np.min(p)
		p /= np.sum(p)
		return p

	@property
	def noisyAdjPinv(self):
		p = self.adjPinv #.flatten()
		# The minimum here effectively sets the minimum likelihood for drawing a position.
		n = np.random.randn(self.nBins**.5,self.nBins**.5)*.001
		p += n
		p -= np.min(p)
		p /= np.sum(p)
		return p

def linePlaneInt(L0,L1,P0=(0.,0.,0.),n=(0.,0.,1.)):
	'''
	Usage: IntPt = linePlaneInt(L0,L1,P0=(0.,0.,0.),n=(0.,0.,1.))

	Find intersection of line with a plane.
	
	Line is specified by two points L0 and L1, each of which is a 
	list / tuple of (x,y,z) values.
	P0 is a point on the plane, and n is the normal of the plane.
	default is a flat floor at z=0 (P0 = (0,0,0), n = (0,0,1))

	For formulas / more description, see:
	http://en.wikipedia.org/wiki/Line-plane_intersection

	ML 2012.02.21
	'''
	L0 = np.matrix(L0).T
	L1 = np.matrix(L1).T
	P0 = np.matrix(P0).T # point on the plane (floor - z=0)
	n = np.matrix(n).T #Plane normal vector (straight up)
	L = L1-L0
	#d = (P0-L0)*n / (L*n)
	# So...:
	d = np.dot((P0-L0).T,n)/np.dot(L.T,n)
	# Intersection should be at [0,-2,-0]...
	# Take that, multiply it by L, add it to L0
	Intersection = lst(L*d + L0)
	return Intersection

def mat2eulerXYZ(mat):
	'''
	Conversion from matrix to euler
	from wikipedia page: 
	
	cosYcosZ, -cosYsinZ,   sinY
	...     , ...      ,   -cosYsinX
	...     , ...      ,   ...

	ML 2012.01
	'''
	yR = np.arcsin(mat[0,2])
	zR = np.arccos(mat[0,0]/np.cos(yR))
	xR = np.arcsin(mat[1,2]/-np.cos(yR))
	return np.array([xR,yR,zR])

def mat2eulerZYX(mat):
	'''
	Conversion from matrix to euler
	from wikipedia page: 
	
	cosYcosZ, -cosYsinZ,   sinY
	...     , ...      ,   -cosYsinX
	...     , ...      ,   ...
	
	ML 2012.01
	'''
	yR = -np.arcsin(mat[2,0])
	zR = np.arcsin(mat[2,1]/np.cos(yR))
	xR = np.arcsin(mat[0,0]/-np.cos(yR))
	return np.array([zR,yR,xR])	
	
def vec2eulerXYZ(vec):
	'''
	converts from X,Y,Z vector (vector from CAMERA to ORIGIN - fixPos-camPos - to euler angles of rotation (X,Y,Z)

	ML 2012.01
	'''
	X,Y,Z = vec
	zR = -np.degrees(np.arctan2(X,Y)) # Always true?? #np.sign(X)*np.sign(Y)*
	yR = 0. # ASSUMED - no roll of camera
	xR = np.degrees(np.arctan(-np.linalg.norm([X,Y])/Z))
	return xR,yR,zR

def mnrnd(d,p,n=1):
	'''
	sample distribution "d" w/ associated probabilities "p" "n" times
	'''
	rr = np.random.rand(n)
	cumP = np.cumsum(p)
	s = []
	for r in rr:
		idx = min(np.nonzero(r<cumP)[0])
		s.append(d[idx])
	return s

