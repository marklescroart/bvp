"""BVP Math utilities"""

from __future__ import division

import numpy as np

from .basics import make_blender_safe

def VectorFn(a):
    b = np.array(a)
    b.shape = (len(a), 1)
    return b
def lst(a):
    a = np.array(a)
    return list(a.flatten())

def circ_avg(a, b):
    """Circular average of two values (in DEGREES)
    """
    Tmp = np.e**(1j*a/180.*np.pi)+np.e**(1j*b/180.*np.pi)
    Mean = np.arctan2(Tmp.imag, Tmp.real)/np.pi*180.
    return Mean

def circ_dist(a, b, degrees=True):
    """Compute angle between two angles w/ circular statistics
    """
    phase = np.e**(1j*a/180*np.pi) / np.e**(1j*b/180*np.pi)
    dist = np.degrees(np.arctan2(phase.imag, phase.real))
    return dist

def vecDist(a, b):
    d = np.linalg.norm(np.array(a) - np.array(b))
    d = make_blender_safe(d, 'float')
    return d

# Lazy man functions
def sind(theta):
    return np.sin(np.radians(theta))

def cosd(theta):
    return np.cos(np.radians(theta))

def tand(theta):
    return np.tan(np.radians(theta))

def atand(theta):
    return np.degrees(np.arctan(theta))

def sph2cart(r, az, elev):
    """Convert spherical to cartesian coordinates

    Parameters
    ----------
    r : scalar or array-like
        radius
    az : scalar or array-like
        azimuth angle in degrees
    elev : scalar or array-like
        elevation angle in degrees
    """
    z = r * sind(elev);
    rcoselev = r * cosd(elev);
    x = rcoselev * cosd(az);
    y = rcoselev * sind(az);
    return x, y, z

def cart2sph(x, y, z, degrees=True):
    """Convert cartesian to spherical coordinates

    Parameters
    ----------
    x, y, z : scalar or array-like
        X, Y, and Z coordinates to be converted
    degrees : bool
        whether to convert radians to degrees (True= result in degrees, False = result in radians)
    """
    r = (x**2 + y**2 + z**2)**0.5
    theta = np.arctan2(y, x)
    phi = np.arcsin(z / r)
    if degrees:
        return r, np.degrees(theta), np.degrees(phi)
    else:
        return r, theta, phi

def circle_pos(radius, n_positions, x_center=0, y_center=0, direction='BotCCW'):
    '''Return points in a circle. 
    
    Parameters
    ----------
    radius : scalar 
        Radius of the circle. Either one value or n_positions values.
    n_positions : int 
        number of positions around the circle
    x_center : scalar
        Defaults to 0
    y_center : scalar
        Defaults to 0
    direction : string 
        Specifies direction of points around circle - 
            'BotCCW' - start from bottom, go Counter-Clockwise, [default]
            'BotCW' - start from bottom, go Clockwise,
            'TopCCW' - top, Counter-Clockwise
            'TopCW' - top, Clockwise
        * Note that Right and Left CW or CCW can be obtained
        by switching x and y
        
    '''
    if (isinstance(radius, list) and len(radius)==1) or isinstance(radius, (float, int)):
        radius = np.tile(radius, (n_positions, 1))
    
    circ_pos = np.nan * np.ones((n_positions, 2))
    for ii, tt in enumerate(np.arange(0, 360., 360./n_positions)):
        circ_pos[ii, 0] = radius[ii]*_sind(tt) + x_center
        circ_pos[ii, 1] = -radius[ii]*_cosd(tt) + y_center
        ii += 1
        
    if direction.upper()=='BOTCCW':
        pass # default
    elif direction.upper()=='BOTCW':
        # reverse order of Y values
        circ_pos[:, 1] = circ_pos[::-1, 1]
    elif direction.upper()=='TOPCCW':
        # Keep top position (circ_pos[1, :]), and invert the rest of the Y values
        circ_pos = np.vstack((circ_pos[:1, :], circ_pos[::-1, :]))
        circ_pos[:, 1] = -(circ_pos[:, 1]-y_center) + y_center
    elif direction.upper()=='TOPCW':
        circ_pos[:, 1] = -(circ_pos[:, 2]-y_center) + y_center
    return circ_pos


def perspective_projection(bvp_object, camera, image_size=(1., 1.), cam_location=None, cam_fix_location=None,cam_lens=None): 
    """Gives image coordinates of an object (Bottom, Top, L, R) given the 3D position of the object and a camera.
    Assumes that the origin of the object is at the center of its base (BVP convention!)
    
    Parameters
    ----------
    bvp_object : Object class
        Should contain object position (x, y, z) and size
    camera : Camera class
        Should contain a list of (x, y, z) camera and fixation positions for n frames
    image_size : tuple or list
        Image size (e.g. [500, 500]) default = (1., 1.) (for pct of image computation)
    frame_index : Int
        Which frame in camera's frame list to compute the projection for

    Notes
    -----
    Blender seems to convert focal length in mm to FOV by assuming 
    a particular (horizontal/diagonal) distance, in mm, across an 
    image. This is not exactly correct, i.e. the rendering effects 
    will not necessarily match with real rectilinear lenses, etc... 
    See http://www.metrocast.net/~chipartist/BlensesSite/index.html
    for more discussion.

    # Code testing the above:
    import numpy as np
    import matplotlib.pyplot as plt
    # different settings for focal length in Blender
    focal_len  = [10 15 25 35 50 100 182.881]; 
    # corresponding values for fov (computed by Blender)
    fov = [115.989 93.695 65.232 49.134 35.489 18.181 10] 
    # Assumed by Blender
    image_dist = 32.
    # Focal length equation, from:
    # http://kmp.bdimitrov.de/technology/fov.html
    # http://www.bobatkins.com/photography/technical/field_of_view.html
    fov_computed = 2 * atand(image_dist. / (2 * focal_len)) 
    plt.plot(focal_len, fov, 'bo', focal_len, fov_computed, 'r')
    """
    image_dist = 32. # Blender assumption - see above!
    if cam_lens is not None:
        fov = 2*atand(image_dist/(2*cam_lens))
    else:
        fov = 2*atand(image_dist/(2*camera.lens))

    objPos = bvp_object.pos3D
    if cam_location is not None:
        camPos = cam_location
    else:
        camPos = camera.location[0]
    if cam_fix_location is not None:
        fix_location = cam_fix_location
    else:
        fix_location = camera.fix_location[0]
    
    # Convert to vector
    cPos = VectorFn(camPos)
    fPos = VectorFn(fix_location)
    oPos = VectorFn(objPos)
    # Prep for shift in L, R directions (wrt camera)
    cVec = fPos-cPos
    
    # Get other bounds...
    oPos_Top = oPos + VectorFn([0, 0, bvp_object.size3D])
    oPos_L = oPos - VectorFn([bvp_object.size3D / 2., 0, 0])
    oPos_R = oPos + VectorFn([bvp_object.size3D / 2., 0, 0])

    # Compute cTheta (Euler angles (XYZ) of camera)
    cVec = fPos-cPos
    # Get anlge of camera in world coordinates 
    cTheta = vec2eulerXYZ(cVec)
    # Blender is Right-handed
    handedness = 'right' 
    x, y, z = 0, 1, 2
    if handedness == 'left':
        # (Here just in case)
        # X rotation
        xRot = np.matrix([[1., 0., 0.], 
            [0., cosd(cTheta[x]), -sind(cTheta[x])], 
            [0., sind(cTheta[x]), cosd(cTheta[x])]])
        # Y rotation
        yRot = np.matrix([[cosd(cTheta[y]), 0., sind(cTheta[y])], 
            [0., 1., 0.], 
            [-sind(cTheta[y]), 0., cosd(cTheta[y])]])
        # Z rotation
        zRot = np.matrix([[cosd(cTheta[z]), -sind(cTheta[z]), 0.], 
            [sind(cTheta[z]), cosd(cTheta[z]), 0.], 
            [0., 0., 1.]])
    elif handedness == 'right':
        # X rotation
        xRot = np.matrix([[1., 0., 0.], 
            [0., cosd(cTheta[x]), sind(cTheta[x])], 
            [0., -sind(cTheta[x]), cosd(cTheta[x])]])
        # Y rotation
        yRot = np.matrix([[cosd(cTheta[y]), 0., -sind(cTheta[y])], 
            [0., 1., 0.], 
            [sind(cTheta[y]), 0., cosd(cTheta[y])]])
        # Z rotation
        zRot = np.matrix([[cosd(cTheta[z]), sind(cTheta[z]), 0.], 
            [-sind(cTheta[z]), cosd(cTheta[z]), 0.], 
            [0., 0., 1.]])

    CamMat = xRot * yRot * zRot
    d = np.array(CamMat*(oPos-cPos))
    # Other positions:
    d_Top = np.array(CamMat*(oPos_Top-cPos))
    d_L = np.array(CamMat*(oPos_L-cPos))
    d_R = np.array(CamMat*(oPos_R-cPos))
    xc = (x, 0)
    yc = (y, 0)
    zc = (z, 0)

    ImX_Bot = image_size[x]/2. - d[xc]/d[zc] * (image_size[x]/2.) / (tand(fov/2.));
    ImY_Bot = d[yc]/d[zc] * (image_size[y]/2.) / (tand(fov/2.)) + image_size[y]/2.;

    ImX_Top = image_size[x]/2. - d_Top[xc]/d_Top[zc] * (image_size[x]/2.) / (tand(fov/2.))
    ImY_Top = d_Top[yc]/d_Top[z] * (image_size[y]/2.) / (tand(fov/2.)) + image_size[y]/2.

    ImX_L = image_size[x]/2. - d_L[xc]/d_L[zc] * (image_size[x]/2.) / (tand(fov/2.))
    ImY_L = d_L[yc]/d_L[z] * (image_size[y]/2.) / (tand(fov/2.)) + image_size[y]/2.

    ImX_R = image_size[x]/2. - d_R[xc]/d_R[zc] * (image_size[x]/2.) / (tand(fov/2.))
    ImY_R = d_R[yc]/d_R[z] * (image_size[y]/2.) / (tand(fov/2.)) + image_size[y]/2.

    imPos_Bot = [ImX_Bot, ImY_Bot]
    imPos_Top = [ImX_Top, ImY_Top]
    imPos_L = [ImX_L, ImY_L]
    imPos_R = [ImX_R, ImY_R]

    mbs = lambda x: make_blender_safe(x, 'float')
    return mbs(imPos_Top), mbs(imPos_Bot), mbs(imPos_L), mbs(imPos_R) #, d, CamMat

def PerspectiveProj_Inv(image_location, camera, Z):
    """Compute object location from image location 
    
    ... using inverse perspective projection

    Parameters
    ----------
    image_location : list-like
        x, y image position as a pct of the image (in range 0-1)
    camera : bvp.Camera instance
        Camera class, which contains all camera info (position, 
        lens/fov, angle)
    Z : scalar
        Distance from camera for inverse computation (distance
        is not uniquely specified otherwise)

    Notes
    -----

    Blender seems to convert focal length(in mm) to fov by assuming a particular
    (horizontal/diagonal) distance, in mm, across an image. This is not
    exactly correct, i.e. the rendering effects will not necessarily match
    with real rectilinear lenses, etc... See
    http://www.metrocast.net/~chipartist/BlensesSite/index.html
    for more discussion.
    
    Test run:
    focal_len  = [10 15 25 35 50 100 182.881]; # different settings for focal length in Blender
    fov = [115.989 93.695 65.232 49.134 35.489 18.181 10] # corresponding values for fov (computed by Blender)
    image_dist = 32; # found by regression w/ values above and equation below:
    fov_computed = 2*atand(image_dist./(2*focal_len)); # Focal length equation, from
    # http://kmp.bdimitrov.de/technology/fov.html and http://www.bobatkins.com/photography/technical/field_of_view.html
    plot(focal_len, fov, 'bo', focal_len, fov_computed, 'r')
    """

    # Blender uses right-handed coordinates
    handedness = 'right'
    image_dist = 32. # Blender assumption - see above!
    fov = 2*atand(image_dist/(2*camera.lens))
    x, y, z = 0, 1, 2
    if Z>0:
        # ensure that Z < 0
        Z = -Z
    cPos = VectorFn(camera.location[0]) 
    fix_location = VectorFn(camera.fix_location[0])
    cTheta = vec2eulerXYZ(lst(fix_location-cPos))
    cTheta = VectorFn(cTheta)
    # Complication?: zero rotation in blender is DOWN, zero rotation for this computation seems to be UP
    if handedness == 'left':
        # X rotation
        xRot = np.matrix([[1., 0., 0.], 
            [0., cosd(cTheta[x]), -sind(cTheta[x])], 
            [0., sind(cTheta[x]), cosd(cTheta[x])]])
        # Y rotation
        yRot = np.matrix([[cosd(cTheta[y]), 0., sind(cTheta[y])], 
            [0., 1., 0.], 
            [-sind(cTheta[y]), 0., cosd(cTheta[y])]])
        # Z rotation
        zRot = np.matrix([[cosd(cTheta[z]), -sind(cTheta[z]), 0.], 
            [sind(cTheta[z]), cosd(cTheta[z]), 0.], 
            [0., 0., 1.]])
    elif handedness == 'right':
        # X rotation
        xRot = np.matrix([[1., 0., 0.], 
            [0., cosd(cTheta[x]), sind(cTheta[x])], 
            [0., -sind(cTheta[x]), cosd(cTheta[x])]])
        # Y rotation
        yRot = np.matrix([[cosd(cTheta[y]), 0., -sind(cTheta[y])], 
            [0., 1., 0.], 
            [sind(cTheta[y]), 0., cosd(cTheta[y])]])
        # Z rotation
        zRot = np.matrix([[cosd(cTheta[z]), sind(cTheta[z]), 0.], 
            [-sind(cTheta[z]), cosd(cTheta[z]), 0.], 
            [0., 0., 1.]])      
    else: 
        raise Exception('WTF are you thinking handedness should be? Options are "Right" and "Left" only!')
    CamMat = xRot * yRot * zRot
    xP, yP = image_location
    image_size = [1, 1]
    CamMatInv = np.linalg.pinv(CamMat);
    # sample one point at Z units from camera
    # This calculation is basically: PctToSideOfImage * x/f * Z = X  # (tand(fov/2.) = x/f)
    d = [0, 0, Z]; 
    d[x] = -(xP-image_size[x]/2.) * tand(fov/2.)/(image_size[x]/2.) * d[z] 
    d[y] = (yP-image_size[y]/2.) * tand(fov/2.)/(image_size[y]/2.) * d[z]
    d = VectorFn(d)
    # So: d is a vector pointing straight from the camera to the object, with the camera at (0, 0, 0) pointing DOWN (?)
    # d needs to be rotated and shifted, according to the camera's real position, to have d point to the location
    # of the object in the world.
    oPos = CamMatInv * d + cPos
    return lst(oPos)

def concatVoxels(fDir, mode='sum'):
    """
    Aggregate all 360 degree fisheye rendered images to a voxelization of an object
    Inputs:
        fDir = directory for 

    """
    import matplotlib.pyplot as plt
    import re, os
    from scipy.io import savemat
    try:
        IsStr = isinstance(fDir, (str, unicode))
    except NameError:
        IsStr = isinstance(fDir, str)

    if IsStr and '*' in fDir:
        # Support wild-card directory structure
        fD, fP = os.path.split(fDir)
        fDir = sorted([f for f in os.listdir(fD) if fp.strip('*') in f])
    elif IsStr and not '*' in fDir:
        fDir = [fDir]

    dt = np.bool if mode=='inside' else np.float32

    # Get resolution from directory name
    mm = re.search('(?<=res)[0-9]*', fDir[0])
    res = int(mm.group())
    vox = np.zeros((res**3, ), dt)

    for fD in fDir:
        fNm = sorted([os.path.join(fD, f) for f in os.listdir(fD) if 'png' in f])
        for f in fNm:
            mm = re.search('(?<=vox)[0-9]*', f)
            idx = int(mm.group())-1
            tmp = plt.imread(f)
            if mode=='inside':
                vox[idx] = np.all(tmp.flatten()==np.max(tmp))
            elif mode=='sum':
                vox[idx] = np.sum(tmp)
    return make_blender_safe(vox, 'float')

class ImPosCount(object):
    """
    Class to store a count of how many times objects have appeared in each of (n x n) bins in an image
    Counts are used to draw new positions (the probability of drawing a given position is inversely 
    proportional to the number of times that position has occurred already)

    Inputs:
    xBin - x bin edges (or, r bin edges)
    yBin - y bin edges (or, theta bin edges)

    image_size - size of each dimesion of the image (scalar) (thus, the image is assumed to be square)
    nBins - number of bins per dimension of image (scalar) (image is assumed to be square)
    e - am't (exponent) by which to increase the probability of drawing an under-represented location

    NOTES: 
    * for now, nBins and image_size are both scalar** 2012.03.15
    * it seems that this could be used for radial bins as well with some minor modification
    ** i.e., just by specifying r and theta values for xBin, yBin instead of x, y values
    """
    def __init__(self, xBin, yBin, image_size, nBins=None, e=1):
        if nBins:
            self.xBin = np.linspace(0, image_size, nBins+1)
            self.yBin = np.linspace(0, image_size, nBins+1)
            self.nBins = nBins**2
        else:
            self.nBins = (len(xBin)-1)*(len(yBin)-1)
            self.xBin = xBin
            self.yBin = yBin
        self.e = e
        self.hst = np.zeros((len(self.xBin)-1, len(self.yBin)-1))

    def updateXY(self, X, Y):
        """
        Update 2D histogram count with one X, Y value pair
        """
        if not isinstance(X, list):
            X = [X]
        if not isinstance(Y, list):
            Y = [Y]
        hstNew = np.histogram2d(Y, X, (self.xBin, self.yBin))[0]
        self.hst += hstNew

    def sampleXYnoWt(self):
        """
        DEPRECATED!
        """
        raise Exception("Deprecated! (I didn't think anyone used this shit!)")
        # One: pull one random sample within each spatial bin
        xl = [np.random.rand()*self.xBin[1]+x for x in self.xBin[:-1]]
        yl = [np.random.rand()*self.yBin[1]+x for x in self.yBin[:-1]]
        xp, yp = np.meshgrid(xl, yl)
        keep = np.random.randint(0, len(xp.flatten()))
        return xp.flatten()[keep], yp.flatten()[keep]

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
        yAdd = self.yBin[int( np.floor(keep/(len(self.yBin)-1)) )]
        xAdd = self.xBin[int( np.mod(keep, len(self.xBin)-1) )]
        x = xp+xAdd
        y = yp+yAdd
        return make_blender_safe(x, 'float'), make_blender_safe(y, 'float')

    @property
    def p(self):
        if np.all(self.hst==0):
            #return make_blender_safe(np.ones(self.hst.shape)/float(np.sum(np.ones(self.hst.shape))))
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
        """
        Adjusted p value (p is raised to exponent e and re-normalized). The 
        higher the exponent (1->5 is a reasonable range), the more the
        overall distribution will stay flat.
        """
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
        p = self.pInv + np.random.randn(self.nBins**.5, self.nBins**.5)*.001
        p -= np.min(p)
        p /= np.sum(p)
        return p

    @property
    def noisyAdjPinv(self):
        p = self.adjPinv #.flatten()
        # The minimum here effectively sets the minimum likelihood for drawing a position.
        n = np.random.randn(int(self.nBins**.5), int(self.nBins**.5))*.001
        p += n
        p -= np.min(p)
        p /= np.sum(p)
        return p

def linePlaneInt(L0, L1, P0=(0., 0., 0.), n=(0., 0., 1.)):
    """Find intersection of line with a plane.
    
    Line is specified by two points L0 and L1, each of which is a 
    list / tuple of (x, y, z) values.
    P0 is a point on the plane, and n is the normal of the plane.
    default is a flat floor at z=0 (P0 = (0, 0, 0), n = (0, 0, 1))
    
    Notes
    -----
    For formulas / more description, see:
    http://en.wikipedia.org/wiki/Line-plane_intersection
    """
    L0 = np.matrix(L0).T
    L1 = np.matrix(L1).T
    P0 = np.matrix(P0).T # point on the plane (floor - z=0)
    n = np.matrix(n).T #Plane normal vector (straight up)
    L = L1-L0
    #d = (P0-L0)*n / (L*n)
    # So...:
    d = np.dot((P0-L0).T, n)/np.dot(L.T, n)
    # Intersection should be at [0, -2, -0]...
    # Take that, multiply it by L, add it to L0
    Intersection = lst(L*d + L0)
    return Intersection

def mat2eulerXYZ(mat):
    """
    Conversion from matrix to euler
    from wikipedia page: 
    
    cosYcosZ, -cosYsinZ,   sinY
    ...     , ...      ,   -cosYsinX
    ...     , ...      ,   ...

    ML 2012.01
    """
    yR = np.arcsin(mat[0, 2])
    zR = np.arccos(mat[0, 0]/np.cos(yR))
    xR = np.arcsin(mat[1, 2]/-np.cos(yR))
    return np.array([xR, yR, zR])

def mat2eulerZYX(mat):
    """
    Conversion from matrix to euler
    from wikipedia page: 
    
    cosYcosZ, -cosYsinZ,   sinY
    ...     , ...      ,   -cosYsinX
    ...     , ...      ,   ...
    
    ML 2012.01
    """
    yR = -np.arcsin(mat[2, 0])
    zR = np.arcsin(mat[2, 1]/np.cos(yR))
    xR = np.arcsin(mat[0, 0]/-np.cos(yR))
    return np.array([zR, yR, xR])   
    
def vec2eulerXYZ(vec):
    """Converts vector from CAMERA to ORIGIN to euler angles of rotation
    Parameters
    ----------
    vec : list | 3-tuple | array
        vec = camera_target_location-camera_location

    """
    X, Y, Z = vec
    zR = -np.degrees(np.arctan2(X, Y)) # Always true?? #np.sign(X)*np.sign(Y)*
    yR = 0. # ASSUMED - no roll of camera
    xR = np.degrees(np.arctan(-np.linalg.norm([X, Y])/Z))
    return xR, yR, zR

def mnrnd(d, p, n=1):
    """
    sample distribution "d" w/ associated probabilities "p" "n" times
    """
    rr = np.random.rand(n)
    cumP = np.cumsum(p)
    s = []
    for r in rr:
        idx = min(np.nonzero(r<cumP)[0])
        s.append(d[idx])
    return s

