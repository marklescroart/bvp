"""BVP Math utilities"""

import numpy as np
import copy
from .basics import make_blender_safe


def vector_fn(a):
    b = np.array(a)
    b.shape = (len(a), 1)
    return b


def lst(a):
    a = np.array(a)
    return list(a.flatten())


def circ_avg(a, b):
    """Circular average of two values (in DEGREES)
    """
    tmp = np.e**(1j * np.radians(a)) + np.e**(1j * np.radians(b))
    m = np.degrees(np.arctan2(tmp.imag, tmp.real))
    return m


def circ_dist(a, b, degrees=True):
    """Compute angle between two angles w/ circular statistics

    Parameters
    ----------
    a : scalar or array
        angle(s) TO WHICH to compute angular (aka rotational) distance
    b : scalar or array
        angle(s) FROM WHICH to compute angular (aka rotational) distance
    degrees : bool
        Whether a and b are in degrees (defaults to True; False means they are in radians)
    """
    if degrees:
        a = np.radians(a)
        b = np.radians(b)
    phase = np.e**(1j*a) / np.e**(1j*b)
    dist = np.arctan2(phase.imag, phase.real)
    if degrees:
        dist = np.degrees(dist)
    return dist


def vecDist(a, b):
    d = np.linalg.norm(np.array(a) - np.array(b))
    d = make_blender_safe(d, 'float')
    return d


# Convenience functions
def sind(theta):
    return np.sin(np.radians(theta))


def cosd(theta):
    return np.cos(np.radians(theta))


def tand(theta):
    return np.tan(np.radians(theta))


def atand(theta):
    return np.degrees(np.arctan(theta))


def sph2cart(r, az, elev, origin=None):
    """Convert spherical to cartesian coordinates

    Parameters
    ----------
    r : scalar or array-like
        radius
    az : scalar or array-like
        azimuth angle in degrees
    elev : scalar or array-like
        elevation angle in degrees
    origin : array-like
        [x,y,z] coordinates for origin around which r, az, & el are specified
    """
    z = r * sind(elev)
    rcoselev = r * cosd(elev)
    x = rcoselev * cosd(az)
    y = rcoselev * sind(az)
    if origin is not None:
        xo, yo, zo = origin
        x += xo
        y += yo
        z += zo
    return x, y, z


def cart2sph(x, y, z, degrees=True, origin=None):
    """Convert cartesian to spherical coordinates

    Parameters
    ----------
    x, y, z : scalar or array-like
        X, Y, and Z coordinates to be converted
    degrees : bool
        whether to convert radians to degrees (True= result in degrees, False = result in radians)
    origin : array-like
        x, y, z coordinates of origin around which to give r, theta, and phi
    """
    if origin is not None:
        xo, yo, zo = origin
        x -= xo
        y -= yo
        z -= zo
    r = (x**2 + y**2 + z**2)**0.5
    theta = np.arctan2(y, x)
    phi = np.arcsin(z / r)
    if degrees:
        return r, np.degrees(theta), np.degrees(phi)
    else:
        return r, theta, phi


def arc_pos(radius, n_points, theta_start, theta_fin, x_center=0, y_center=0):
    """Return linearly spaced points along an arc of a circle
    
    Parameters
    ----------
    radius : scalar
        radius of arc
    n_points : int
        number of points along the arc
    theta_start : scalar
        angle to start 
    theta_fin : scalar
        angle to finish
    x_center : scalar
        x center of arc
    y_center : scalar
        y center of arc
    """
    theta = np.linspace(np.radians(theta_start),
                        np.radians(theta_fin), n_points)
    x = radius * np.sin(theta) + x_center
    y = radius * np.cos(theta) + y_center
    return np.vstack([x, y]).T

    
def circle_pos(radius, n_positions, x_center=0, y_center=0, direction='botccw'):
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
        circ_pos[ii, 0] = radius[ii]*sind(tt) + x_center
        circ_pos[ii, 1] = -radius[ii]*cosd(tt) + y_center
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
    
    #sensor_size_
#     bvp_object : Object class
#         Should contain object position (x, y, z) and size
#     camera : Camera class
#         Should contain a list of (x, y, z) camera and fixation positions for n frames
#     image_size : tuple or list
#         Image size (e.g. [500, 500]) default = (1., 1.) (for pct of image computation)
#     frame_index : Int
#         Which frame in camera's frame list to compute the projection for

#     Notes
#     -----
#     Blender seems to convert focal length in mm to FOV by assuming 
#     a particular (horizontal/diagonal) distance, in mm, across an 
#     image. This is not exactly correct, i.e. the rendering effects 
#     will not necessarily match with real rectilinear lenses, etc... 
#     See http://www.metrocast.net/~chipartist/BlensesSite/index.html
#     for more discussion.

#     # Code testing the above:
#     import numpy as np
#     import matplotlib.pyplot as plt
#     # different settings for focal length in Blender
#     focal_len  = [10 15 25 35 50 100 182.881]; 
#     # corresponding values for fov (computed by Blender)
#     fov = [115.989 93.695 65.232 49.134 35.489 18.181 10] 
#     # Assumed by Blender
#     sensor_size = 32.
#     # Focal length equation, from:
#     # http://kmp.bdimitrov.de/technology/fov.html
#     # http://www.bobatkins.com/photography/technical/field_of_view.html
#     fov_computed = 2 * atand(sensor_size. / (2 * focal_len)) 
#     plt.plot(focal_len, fov, 'bo', focal_len, fov_computed, 'r')
#     """
#     if cam_lens is not None:
#         fov = 2*atand(sensor_size/(2*cam_lens))
#     else:
#         fov = 2*atand(sensor_size/(2*camera.lens))

#     objPos = bvp_object.pos3D
#     if cam_location is not None:
#         camPos = cam_location
#     else:
#         camPos = camera.location[0]
#     if cam_fix_location is not None:
#         fix_location = cam_fix_location
#     else:
#         fix_location = camera.fix_location[0]

    
#     # Convert to vector
#     camera_location = vector_fn(camPos)
#     fix_location = vector_fn(fix_location)
#     oPos = vector_fn(objPos)
    
#     # Get other bounds...
#     oPos_Top = oPos + vector_fn([0, 0, bvp_object.size3D])
#     oPos_L = oPos - vector_fn([bvp_object.size3D / 2., 0, 0])
#     oPos_R = oPos + vector_fn([bvp_object.size3D / 2., 0, 0])

#     # Compute camera_euler (Euler angles (XYZ) of camera)
#     cVec = fix_location-camera_location
#     # Get anlge of camera in world coordinates 
#     camera_euler = vector_to_eulerxyz(cVec)
#     # Blender is Right-handed
#     handedness = 'right' 
#     x, y, z = 0, 1, 2
#     if handedness == 'left':
#         # (Here just in case)
#         # X rotation
#         x_rot = np.matrix([[1., 0., 0.], 
#             [0., cosd(camera_euler[x]), -sind(camera_euler[x])], 
#             [0., sind(camera_euler[x]), cosd(camera_euler[x])]])
#         # Y rotation
#         y_rot = np.matrix([[cosd(camera_euler[y]), 0., sind(camera_euler[y])], 
#             [0., 1., 0.], 
#             [-sind(camera_euler[y]), 0., cosd(camera_euler[y])]])
#         # Z rotation
#         z_rot = np.matrix([[cosd(camera_euler[z]), -sind(camera_euler[z]), 0.], 
#             [sind(camera_euler[z]), cosd(camera_euler[z]), 0.], 
#             [0., 0., 1.]])
#     elif handedness == 'right':
#         # X rotation
#         x_rot = np.matrix([[1., 0., 0.], 
#             [0., cosd(camera_euler[x]), sind(camera_euler[x])], 
#             [0., -sind(camera_euler[x]), cosd(camera_euler[x])]])
#         # Y rotation
#         y_rot = np.matrix([[cosd(camera_euler[y]), 0., -sind(camera_euler[y])], 
#             [0., 1., 0.], 
#             [sind(camera_euler[y]), 0., cosd(camera_euler[y])]])
#         # Z rotation
#         z_rot = np.matrix([[cosd(camera_euler[z]), sind(camera_euler[z]), 0.], 
#             [-sind(camera_euler[z]), cosd(camera_euler[z]), 0.], 
#             [0., 0., 1.]])

#     camera_matrix = x_rot * y_rot * z_rot
#     d = np.array(camera_matrix * (oPos - camera_location))
#     # Other positions:
#     d_Top = np.array(camera_matrix*(oPos_Top-camera_location))
#     d_L = np.array(camera_matrix*(oPos_L-camera_location))
#     d_R = np.array(camera_matrix*(oPos_R-camera_location))
#     xc = (x, 0)
#     yc = (y, 0)
#     zc = (z, 0)

#     ImX_Bot = image_size[x]/2. - d[xc]/d[zc] * (image_size[x]/2.) / (tand(fov/2.));
#     ImY_Bot = d[yc]/d[zc] * (image_size[y]/2.) / (tand(fov/2.)) + image_size[y]/2.;

#     ImX_Top = image_size[x]/2. - d_Top[xc]/d_Top[zc] * (image_size[x]/2.) / (tand(fov/2.))
#     ImY_Top = d_Top[yc]/d_Top[z] * (image_size[y]/2.) / (tand(fov/2.)) + image_size[y]/2.

#     ImX_L = image_size[x]/2. - d_L[xc]/d_L[zc] * (image_size[x]/2.) / (tand(fov/2.))
#     ImY_L = d_L[yc]/d_L[z] * (image_size[y]/2.) / (tand(fov/2.)) + image_size[y]/2.

#     ImX_R = image_size[x]/2. - d_R[xc]/d_R[zc] * (image_size[x]/2.) / (tand(fov/2.))
#     ImY_R = d_R[yc]/d_R[z] * (image_size[y]/2.) / (tand(fov/2.)) + image_size[y]/2.

#     imPos_Bot = [ImX_Bot, ImY_Bot]
#     imPos_Top = [ImX_Top, ImY_Top]
#     imPos_L = [ImX_L, ImY_L]
#     imPos_R = [ImX_R, ImY_R]

#     mbs = lambda x: make_blender_safe(x, 'float')
#     return mbs(imPos_Top), mbs(imPos_Bot), mbs(imPos_L), mbs(imPos_R)


def get_camera_matrix(camera_location, fix_location, handedness='right'):
    """Get 3 x 3 camera matrix. 

    Parameters
    ----------
    camera_location : array-like
        list, tuple, or array for (x, y, z) camera location
    fix_location : array_like
        list, tuple, or array for (x, y, z) camera target (fixation) location
    handedness : str
        'right' or 'left'. Not tested or likey to be working for left-handed 
        coordinates. 

    Notes
    -----
    This returns the top left 3x3 part of Blender's 4x4 camera matrix; 
    do we need to bother with 4D camera matrix? Maybe. Not so far.
    """
    
    # Convert to vector
    camera_location = vector_fn(camera_location)
    fix_location = vector_fn(fix_location)
    # Prep for shift in L, R directions (wrt camera)
    if handedness == 'left':
        camera_vector = fix_location - camera_location
        # Get angle of camera in world coordinates 
        camera_euler = vector_to_eulerxyz(camera_vector)
        # Blender is Right-handed
        x, y, z = 0, 1, 2
        warnings.warn("Not checked for left-handed coordinates!")
        # is this just a different up vector??
        # (Here just in case; note, this is missing a factor here, doesn't work if 
        # camera is below fixation target.
        # X rotation
        x_rot = np.matrix([[1., 0., 0.], 
            [0., cosd(camera_euler[x]), -sind(camera_euler[x])], 
            [0., sind(camera_euler[x]), cosd(camera_euler[x])]])
        # Y rotation
        y_rot = np.matrix([[cosd(camera_euler[y]), 0., sind(camera_euler[y])], 
            [0., 1., 0.], 
            [-sind(camera_euler[y]), 0., cosd(camera_euler[y])]])
        # Z rotation
        z_rot = np.matrix([[cosd(camera_euler[z]), -sind(camera_euler[z]), 0.], 
            [sind(camera_euler[z]), cosd(camera_euler[z]), 0.], 
            [0., 0., 1.]])
        camera_matrix = x_rot * y_rot * z_rot
    elif handedness == 'right':
        # Per: https://ksimek.github.io/2012/08/22/extrinsic/
        up = (0, 0, 1)
        p, c = fix_location.flatten(), camera_location.flatten()
        L = np.array(p) - np.array(c)
        L = L / np.linalg.norm(L)
        s = np.cross(L, up)
        s = s / np.linalg.norm(s)
        u = np.cross(s, L)
        camera_matrix = np.matrix(np.vstack([s, u, -L]))
    return camera_matrix

def perspective_projection(location, 
                           camera_location, 
                           fix_location,
                           camera_fov=None, 
                           camera_lens=None, 
                           image_size=(1., 1.),
                           handedness='right', # Blender default
                           aspect_ratio=1.0,
                           sensor_size=36): 
    """Maps a 3D location to its 2D location given camera parameters
    
    Parameters
    ----------
    location : array-like
        3D (x, y, z) object location to be projected
    camera_location : array-like
        3D (x, y, z) camera and location
    fix_location : array-like
        3D (x, y, z) fixation location (track point for camera)
    image_size : array-like
        Image size (e.g. [500, 500]) default = (1., 1.) (for pct of image computation)

    Also, look into this (for within Blender only): 
    https://blender.stackexchange.com/questions/16472/how-can-i-get-the-cameras-projection-matrix
    """
    location = vector_fn(location)

    assert sum([(camera_lens is None), (camera_fov is None)]) == 1, 'Please specify EITHER `camera_lens` or `camera_fov` input'
    if camera_lens is not None:
        camera_fov = 2*atand(sensor_size/(2*camera_lens))
        camera_lens = None
    
    # Convert to vector
    location = vector_fn(location)
    camera_location = vector_fn(camera_location)
    camera_matrix = get_camera_matrix(camera_location, fix_location, handedness=handedness)
    # Blender is Right-handed
    x_sz, y_sz = image_size
    #d = np.array(camera_matrix * (location - camera_location))
    dx, dy, dz = np.array(camera_matrix * (location - camera_location)).flatten()
    #im_x = image_size[x] / 2. - d[x, 0] / d[x, 0] * (image_size[x] / 2.) / (tand(camera_fov / 2.))
    im_x = x_sz / 2. - dx / dz * (x_sz / 2.) / (tand(camera_fov / 2.))
    #im_y = d[y, 0] / d[z, 0] * (image_size[y] / 2.) / (tand(camera_fov / 2.)) + image_size[y] / 2.
    im_y = dy / dz * (y_sz / 2.) / (tand(camera_fov / 2.)) + y_sz / 2.
    return make_blender_safe([im_x, im_y], 'float')


def perspective_projection_inv(image_location, 
                               camera_location, 
                               fix_location,
                               Z,
                               camera_fov=None, 
                               camera_lens=None, 
                               image_size=(1., 1.),
                               handedness='right', 
                               aspect_ratio=1.,
                               sensor_size=36.):
    """Compute object location from image location + distance using inverse perspective projection

    Parameters
    ----------
    image_location : array-like
        x, y image position as a pct of the image (in range 0-1)
    camera_location : bvp.Camera instance
        Camera class, which contains all camera info (position, 
        lens/camera_fov, angle)
    Z : scalar
        Distance from camera for inverse computation (distance
        is not uniquely specified otherwise)
    camera_fov : 

    handedness : str
        'right' or 'left'. 'left' not guaranteed to work. Probably not working.
    sensor_size : int or array-like
        size of sensor. 

    Notes
    -----
    See `perspective_projection()` docstring for math
    """
    
    if Z>0:
        Z = -Z # ensure that Z < 0
    assert sum([(camera_lens is None), (camera_fov is None)]) == 1, 'Please specify EITHER `camera_lens` or `camera_fov` input'
    if camera_lens is not None:
        sensor_size_x = copy.copy(sensor_size)
        sensor_size_y = sensor_size / aspect_ratio 
        camera_fov = [2 * atand(ss / (2 * camera_lens)) for ss in [sensor_size_x, sensor_size_y]]
        camera_lens = None
    if not isinstance(camera_fov, (list, tuple)):
        camera_fov_x = camera_fov_y = camera_fov
    else:
        camera_fov_x, camera_fov_y = camera_fov
    
    # Get camera matrix
    camera_matrix = get_camera_matrix(camera_location, fix_location, handedness=handedness)

    x_pos, y_pos = image_location
    x_sz, y_sz = image_size
    camera_matrix_inv = np.linalg.pinv(camera_matrix)
    # Sample one point at Z units from camera
    # This calculation is basically: PctToSideOfImage * x/f * Z = X  # (tand(fov/2.) = x/f)
    if isinstance(x_pos, (int, np.integer)):
        x_pos = ((x_pos - x_sz / 2.) / (x_sz / 2.))
        # Assume if x_pos is int, so is y_pos
        if x_sz > y_sz:
            x_frac, y_frac = x_sz / y_sz, 1.0
        else:
            x_frac, y_frac = 1.0, x_sz / y_sz
    else:
        x_pos = (x_pos - 0.5) / 0.5
        x_frac, y_frac = x_sz, y_sz
    if isinstance(y_pos, (int, np.integer)):
        # Convert pixels to fraction
        y_pos = ((y_pos - y_sz / 2.) / (y_sz / 2.))
    else:
        y_pos = (y_pos - 0.5) / 0.5
    dx = -x_pos * tand(camera_fov_x / 2.) * (x_frac / 2.) * Z
    dy = y_pos * tand(camera_fov_y / 2.) * (y_frac / 2.) * Z
    d = vector_fn([2 * dx, 2 * dy, Z])
    # d is a vector pointing straight from the camera to the object, with the camera at (0, 0, 0) pointing DOWN
    # d needs to be rotated and shifted, according to the camera's real position, to have d point to the location
    # of the object in the world.
    location_3d = camera_matrix_inv * d + vector_fn(camera_location)
    return lst(location_3d)


def aim_camera(object_location,
               image_location, 
               camera_location, 
               camera_fov=None, 
               camera_lens=None, 
               image_size=(1., 1.),
               aspect_ratio = 1.,
               handedness='right'):
    """Place camera fixation to put an object at a specified 2D location
    
    Parameters
    ----------
    object_location : array-like
        (x, y, z) location of object to use as reference for aim
    image_location : array-like
        (x, y ) coordinate of image at which object center should appear
    camera_location : array-like
        (x, y, z) coordinates of camera
    camera_fov : scalar
        field of view of camera (in degrees...?)
        provide EITHER `camera_fov` or `camera_lens`, not both
    camera_lens : scalar
        camera lens in mm
        provide EITHER `camera_fov` or `camera_lens`, not both
    image_size : array-like
        size of image in which `image_location` is specified
    handedness : str
        handedness ('left' or 'right') of the coordinate system for the camera
        Blender default is 'right'


    Return 3D coordintes to place fixation for `object_location` to appear at `image_location`
    """
    # Compute image-center relative coords
    image_location = np.array(image_location)
    image_size = np.array(image_size)
    sz_x, sz_y = image_size
    if all(image_size > 1):
        # Pixel coordinates specified
        # `_c` for center-relative
        im_x, im_y = image_location
        im_x_c = -(im_x - (sz_x / 2))
        im_y_c = -(im_y - (sz_y / 2))
        fix_location_image = [int(im_x_c + (sz_x / 2)), 
                              int(im_y_c + (sz_y / 2))]
    else:
        fix_location_image = 1 - image_location
    Z = -np.linalg.norm(np.array(object_location) - np.array(camera_location))
    fix_location_3d = perspective_projection_inv(fix_location_image, 
                                                 camera_location, 
                                                 object_location,
                                                 Z,
                                                 camera_fov=camera_fov, 
                                                 camera_lens=camera_lens, 
                                                 image_size=image_size,
                                                 aspect_ratio=aspect_ratio,
                                                 handedness=handedness)
    return fix_location_3d
    

class ImPosCount(object):
    def __init__(self, x_bin_edges, y_bin_edges, image_size, n_bins=None, e=1):
        """
        Class to store a count of how many times objects have appeared in each of (n x n) bins in an image
        Counts are used to draw new positions (the probability of drawing a given position is inversely 
        proportional to the number of times that position has occurred already)

        Parameters
        ----------
        x_bin_edges : list
            x bin edges (or, r bin edges, for polar coordinates)
        y_bin_edges : list
            y bin edges (or, theta bin edges, for polar coordinates)
        image_size : scalar
            size of each dimesion of the image (scalar) (thus, the image is assumed to be square)
        n_bins : scalar
            number of bins per dimension of image (scalar) (image is assumed to be square)
        e : scalar
            am't (exponent) by which to increase the probability of drawing an under-represented location

        Notes
        -----
        * for now, n_bins and image_size are both scalar** 2012.03.15
        * it seems that this could be used for radial bins as well with some minor modification
        ** i.e., just by specifying r and theta values for x_bin_edges, y_bin_edges instead of x, y values
        """        
        if n_bins:
            self.x_bin_edges = np.linspace(0, image_size, n_bins+1)
            self.y_bin_edges = np.linspace(0, image_size, n_bins+1)
            self.n_bins = n_bins**2
        else:
            self.n_bins = (len(x_bin_edges)-1)*(len(y_bin_edges)-1)
            self.x_bin_edges = x_bin_edges
            self.y_bin_edges = y_bin_edges
        self.e = e
        self.hst = np.zeros((len(self.x_bin_edges)-1, len(self.y_bin_edges)-1))

    def updateXY(self, X, Y):
        """Update 2D histogram count with one X, Y value pair
        """
        if not isinstance(X, list):
            X = [X]
        if not isinstance(Y, list):
            Y = [Y]
        hstNew = np.histogram2d(Y, X, (self.x_bin_edges, self.y_bin_edges))[0]
        self.hst += hstNew

    def sampleXY(self):
        # One: pull one random sample within each spatial bin
        # NOTE: This won't work with non-uniform bins! fix??
        xp = np.random.rand()*(self.x_bin_edges[1]-self.x_bin_edges[0])
        yp = np.random.rand()*(self.y_bin_edges[1]-self.y_bin_edges[0])
        # Two: Choose one of those values with probability self.<one of the p values>
        # (look up efficient sampling of multinomial distributions:)
        # http://psiexp.ss.uci.edu/research/teachingP205C/205C.pdf
        # Take cumulative dist:
        #cumP = np.cumsum(self.p_inv)
        #cumP = np.cumsum(self.adjusted_p_inv)
        idx = np.arange(self.n_bins) # necessary?
        cumP = np.cumsum(self.noisy_adjusted_p_inv)
        # ... and sample that:
        r = np.random.rand()
        i = min(np.nonzero(r<cumP)[0])
        keep = idx[i]
        yAdd = self.y_bin_edges[int( np.floor(keep/(len(self.y_bin_edges)-1)) )]
        xAdd = self.x_bin_edges[int( np.mod(keep, len(self.x_bin_edges)-1) )]
        x = xp+xAdd
        y = yp+yAdd
        return make_blender_safe(x, 'float'), make_blender_safe(y, 'float')

    @property
    def p(self):
        if np.all(self.hst==0):
            return np.ones(self.hst.shape) / float(np.sum(np.ones(self.hst.shape)))
        else:
            return self.hst / float(np.sum(self.hst))

    @property
    def p_inv(self):
        pI = np.max(self.p)-self.p
        if np.all(pI==0):
            return np.ones(self.hst.shape)/float(self.n_bins)
        else:
            p_inv = pI/np.sum(pI)
            return p_inv

    @property
    def adjusted_p(self):
        """
        Adjusted p value (p is raised to exponent e and re-normalized). The 
        higher the exponent (1->5 is a reasonable range), the more the
        overall distribution will stay flat.
        """
        aa = (self.p**self.e)
        bb = np.sum(self.p**self.e)
        return aa/bb

    @property
    def adjusted_p_inv(self):
        aa = (self.p_inv**self.e)
        bb = np.sum(self.p_inv**self.e)
        return aa/bb

    @property
    def noisy_posinv(self):
        """Add noise to allow not exactly flat distribution

        (A flat distribution would REQUIRE filling in one of each bin each iteration
         through the bins, which would be too strict a condition for scenes with stuff
         in them.)
        """
        p = self.p_inv + np.random.randn(self.n_bins**.5, self.n_bins**.5)*.001
        p -= np.min(p)
        p /= np.sum(p)
        return p

    @property
    def noisy_adjusted_p_inv(self):
        p = self.adjusted_p_inv #.flatten()
        # The minimum here effectively sets the minimum likelihood for drawing a position.
        n = np.random.randn(int(self.n_bins**.5), int(self.n_bins**.5))*.001
        p += n
        p -= np.min(p)
        p /= np.sum(p)
        return p


def line_plane_intersection(L0, L1, P0=(0., 0., 0.), n=(0., 0., 1.)):
    """Find intersection of line with a plane.

    Parameters
    ----------
    L0 : array-like (list or tuple)
        First point on the line, (x, y, z)
    L1 : array-like (list or tuple)
        Second point on the line, (x, y, z)
    P0 : array-like (list or tuple)
        Point on the plane, (x, y, z)
    n : array-like (list or tuple)
        the normal of the plane, (x, y, z)

    Notes
    -----
    default is a flat floor at z=0 (P0 = (0, 0, 0), n = (0, 0, 1))
    For formulas / more description, see:
    http://en.wikipedia.org/wiki/Line-plane_intersection
    """
    L0 = np.matrix(L0).T
    L1 = np.matrix(L1).T
    P0 = np.matrix(P0).T # point on the plane (floor - z=0)
    n = np.matrix(n).T # plane normal vector (straight up)
    L = L1-L0
    # d = (P0 - L0) * n / (L * n)
    # So...:
    d = np.dot((P0 - L0).T, n) / np.dot(L.T, n)
    # Intersection should be at [0, -2, -0]...
    # Take that, multiply it by L, add it to L0
    intersection = lst(L*d + L0)
    return intersection


def mat2eulerXYZ(mat):
    """
    Conversion from matrix to euler from wikipedia page:

    cosYcosZ, -cosYsinZ,   sinY
    ...     , ...      ,   -cosYsinX
    ...     , ...      ,   ...
    """
    yR = np.arcsin(mat[0, 2])
    zR = np.arccos(mat[0, 0]/np.cos(yR))
    xR = np.arcsin(mat[1, 2]/-np.cos(yR))
    return np.array([xR, yR, zR])


def mat2eulerZYX(mat):
    """
    Conversion from matrix to euler from wikipedia page:

    cosYcosZ, -cosYsinZ,   sinY
    ...     , ...      ,   -cosYsinX
    ...     , ...      ,   ...
    """
    yR = -np.arcsin(mat[2, 0])
    zR = np.arcsin(mat[2, 1]/np.cos(yR))
    xR = np.arcsin(mat[0, 0]/-np.cos(yR))
    return np.array([zR, yR, xR])


def vector_to_eulerxyz(vec, y_rot=0):
    """Converts vector from CAMERA to ORIGIN to euler angles of rotation
    Parameters
    ----------
    vec : array-like
        vector from camera to target (camera_target_location-camera_location)
    y_rot : 
    """
    x, y, z = np.array(vec).flatten()
    z_rot = -np.degrees(np.arctan2(x, y)) # Always true?? #np.sign(x)*np.sign(y)*
    x_rot = np.degrees(np.arctan(-np.linalg.norm([x, y])/z))
    return x_rot, y_rot, z_rot


# For rigid body physics
def get_random_throw_vector(r=1, origin=(0, 0, 0), elev_range=(-5, 15), az_range=(-180, 180)):
    az = np.random.uniform(*az_range)
    elev = np.random.uniform(*elev_range)
    x, y, z = sph2cart(r, az, elev, origin=origin)
    return [x, y, z]
