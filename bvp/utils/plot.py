"""
.B.lender .V.ision .P.roject plotting functions. Require access to pylab, numpy.
"""
import glob
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, LinearSegmentedColormap
import skimage.color as skcol

from .math import circ_dist

# Circular color map
_ret_list = ([(1.0, 0.0, 0.0, 1.0), (1.0, 0.95, 0.0, 1.0), (0.0, 0.0, 1.0, 0, ), (0.0, 1.0, 1.0, 1.0), (1.0, 0.0, 0.0, 1.0)])
ret = LinearSegmentedColormap.from_list('Retinotopy_RYBCR', _ret_list)

try:
    from mpl_toolkits.mplot3d import Axes3D
except:
    pass

try: 
    import cv2
except ImportError:
    print("Missing cv2, some plot functions won't work")

def plot_cam_location(camera_list, n, fig=None, ax=None):
    FigSz = (8, 8)
    L = np.array([list(c.location[n]) for c in camera_list])
    x = L[:, 0]
    y = L[:, 1]
    z = L[:, 2]
    if not fig:
        fig = plt.figure(figsize=FigSz)
    #view1 = np.array([-85., 60.])
    if not ax:
        ax = Axes3D(fig) #, azim=view1[0], elev=view1[1])
    Axes3D.scatter(ax, x, y, zs=z, color='k')
    zer = np.array
    Axes3D.scatter(ax, zer([0]), zer([0]), zs=zer([5]), color='r')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_ylim3d(-50, 50)
    ax.set_xlim3d(-50, 50)
    ax.set_zlim3d(0, 50)
    #if Flag['ShowPositions']:
    fig.show()
    #else:
    #   fig.savefig(fName)
    return ax, fig


def load_exr_normals(f, xflip=True, yflip=True, zflip=True, clip=True):
    """Load exr file with assumption that values are surface normals"""
    img = cv2.imread(f, cv2.IMREAD_UNCHANGED)
    imc = img-1
    y, z, x = imc.T
    rev_x = xflip
    rev_y = yflip
    rev_z = zflip
    if rev_x: 
        x = -x
    if rev_y:
        y = -y
    if rev_z:
        z = -z
    imc = np.dstack([x.T,y.T,z.T])
    if clip:
        imc = np.clip(imc, -1, 1)
    return imc


def norm_color_image(tilt, slant, cmap=ret, vmin_t=0, vmax_t=2 * np.pi,
                    vmin_s=0, vmax_s=np.pi/2):
    """Create colorized image of surface normal tilt and slant

    Colorized 360 degree tilt according to circular color map; saturation
    indicates slant (shades of gray are flat-on). This provides a useful
    way to visualize surface normals.

    Parameters
    ----------
    tilt

    """
    # Normalize tilt (-pi to pi) -> (0, 1)
    norm_t = Normalize(vmin=vmin_t, vmax=vmax_t, clip=True)
    # Normalize slant (0 to pi/2) -> (0, 1)
    norm_s = Normalize(vmin=vmin_s, vmax=vmax_s, clip=True)
    # Convert normalized tilt to RGB color
    tilt_rgb_orig = cmap(norm_t(tilt))
    # Convert to HSV, replace saturation w/ normalized slant value
    tilt_hsv = skcol.rgb2hsv(tilt_rgb_orig[...,:3])
    tilt_hsv[:,:,1] = norm_s(slant)
    # Convert back to RGB
    tilt_rgb = skcol.hsv2rgb(tilt_hsv)
    tilt_rgb = np.dstack([tilt_rgb, 1-np.isnan(slant).astype(np.float)])
    # Mess with alpha...???
    a_im = np.dstack([tilt_rgb_orig[...,:3], norm_s(slant)])
    aa_im = tilt_rgb_orig[...,:3] * norm_s(slant)[..., np.newaxis] + np.ones_like(tilt_rgb_orig[...,:3]) * 0.5 * (1-norm_s(slant)[...,np.newaxis])
    aa_im = np.dstack([aa_im, 1-np.isnan(tilt).astype(np.float)])
    
    return aa_im


def load_exr_zdepth(f, thresh=1000):
    """Load exr file with assumption that values are z buffer (distance)

    Parameters
    ----------
    f : str
        file name
    thresh : scalar

    """
    img = cv2.imread(f, cv2.IMREAD_UNCHANGED)
    z = img[..., 0]
    z[z > thresh] = np.nan
    return z


def get_im_files(base_path, im_type='RGB'):
    """Convenience function to get bvp render output file names"""
    ftype = dict(RGB='png',
                 Zdepth='exr',
                 Normals='exr')
    im_files = sorted(glob.glob(base_path + "/*%s"%ftype[im_type]))
    return im_files

def load_ims(base_path, im_type='Scenes', do_proc=True, n=None):
    im_files = get_im_files(base_path, im_type=im_type)
    if im_type=='RGB':
        fn = plt.imread
    elif im_type=='Zdepth':
        fn = load_exr_zdepth
    elif im_type=='Normals':
        def fn(f):
            nrm = load_exr_normals(f)
            if do_proc:
                tilt, slant = tilt_slant(nrm)
                img = norm_color_image(tilt, slant)
                return img
            else:
                return nrm
    if n is None:
        n = len(im_files)
    ims = np.array([fn(f).T for f in im_files[:n]]).T

    return ims


def circ_dist2(a, b):
    """Angle between two angles
    """
    phi = np.e**(1j*a) / np.e**(1j*b)
    ang_dist = np.arctan2(phi.imag, phi.real)
    return ang_dist


def tilt_slant(img, make_1d=False):
    sky = np.all(img==0, axis=2)
    # Tilt
    tau = np.arctan2(img[:,:,2], img[:,:,0])
    # Slant
    sig = np.arccos(img[:,:,1])
    tau[sky] = np.nan
    sig[sky] = np.nan
    tau = circ_dist(tau, -np.pi / 2, degrees=False) + np.pi
    #tau = circ_dist(tau, np.pi) + np.pi
    if make_1d:
        tilt = tau[~np.isnan(tau)].flatilten()
        slant = sig[~np.isnan(sig)].flatilten()
        return tilt, slant
    else:
        return tau, sig

    
def tilt_slant_hist(tilt, slant, n_slant_bins = 30, n_tilt_bins = 90, do_log=True, 
                    vmin=None, vmax=None, H=None, ax=None, **kwargs):
    """Plot a polar histogram of tilt and slant values
    
    if H is None, computes & plots histogram of tilt & slant
    if H is True, computes histogram of tilt & slant & returns histogram count
    if H is a value, plots histogram of H"""
    if (H is None) or (H is True) or (H is False):
        return_h = H is True
        tbins = np.linspace(0, 2*np.pi, n_tilt_bins)      # 0 to 360 in steps of 360/N.
        sbins = np.linspace(0, np.pi/2, n_slant_bins) 
        H, xedges, yedges = np.histogram2d(tilt, slant, bins=(tbins,sbins), normed=True) #, weights=pwr)
        #H /= H.sum()
        if do_log:
            #print(H.shape)
            H = np.log(H)
            #H[np.isinf(H)] = np.nan
        if return_h:
            return H
    if do_log:
        if vmin is None:
            vmin=-8
        if vmax is None:
            vmax = 4
    e1 = n_tilt_bins * 1j
    e2 = n_slant_bins * 1j

    # Grid to plot your data on using pcolormesh
    theta, r = np.mgrid[0:2*np.pi:e1, 0:np.pi/2:e2]
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
    
    pc = ax.pcolormesh(theta, r, H, vmin=vmin, vmax=vmax, **kwargs)
    # Remove yticklabels, set limits
    #ax.set_yticklabels([]) 
    #ax.set_xticklabels([]) 
    ax.set_ylim([0, np.pi/2])
    ax.set_theta_offset(-np.pi/2)
    if ax is None:
        plt.colorbar(pc)