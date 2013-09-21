'''
.B.lender .V.ision .P.roject plotting functions. Require access to pylab, numpy.

ML 2012.01
'''

try:
	from mpl_toolkits.mplot3d import Axes3D

def PlotCamLoc(CamList,n,FigH=None,ax=None):
	FigSz = (8,8)
	L = np.array([list(c.location[n]) for c in CamList])
	x = L[:,0]
	y = L[:,1]
	z = L[:,2]
	if not FigH:
		FigH = plt.figure(figsize=FigSz)
	#view1 = np.array([-85.,60.])
	if not ax:
		ax = Axes3D(FigH) #,azim=view1[0],elev=view1[1])
	Axes3D.scatter(ax,x,y,zs=z,color='k')
	zer = np.array
	Axes3D.scatter(ax,zer([0]),zer([0]),zs=zer([5]),color='r')
	ax.set_xlabel('X')
	ax.set_ylabel('Y')
	ax.set_zlabel('Z')
	ax.set_ylim3d(-50,50)
	ax.set_xlim3d(-50,50)
	ax.set_zlim3d(0,50)
	#if Flag['ShowPositions']:
	FigH.show()
	#else:
	#	FigH.savefig(fName)
	return ax,FigH
	
