'''
Class for storing constraints on camera / fixation position and motion.
Sub-class of bvpPosConstraint.

TODO: 
update sampleXYZ,sampleXY to take origin into account

ML 2012.02.15
'''
import bvp,copy,random
import math as bnp
from bvp.bvpPosConstraint import bvpPosConstraint
from bvp.utils.bvpMath import vecDist,sph2cart,cart2sph,CirclePos,circ_dst

class bvpCamConstraint(bvpPosConstraint):
	'''
	Extension of bvpPosConstraint to have:
	*camera speed (measured in Blender Units*) per second (assumes 15 fps)
	*pan / zoom constraints (True/False for whether pan/zoom are allowed)

	for pan, constrain radius
	for zoom, constrain theta and phi
	... and draw another position


	NOTES: 

	What circle positions mean in Blender space, from the -y perspective @x=0 :
				  (+y)
				  90
			135			45
		180					0  (or 360)
			225			315
				  270
				  (-y)
	THUS: to achieve 0 at dead-on (top position from -y), subtract 270 from all thetas

	'''
	## Camera position (spherical constraints)
	## Fixation position (X,Y,Z constraints)
	def __init__(self,r=(30.,3.,20.,40.),theta=(0.,60.,-135.,135.),phi=(17.5,2.5,12.5,45.5),
				origin=(0.,0.,0.),X=None,Y=None,Z=None,fixX=(0.,1.,-3.,3.),
				fixY=(0.,3.,-3.,3.),fixZ=(2.,.5,.0,3.5),
				speed=(3.,1.,0.,6.),pan=True,zoom=True):
		super(bvpCamConstraint, self).__init__(X=X, Y=Y, Z=Z, theta=theta, phi=phi, r=r, origin=origin)
		Inpt = locals()
		for i in Inpt.keys():
			if not i=='self':
				setattr(self,i,Inpt[i])
	def __repr__(self):
		S = 'bvpCamConstraint:\n'+self.__dict__.__repr__()
		return(S)
	def sampleFixPos(self,frames=None,obj=None):
		'''
		Sample fixation positions. Returns a list of (X,Y,Z) position tuples, nFrames long

		TO DO: 
		More constraints? max angle to change wrt camera? fixation change speed constraints?

		ML 2012.01.31
		'''
		fixPos = list()
		for ii in range(len(frames)):
			# So far: No computation of how far apart the frames are, so no computation of how fast the fixation point is moving. ADD??
			if obj is None:
				TmpFixPos = (self.sampleWConstr(self.fixX),self.sampleWConstr(self.fixY),self.sampleWConstr(self.fixZ))
			else:
				ObPos = [o.pos3D for o in obj]
				ObPosX = [None,None, min([x[0] for x in ObPos]),max([x[0] for x in ObPos])] # (Mean,Std,Min,Max) for sampleWConstr
				ObPosY = [None,None, min([x[1] for x in ObPos]),max([x[1] for x in ObPos])]
				#ObPosZ = [None,None, min([x[2] for x in ObPos]),max([x[2] for x in ObPos])] # use if we ever decide to do floating objects??
				TmpFixPos = (self.sampleWConstr(ObPosX),self.sampleWConstr(ObPosY),self.sampleWConstr(self.fixZ))
			# Necessary??
			#TmpFixPos = tuple([a+b for a,b in zip(TmpFixPos,self.origin)])
			fixPos.append(TmpFixPos)
		return fixPos
	def sampleCamPos(self,frames=None):
		'''
		Sample nFrames positions (X,Y,Z) from position distribution given spherical / XYZ position constraints, 
		as well as camera motion constraints (speed, pan/zoom, nFrames)

		Returns a list of (x,y,z) positions for each keyframe in "frames"

		NOTE: 
		ONLY tested up to 2 frames (i.e., len(frames)==2) as of 2012.02.15
		
		ML 2012.02
		'''
		fps = 15.
		thetaOffset = 270.
		nAttempts = 1000 # Number of times to try to get whole trajectory
		nSamples = 500 # Number of positions to sample for each frame to find an acceptable next frame (within constraints)
		Failed = True
		Ct = 0
		while Failed and Ct<nAttempts:
			location = []
			Ct+=1
			for iFr,fr in enumerate(frames):
				if iFr==0: 
					# For first frame, simply get a position
					TmpPos = self.sampleXYZ()
				else:
					newR,newTheta,newPhi = cart2sph(TmpPos[0]-self.origin[0],TmpPos[1]-self.origin[1],TmpPos[2]-self.origin[2])
					if bvp.Verbosity_Level>5: print('computed first theta to be: %.3f'%(newTheta))
					newTheta = circ_dst(newTheta-270.,0.) # account for offset
					if bvp.Verbosity_Level>5: print('changed theta to: %.3f'%(newTheta))
					''' All cart2sph need update with origin!! '''
					if self.speed:
						# Compute nSamples positions in a circle around last position
						# If speed has a distribution, this will potentially allow for multiple possible positions
						Rad = [self.sampleWConstr(self.speed) * (fr-frames[iFr-1])/fps for x in range(nSamples)]
						# cPos will give potential new positions at allowable radii around original position
						cPos = CirclePos(Rad,nSamples,TmpPos[0],TmpPos[1]) # Gives x,y; z will be same
						if self.X:
							# Clip new positions if they don't satisfy original Cartesian constraints:
							nPosXYZ = [xx+[location[iFr-1][2]] for xx in cPos if (self.X[2]<=xx[0]<=self.X[3]) and (self.Y[2]<=xx[1]<=self.Y[3])]
							# Convert to spherical coordinates for later computations to allow zoom / pan
							nPosSphBl = [cart2sph(xx[0]-self.origin[0],xx[1]-self.origin[1],xx[2]-self.origin[2]) for xx in nPosXYZ]
							nPosSphCs = [[xx[0],circ_dst(xx[1]-thetaOffset,0.),xx[2]] for xx in nPosSphBl]
						elif self.theta:
							# Convert circle coordinates to spherical coordinates (for each potential new position)
							# "Bl" denotes un-corrected Blender coordinate angles (NOT intuitive angles, which are the units for constraints)
							nPosSphBl = [cart2sph(cPos[ii][0]-self.origin[0],cPos[ii][1]-self.origin[1],location[iFr-1][2]-self.origin[2]) for ii in range(nSamples)]
							# returns r, theta, phi
							# account for theta offset in original conversion from spherical to cartesian
							# "Cs" means this is now converted to units of constraints
							nPosSphCs = [[xx[0],circ_dst(xx[1]-thetaOffset,0.),xx[2]] for xx in nPosSphBl]
							# Clip new positions if they don't satisfy original spherical constraints
							nPosSphCs = [xx for xx in nPosSphCs if (self.r[2]<=xx[0]<=self.r[3]) and (self.theta[2]<=xx[1]<=self.theta[3]) and (self.phi[2]<=xx[2]<=self.phi[3])]
							# We are now left with a list of positions in spherical coordinates that are the 
							# correct distance away and in permissible positions wrt the original constraints
					else: 
						# If no speed is specified, just sample from original distribution again
						nPosXYZ = [self.sampleXYZ() for x in range(nSamples)]
						nPosSphBl = [cart2sph(xx[0]-self.origin[0],xx[1]-self.origin[1],xx[2]-self.origin[2]) for xx in nPosXYZ]
						nPosSphCs = [[xx[0],circ_dst(xx[1]-thetaOffset,0.),xx[2]] for xx in nPosSphBl]
					
					# Now filter sampled positions (nPosSphCs) by pan/zoom constraints
					if not self.pan and not self.zoom:
						# Repeat same position
						pPosSphBl = [cart2sph(location[iFr-1][0]-self.origin[0],location[iFr-1][1]-self.origin[1],location[iFr-1][2]-self.origin[2])]
						pPosSphCs = [[xx[0],circ_dst(xx[1]-thetaOffset,0.),xx[2]] for xx in pPosSphBl]
					elif self.pan and self.zoom:
						# Any movement is possible; all positions up to now are fine
						pPosSphCs = nPosSphCs
					elif not self.pan and self.zoom:
						# Constrain theta within some wiggle range
						WiggleThresh = 3. # permissible azimuth angle variation for pure zooms, in degrees
						thetaDist = [abs(newTheta-xx[1]) for xx in nPosSphCs]
						pPosSphCs = [nPosSphCs[ii] for ii,xx in enumerate(thetaDist) if xx < WiggleThresh]
					elif not self.zoom and self.pan:
						# constrain r within some wiggle range
						WiggleThresh = newR*.05 # permissible distance to vary in radius from center - 5% of original radius
						rDist = [abs(newR-xx[0]) for xx in nPosSphCs]
						pPosSphCs = [nPosSphCs[ii] for ii,xx in enumerate(rDist) if xx < WiggleThresh]				
					else:
						raise Exception('Something done got fucked up. This line should never be reached.')
					if not pPosSphCs:
						# No positions satisfy constraints!
						break
					else:
						# Sample pPos (spherical coordinates for all possible new positions)	
						TmpPosSph = pPosSphCs[random.randint(0,len(pPosSphCs)-1)]
						r1,theta1,phi1 = TmpPosSph;
						TmpPos = sph2cart(r1,theta1+thetaOffset,phi1)
						TmpPos = [aa+bb for (aa,bb) in zip(TmpPos,self.origin)]
				location.append(TmpPos)
				if fr==frames[-1]:
					Failed=False
		if Failed:
			raise Exception(['Could not find camera trajectory to match constraints!'])
		else:
			return location
	