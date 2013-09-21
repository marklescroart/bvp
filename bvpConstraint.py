'''
Class for general constraints on random distributions. 

ML 2012.01.31
'''

import random
randn = random.gauss # Takes inputs Mean, Std
rand = random.random

class bvpConstraint(object):
	def __init__(self,X=None):
		'''
		Class for general constraints (Mean,Std,Min,Max) on random distributions (rectangular or normal)

		See bvpConstraint.sampleWConstr() for usage. Parent class for bvpPosConstriant, and thus also bvpObConstraint, bvpCamConstraint.

		ML 2012.01.31
		'''
		self.X = X
	def sampleWConstr(self,Inpt=None):
		'''
		Usage: x = sampleWConstr((Mean,Std,Min,Max))
		
		Get random sample given mean, std, min, max.

		Input is a tuple w/ 4 values: Mean, Std, Min, and Max

		If "Mean" (Input[0]) is None, returns uniform random sample, Min <= x <= Max
		If "Mean" is not None, returns x ~N(Mean,Std), Min <= x <= Max

		ML 2012.01.26
		'''
		if not Inpt:
			Inpt=self.X
		if not Inpt:
			# Raise error??
			print('Insufficient constraints!')
			return None
		Mean,Std,Min,Max = Inpt
		if not Mean is None:
			if not Std and Std!=0:
				# Raise error??
				print('Insufficient constraints!')
				return None
			n = randn(Mean,Std)
			if Max:
				n = min([n,Max])
			if Min:
				n = max([n,Min])
		else:
			if not Max:
				if not Max==0:
					# Raise error??
					print('Insufficient constraints!')
					return None
			if not Min:
				Min=0
			n = rand()*(Max-Min)+Min
		return n
