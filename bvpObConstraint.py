'''
Class for constraints on object position. 
Sub-class of bvpPosConstraint.

ML 2012.01.31
'''
import bvp,random,copy,sys
from bvp.bvpObject import bvpObject
from bvp.bvpPosConstraint import bvpPosConstraint
from bvp.utils.bvpMath import PerspectiveProj,PerspectiveProj_Inv,linePlaneInt,vecDist,listMean,AddLists,ImPosCount
from bvp.utils.basics import MakeBlenderSafe
class bvpObConstraint(bvpPosConstraint):
	def __init__(self,X=None,Y=None,Z=None,
				theta=(None,None,0.,360.),phi=(0.,0.,0.,0.),r=(0.,5.,-25.,25.),
				origin=(0.,0.,0.),Sz=(6.,1.,3.,10.),zRot=(None,None,-180.,180.)):
		'''
		Usage: bvpObConstraint(X=None,Y=None,Z=None,
				theta=(None,None,0.,360.),phi=(0.,0.,0.,0.),r=(0.,5.,-25.,25.),
				origin=(0.,0.,0.),Sz=(6.,1.,3.,10.),zRot=(None,None,-180.,180.))

		Class to store 3D position constraints for objects

		All inputs (X,Y,...) are 4-element lists: [Mean, Std, Min, Max]
		For rectangular X,Y,Z constraints, only specify X, Y, and Z
		For spherical constraints, only specify theta, phi, and r 

		"Obst" is a list of bvpObjects (with a size and position) that 
		are to be avoided in positioning objects

		ML 2012.10
		'''
		super(bvpObConstraint, self).__init__(X=X, Y=Y, Z=Z, theta=theta, phi=phi, r=r,origin=origin)
		# Set all inputs as class properties
		Inputs = locals()
		for i in Inputs.keys():
			if not i=='self':
				setattr(self,i,Inputs[i])
	
	def checkXYZS_3D(self,XYZpos,Sz,Obst=None,CheckBounds=True):
		"""
		Verify that a particular position and size is acceptable given "Obst" obstacles and 
		the position constraints of this object (in 3-D). 
		
		Inputs:
			XYZpos = (x,y,z) position (tuple or list)
			Sz = scalar size
			Obst = list of "bvpObject" instances to specify positions of obstacles to avoid
		Returns:
			BGboundOK = boolean; True if XYZpos is within boundary constraints
			ObDistOK = boolean; True if XYZpos does not overlap with other objects/obstacles 
		"""
		# (1) Check distance from allowable object position boundaries (X,Y,and/or r)
		BGboundOK_3D = [True,True,True]
		if CheckBounds:
			X_OK,Y_OK,r_OK = True,True,True # True by default
			if self.X:
				xA = True if self.X[2] is None else (XYZpos[0]-Sz/2.)>self.X[2]
				xB = True if self.X[3] is None else (XYZpos[0]+Sz/2.)<self.X[3]
				X_OK = xA and xB
			if self.Y:
				yA = True if self.Y[2] is None else (XYZpos[1]-Sz/2.)>self.Y[2]
				yB = True if self.Y[3] is None else (XYZpos[1]+Sz/2.)<self.Y[3]
				Y_OK = yA and yB
			if self.r:
				oX,oY,oZ = self.origin
				R = ((XYZpos[0]-oX)**2+(XYZpos[1]-oY)**2)**.5
				rA = True if self.r[2] is None else (R-Sz/2.)>self.r[2]
				rB = True if self.r[3] is None else (R+Sz/2.)<self.r[3]
				r_OK = rA and rB
			BGboundOK_3D = [X_OK,Y_OK,r_OK] # all([...])
		# (2) Check distance from other objects in 3D
		if Obst is not None:
			nObj = len(Obst)
		else:
			nObj = 0
		TmpOb = bvpObject(pos3D=XYZpos,size3D=Sz)
		ObDstOK_3D = [True]*nObj
		for c in range(nObj):
			DstThresh3D = TmpOb.size3D/2. +  Obst[c].size3D /2. 
			Dst3D = vecDist(TmpOb.pos3D,Obst[c].pos3D)
			ObDstOK_3D[c] = Dst3D>DstThresh3D
		return BGboundOK_3D,ObDstOK_3D

	def checkXYZS_2D(self,XYZpos,Sz,Cam,Obst=None,EdgeDist=0.,ObOverlap=50.):
		"""
		Verify that a particular position and size is acceptable given "Obst" obstacles and 
		the position constraints of this object (in 2D images space). 
		
		Inputs:
			XYZpos = (x,y,z) position (tuple or list)
			Sz = scalar size
			Cam = bvpCamera object (for computing perspective)
			Obst = list of "bvpObject" instances to specify positions of obstacles to avoid
			EdgeDist = proportion of object that can go outside of the 2D image (0.-100.)
			ObOverlap = proportion of object that can overlap with other objects (0.-100.)
		Returns:
			ImBoundOK = boolean; True if 2D projection of XYZpos is less than (EdgeDist) outside of image boundary 
			ObDistOK = boolean; True if 2D projection of XYZpos overlaps less than (ObOverlap) with other objects/obstacles 
		"""
		# (TODO: Make flexible for EdgeDist,ObOverlap being 0-1 or 0-100?)
		TmpOb = bvpObject(pos3D=XYZpos,size3D=Sz)
		tmpIP_Top,tmpIP_Bot,tmpIP_L,tmpIP_R = PerspectiveProj(TmpOb,Cam,ImSz=(100,100))
		TmpObSz_X = abs(tmpIP_R[0]-tmpIP_L[0])
		TmpObSz_Y = abs(tmpIP_Bot[1]-tmpIP_Top[1])
		TmpImPos = [listMean([tmpIP_R[0],tmpIP_L[0]]),listMean([tmpIP_Bot[1],tmpIP_Top[1]])]
		### --- (1) Check distance from screen edges --- ###
		Top_OK = EdgeDist < tmpIP_Top[1]
		Bot_OK = 100-EdgeDist > tmpIP_Bot[1]
		L_OK = EdgeDist < tmpIP_L[0]
		R_OK = 100-EdgeDist > tmpIP_R[0]
		EdgeOK_2D = all([Top_OK,Bot_OK,L_OK,R_OK])
		### --- (2) Check distance from other objects in 2D --- ###
		if Obst:
			nObj = len(Obst)
		else:
			nObj = 0
		obstPos2D_List = []
		Dist_List = []
		Dthresh_List = []
		ObstSz_List = []
		ObDstOK_2D = [True for x in range(nObj)]
		for c in range(nObj):
			# Get position of obstacle
			obstIP_Top,obstIP_Bot,obstIP_L,obstIP_R = PerspectiveProj(Obst[c],Cam,ImSz=(1.,1.))
			obstSz_X = abs(obstIP_R[0]-obstIP_L[0])
			obstSz_Y = abs(obstIP_Bot[1]-obstIP_Top[1])
			obstPos2D = [listMean([obstIP_R[0],obstIP_L[0]]),listMean([obstIP_Bot[1],obstIP_Top[1]])]
			ObstSz2D = listMean([obstSz_X,obstSz_Y])
			ObjSz2D = listMean([TmpObSz_X,TmpObSz_Y])
			# Note: this is an approximation! But we're ok for now (2012.10.08) with overlap being a rough measure
			PixDstThresh = (ObstSz2D/2. + ObjSz2D/2.) - (min([ObjSz2D,ObstSz2D]) * ObOverlap)
			ObDstOK_2D[c] = vecDist(TmpImPos,obstPos2D) > PixDstThresh
			# For debugging
			obstPos2D_List.append(obstPos2D) 
			Dist_List.append(vecDist(TmpImPos,obstPos2D))
			Dthresh_List.append(PixDstThresh)
			ObstSz_List.append(ObstSz2D)
		return EdgeOK_2D,ObDstOK_2D
	def checkSize2D(self,bvpObj,bvpCam,MinSz2D):
		'''
		Usage: checkSize2D(TmpPos,Cam,MinSz2D)

		Check whether (projected) 2D size of objects meets a minimum size criterion (MinSz2D)
		
		'''
		tmpIP_Top,tmpIP_Bot,tmpIP_L,tmpIP_R = PerspectiveProj(bvpObj,bvpCam,ImSz=(1.,1.))
		TmpObSz_X = abs(tmpIP_R[0]-tmpIP_L[0])
		TmpObSz_Y = abs(tmpIP_Bot[1]-tmpIP_Top[1])
		SzOK_2D = sum([TmpObSz_X,TmpObSz_Y])/2. > MinSz2D
		return SzOK_2D
	def sampleXYZ(self,Sz,Cam,Obst=None,EdgeDist=0.,ObOverlap=50.,RaiseError=False,nIter=100,MinSz2D=0.):
		'''
		Usage: sampleXYZ(self,Sz,Cam,Obst=None,EdgeDist=0.,ObOverlap=50.,RaiseError=False,nIter=100,MinSz2D=0.)

		Randomly sample across the 3D space of a scene, given object 
		constraints (in 3D) on that scene and the position of a camera*.
		Takes into account the size of the object to be positioned as 
		well as (optionally) the size and location of obstacles (other 
		objects) in the scene.

		* Currently only for first frame! (2012.02.19)

		Inputs: 
		Sz = object size
		Cam = bvpCamera object
		Obst = list of bvpObjects to be avoided 
		EdgeDist = Proportion of object by which objects must avoid the
			image border. Default=0 (touching edge is OK) Specify as a
			proportion (e.g., .1,.2, etc). Negative values mean that it
			is OK for objects to go off the side of the image. 
		ObOverlap = Proportion of image by which objects must avoid 
			the centers of other objects. Default = 50 (50% of 2D 
			object size)
		RaiseError = option to raise an error if no position can be found.
			default is False, which causes the function to return None
			instead of a position. Other errors will still be raised if 
			they occur.
		nIter = number of attempts to make at finding a scene arrangement
			that works with constraints.
		MinSz2D = minimum size of an object in 2D, given as proportion of screen (0-1)
		
		Outputs: 
		Position (x,y,z)

		NOTE: sampleXY (sampling across image space, but w/ 3D constraints)
		is currently (2012.02.22) the preferred method! (see NOTES in code)
		
		'''


		'''
		NOTES:
		Current method (2012.02.18) is to randomly re-sample until all 
		constraints on position are met. This can FAIL because of conflicting
		constraints (sometimes because not enough iterations were attempted,
		sometimes because there is no solution to be found that satisfies all
		the constraints.

		sampleXY is preferred because (a) it allows for control of how often 
		objects appear at particular positions in the 2D image, and (b) it 
		seems to fail less often (it does a better job of finding a solution 
		with fewer iterations).
		
		Random re-sampling seems to be a sub-optimal way to do this; better
		would be some sort of optimized sampling method with constraints. 
		(Lagrange multipliers?) But that sounds like a pain in the ass. 
		'''
		#Compute
		TooClose = True
		Iter = 1
		if Obst:
			nObj = len(Obst)
		else:
			nObj = 0
		while TooClose and Iter<nIter:
			if bvp.Verbosity_Level>9: 
				print("--------- Iteration %d ---------"%Iter)
			# Draw random position to start:
			c = copy.copy
			tmpC = bvpPosConstraint(X=c(self.X),Y=c(self.Y),Z=c(self.Z),r=c(self.r),theta=c(self.theta),phi=c(self.phi))
			# change x,y position (and/or radius) limits to reflect the size of the object 
			# (can't come closer to limit than Sz/2)
			ToLimit = ['X','Y','r']
			for pNm in ToLimit:
				value = getattr(tmpC,pNm)
				if value: # (?) if any(value): (?)
					if value[2]:
						value[2]+=Sz/2. # increase min by Sz/2
					if value[3]:
						value[3]-=Sz/2. # decrease max by Sz/2
				print(pNm + '='+ str(value))
				setattr(tmpC,pNm,value)
			TmpPos = tmpC.sampleXYZ()
			BoundOK_3D,ObDstOK_3D = self.checkXYZS_3D(TmpPos,Sz,Obst=Obst)
			EdgeOK_2D,ObDstOK_2D = self.checkXYZS_2D(TmpPos,Sz,Cam,Obst=Obst,EdgeDist=EdgeDist,ObOverlap=ObOverlap)
			TmpOb = bvpObject(pos3D=TmpPos,size3D=Sz)
			SzOK_2D = self.checkSize2D(TmpOb,Cam,MinSz2D)
			if all(ObDstOK_3D) and all(ObDstOK_2D) and all(BoundOK_3D) and EdgeOK_2D:
				TooClose = False
				TmpOb = bvpObject(pos3D=TmpPos,size3D=Sz)
				tmpIP_Top,tmpIP_Bot,tmpIP_L,tmpIP_R = PerspectiveProj(TmpOb,Cam,ImSz=(1.,1.))
				ImPos = [listMean([tmpIP_R[0],tmpIP_L[0]]),listMean([tmpIP_Bot[1],tmpIP_Top[1]])]
				return TmpPos,ImPos
			else:
				if bvp.Verbosity_Level>9:
					Reason = ''
					if not all(ObDstOK_3D):
						Add = 'Bad 3D Dist!\n'
						for iO,O in enumerate(Obst):
							Add += 'Dist %d = %.2f, Sz = %.2f\n'%(iO,vecDist(TmpPos,O.pos3D),O.size3D)
						Reason += Add
					if not all(ObDstOK_2D):
						Add = 'Bad 2D Dist!\n'
						for iO,O in enumerate(Obst):
							Add+= 'Dist %d: %s to %s\n'%(iO,str(obstPos2D_List[iO]),str(TmpImPos))
						Reason+=Add
					if not EdgeOK_2D:
						Reason+='Edge2D bad!\n%s\n'%(str([Top_OK,Bot_OK,L_OK,R_OK]))
					if not SzOK_2D:
						Reason+='Object too small / size ratio bad!'
					print('Rejected for:\n%s'%Reason)
			Iter += 1
		# Raise error if nIter is reached
		if Iter==nIter:
			if RaiseError:
				raise Exception('Iterated %d x without finding good position!'%nIter)
			else: 
				return None,None
	def sampleXY(self,Sz,Cam,Obst=None,ImPosCt=None,EdgeDist=0.,ObOverlap=.50,RaiseError=False,nIter=100,MinSz2D=0.):
		'''
		Usage: sampleXY(Sz,Cam,Obst=None,ImPosCt=None,EdgeDist=0.,ObOverlap=.50,RaiseError=False,nIter=100,MinSz2D=0.)

		Randomly sample across the 2D space of the image, given object 
		constraints (in 3D) on the scene and the position of a camera*.
		Takes into account the size of the object to be positioned as 
		well as (optionally) the size and location of obstacles (other 
		objects) in the scene.

		* Currently only for first frame! (2012.02.19)

		Inputs: 
		Sz = object size
		Cam = bvpCamera object
		Obst = list of bvpObjects to be avoided 
		ImPosCt = Class that keeps track of which image positions have been sampled 
			already. Can be omitted for single scenes.
		EdgeDist = Proportion of object by which objects must avoid the
			image border. Default=0 (touching edge is OK) Specify as a
			proportion (e.g., .1,.2, etc). Negative values mean that it
			is OK for objects to go off the side of the image. 
		ObOverlap = Proportion of image by which objects must avoid 
			the centers of other objects. Default = .50 (50% of 2D 
			object size)
		RaiseError = option to raise an error if no position can be found.
			default is False, which causes the function to return None
			instead of a position. 
		nIter = number of attempts to make at finding a scene arrangement
			that works with constraints.

		Outputs: 
		Position (x,y,z), ImagePosition (x,y)

		NOTE: This is currently (2012.08) the preferred method for sampling
		object positions in a scene. See notes in sampleXYZ for more.
		
		ML 2012.02
		'''

		"""Check on 2D object size???"""
		#Compute
		if not ImPosCt:
			ImPosCt = ImPosCount(0,0,ImSz=1.,nBins=5,e=1)
		TooClose = True
		Iter = 1
		if Obst:
			nObj = len(Obst)
		else:
			nObj = 0
		while TooClose and Iter<nIter:
			if bvp.Verbosity_Level>9: 
				print("--------- Iteration %d ---------"%Iter)
			#Zbase = self.sampleXYZ(Sz,Cam)[2]
			Zbase = self.origin[2]
			# Draw random (x,y) image position to start:
			ImPos = ImPosCt.sampleXY() 
			oPosZ = PerspectiveProj_Inv(ImPos,Cam,Z=100)
			oPosUp = linePlaneInt(Cam.location[0],oPosZ,P0=(0,0,Zbase+Sz/2.))
			TmpPos = oPosUp
			TmpPos[2] -= Sz/2.
			# Check on 3D bounds
			BoundOK_3D,ObDstOK_3D = self.checkXYZS_3D(TmpPos,Sz,Obst=Obst)
			# Check on 2D bounds
			EdgeOK_2D,ObDstOK_2D = self.checkXYZS_2D(TmpPos,Sz,Cam,Obst=Obst,EdgeDist=EdgeDist,ObOverlap=ObOverlap)
			# Instantiate temp object and...
			TmpOb = bvpObject(pos3D=TmpPos,size3D=Sz)
			# ... check on 2D size
			SzOK_2D = self.checkSize2D(TmpOb,Cam,MinSz2D)
			if all(ObDstOK_3D) and all(ObDstOK_2D) and EdgeOK_2D and all(BoundOK_3D) and SzOK_2D:
				TooClose = False
				if bvp.Is_Numpy:
					TmpPos = MakeBlenderSafe(TmpPos,'float')
				if bvp.Verbosity_Level>7:
					print('\nFinal image positions:')
					for ii,dd in enumerate(obstPos2D_List):
						print('ObPosX,Y=(%.2f,%.2f),ObstPosX,Y=%.2f,%.2f, D=%.2f'%(TmpImPos[1],TmpImPos[0],dd[1],dd[0],Dist_List[ii]))
						print('ObSz = %.2f, ObstSz = %.2f, Dthresh = %.2f\n'%(ObjSz2D,ObstSz_List[ii],Dthresh_List[ii]))
				return TmpPos,ImPos
			else:
				if bvp.Verbosity_Level>9:
					Reason = ''
					if not all(ObDstOK_3D):
						Add = 'Bad 3D Dist!\n'
						for iO,O in enumerate(Obst):
							Add += 'Dist %d = %.2f, Sz = %.2f\n'%(iO,vecDist(TmpPos,O.pos3D),O.size3D)
						Reason += Add
					if not all(ObDstOK_2D):
						Add = 'Bad 2D Dist!\n'
						for iO,O in enumerate(Obst):
							Add+= 'Dist %d: %s to %s\n'%(iO,str(obstPos2D_List[iO]),str(TmpImPos))
						Reason+=Add
					if not EdgeOK_2D:
						Reason+='Edge2D bad!\n%s\n'%(str([Top_OK,Bot_OK,L_OK,R_OK]))
					if not EdgeOK_3D:
						Reason+='Edge3D bad! (Object(s) out of bounds)'
					if not SzOK_2D:
						Reason+='Object too small / size ratio bad! '
					print('Rejected for:\n%s'%Reason)
			Iter += 1
		# Raise error if nIter is reached
		if Iter==nIter:
			if RaiseError:
				raise Exception('MaxAttemptReached','Iterated %d x without finding good position!'%nIter)
			else:
				if bvp.Verbosity_Level>3:
					print('Warning! Iterated %d x without finding good position!'%nIter)
				else:
					sys.stdout.write('.')
				return None,None
	def sampleSize(self):
		'''
		sample size from self.Sz
		'''
		Sz = self.sampleWConstr(self.Sz)
		return Sz
	def sampleRot(self,Cam=None):
		'''
		sample rotation from self.zRot (only rotation around Z axis for now!)
		If "Cam" argument is provided, rotation is constrained to be within 90 deg. of camera!
		'''
		if not Cam is None:
			import random
			VectorFn = bvp.utils.bvpMath.VectorFn
			# Get vector from fixation->camera
			cVec = VectorFn(Cam.fixPos[0])-VectorFn(Cam.location[0])
			# Convert to X,Y,Z Euler angles
			x,y,z = bvp.utils.bvpMath.vec2eulerXYZ(cVec)
			if round(random.random()):
				posNeg=1
			else:
				posNeg=-1
			zRot = z + random.random()*90.*posNeg
			zRot = bvp.utils.bvpMath.bnp.radians(zRot)
		else:
			zRot = self.sampleWConstr(self.zRot)
		return (0,0,zRot)


