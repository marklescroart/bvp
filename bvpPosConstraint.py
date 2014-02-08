'''
Class for 3D position information. Generates X,Y,Z positions in 3D from a set of constraints.

ML 2012.01.31
'''

import bvp,random
import math as bnp
from bvp.bvpConstraint import bvpConstraint
from bvp.utils.bvpMath import sph2cart # ? WORKING ? 

'''def mod(x,y): 
	z = x - bnp.floor(x/y) * y; 
	return z
'''
class bvpPosConstraint(bvpConstraint):
	def __init__(self,X=None,Y=None,Z=None,theta=None,phi=None,r=None,origin=(0.,0.,0.)):
		'''
		Usage: bvpPosConstraint(X=None,Y=None,Z=None,theta=None,phi=None,r=None)

		Class to store 3D position constraints for objects / cameras / whatever in Blender.

		All inputs (X,Y,...) are 4-element tuples: (Mean, Std, Min, Max)
		For rectangular X,Y,Z constraints, only specify X, Y, and Z
		For spherical constraints, only specify theta, phi, and r 
		XYZ constraints, if present, override spherical constraints

		ML 2012.01.31
		'''
		super(bvpPosConstraint,self).__init__(X)
		# Set all inputs as class properties
		Inputs = locals()
		for i in Inputs.keys():
			if not i=='self':
				setattr(self,i,Inputs[i])
		
	#def constr2xyz(self,ConstrObj):
	def sampleXYZ(self):
		'''
		Sample one position (X,Y,Z) from position distribution given spherical / XYZ constraints

		XYZ constraint will override spherical constraints if they are present.

		ML 2012.01.31
		'''
		if not self.X and not self.theta:
			raise Exception('Ya hafta provide either rectangular or spherical constraints on the distribution of positions!')
		# Calling this within Blender, code should never get to here - location should be defined
		if not self.X:
			thetaOffset = 270 # To make angles in Blender more interpretable
			# Use spherical constraints  ## THETA AND PHI MAY BE BACKWARDS FROM CONVENTION!! as is its, theta is Azimuth, phi is elevation
			if not self.theta:
				theta = random.random()*360.
			else:
				theta = self.sampleWConstr(self.theta)+thetaOffset
			phi = self.sampleWConstr(self.phi)
			r = self.sampleWConstr(self.r)
			# Constrain position
			x,y,z = sph2cart(r,theta,phi) # w/ theta, phi in degrees
			x = x+self.origin[0]
			y = y+self.origin[1]
			z = z+self.origin[2]
		else:
			# Use XYZ constraints:
			x = self.sampleWConstr(self.X)
			y = self.sampleWConstr(self.Y)
			z = self.sampleWConstr(self.Z)
		# Check for obstacles! 
		return x,y,z		


