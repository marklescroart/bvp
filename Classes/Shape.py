'''
.B.lender .V.ision .P.roject utils for computing shape-related quantities in Blender

TO DO: generalize so that these can be used outside of Blender? Or do we care, because 
Blender is our storage for all mesh geometry...?
'''
import bvp
import numpy as np
#from scipy import sparse
#import scipy.sparse.linalg as la
import functools

if bvp.Is_Blender:
    from bvp.utils.blender import grab_only
    import mathutils as bmu
    import bpy


def _memo(fn):
    """Helper decorator memoizes the given zero-argument function.
    Really helpful for memoizing properties so they don't have to be recomputed
    dozens of times.
    """
    @functools.wraps(fn)
    def memofn(self, *args, **kwargs):
        if id(fn) not in self._cache:
            self._cache[id(fn)] = fn(self)
        return self._cache[id(fn)]
    return memofn

class bvpShape(object):
    """Class to hold geometric (triangulated manifold) information for bvpObjects.
    Mostly useful WITHIN Blender for now.

    Based on Alex Huth's Surface class from cortex.polyutils.py (from pycortex: 
    see https://github.com/gallantlab/pycortex/). 

    Implements some useful functions for dealing with functions across meshes.
    """
    def __init__(self, pts, polys, edges=None, make_object=None):
        """Initialize Shape.

        Parameters
        ----------
        pts : 2D ndarray, shape (total_verts, 3)
            Location of each vertex in space (arbitrary units). Order is x, y, z.
        polys : 2D ndarray, shape (total_polys, 3)
            Indices of the vertices in each triangle in the surface.
        make_object : string | None
            if a string is provided, a new Blender object with name `make_object` is created.
        """
        if isinstance(pts, np.ndarray):
            self.pts = pts.astype(np.double)
        self.polys = polys
        self.edges = edges
        # For now: demand bpy
        if not make_object is None:
            if edges is None:
                #raise Exception("Must supply edges to make new shape!")
                edges = []
            me = bpy.data.meshes.new(make_object+'_mesh')
            me.from_pydata(pts, edges, polys)
            self.ob = bpy.data.objects.new(make_object, me)
        else: 
            self.ob = None
        self._cache = dict()
        self._rlfac_solvers = dict()
        self._nLC_solvers = dict()

    @classmethod
    def from_object(cls, obgrp, name=None, replace=True):
        """Get pts, polys from blender object (i.e., a group of potentially many Blender objects)

        Eventually:
        Combines multiple meshes into one via (??), finds surface, maps surface to sphere (?)
        
        For now:
        returns pts, polys iff mesh is already a single (g0?) manifold.

        Parameters
        ----------
        obgrp : blender group instance
            Should be the group defining a BVP object (for now: that has already been fully imported into the scene)
            ALSO accepts blender object instances... for now?
        name : string
            Name for newly-formed shape object
        Returns
        -------
        bvpShape : bvpShape instance
            Having defined `pts` & `polys`

        """
        # Test for single (manifold?) mesh:
        if isinstance(obgrp, bpy.types.Object):
            obgrp = [obgrp]
        elif isinstance(obgrp, bpy.types.Group):
            obgrp = list(obgrp.objects)
        if len(obgrp)>1:
            # Ruh roh... (TEMP ERRROR for multiple objects) 
            raise NotImplementedError("Can't handle multi-object groups yet!")
        for ob in obgrp:
            # Check for multiple meshes within group
            grab_only(ob)
            bpy.ops.mesh.separate(type='LOOSE')
            nobjects = len(bpy.context.selected_objects)
            if nobjects>1:
                # Ruh roh... (TEMP ERROR for multiple meshes)
                raise NotImplementedError("Can't handle multi-mesh objects yet!")
            for oo in bpy.context.selected_objects:
                print("Getting pts, polys, edges...")
                #Get pts, polys
                # Was np.array... (may need arrays for math in steps to be added)
                pts = [v.co for v in oo.data.vertices]
                polys = [p.vertices for p in oo.data.polygons]
                edges = [e.vertices for e in oo.data.edges]

            # EVENTUALLY, concatenate pts, polys, edges somehow...
            # Power crust?
            # Spherize?

        # Make new object w/ concatenated pts, polys, edges
        S = cls.__new__(cls)
        if replace:
            S.__init__(pts, polys, edges=edges, make_object=name)
        else:
            if len(obgrp)>1:
                raise NotImplementedError("Don't know what to do with multi-object groups!")
            S.__init__(pts, polys, edges=edges, make_object=None)
            S.ob = obgrp[0]
        # Triangulate mesh (if necessary)
        polytest = np.array([len(p.vertices) for p in S.ob.data.polygons])
        if np.max(polytest)>3:
            S.triangulate()
        
        # Re-compute pts, polys
        S.pts = np.array([v.co for v in S.ob.data.vertices])
        S.polys = np.array([p.vertices for p in S.ob.data.polygons])
        S.edges = np.array([p.vertices for p in S.ob.data.edges])
        
        # (optionally) replace current object(s)
        if replace:
            for ob in obgrp:
                bpy.context.scene.objects.unlink(ob)
            bpy.context.scene.objects.link(S.ob)
        
        # Output
        grab_only(S.ob)
        return S
        
    @property
    @_memo
    def ppts(self):
        """3D matrix of points in each face: n faces x 3 points per face x 3 coords per point.
        """
        return self.pts[self.polys]
    
    @property
    @_memo
    def connected(self):
        """Sparse matrix of vertex-face associations.
        """
        npt = len(self.pts)
        npoly = len(self.polys)
        print(npt)
        print(npoly)
        return sparse.coo_matrix((np.ones((3*npoly, )), # data
                                  (np.hstack(self.polys.T), # row
                                   np.tile(range(npoly), (1, 3)).squeeze())), # col
                                 (npt, npoly)).tocsr() # size
    @property
    @_memo
    def adj(self):
        """Sparse vertex adjacency matrix.
        """
        npt = len(self.pts)
        npoly = len(self.polys)
        adj1 = sparse.coo_matrix((np.ones((npoly, )), 
                                  (self.polys[:, 0], self.polys[:, 1])), (npt, npt))
        adj2 = sparse.coo_matrix((np.ones((npoly, )), 
                                  (self.polys[:, 0], self.polys[:, 2])), (npt, npt))
        adj3 = sparse.coo_matrix((np.ones((npoly, )), 
                                  (self.polys[:, 1], self.polys[:, 2])), (npt, npt))
        return (adj1 + adj2 + adj3).tocsr()
    
    @property
    @_memo
    def face_normals(self):
        """Normal vector for each face. [keep?]
        """
        # Compute normal vector direction
        nnfnorms = np.cross(self.ppts[:, 1] - self.ppts[:, 0], 
                            self.ppts[:, 2] - self.ppts[:, 0])
        # Normalize to norm 1
        nfnorms = nnfnorms / np.sqrt((nnfnorms**2).sum(1))[:, np.newaxis]
        # Ensure that there are no nans (shouldn't be a problem with well-formed surfaces)
        return np.nan_to_num(nfnorms)

    @property
    @_memo
    def vertex_normals(self):
        """Normal vector for each vertex (average of normals for neighboring faces). [keep?]
        """
        # Average adjacent face normals
        nnvnorms = np.nan_to_num(self.connected.dot(self.face_normals) / self.connected.sum(1)).A
        # Normalize to norm 1
        return nnvnorms / np.sqrt((nnvnorms**2).sum(1))[:, np.newaxis]

    @property
    @_memo
    def face_areas(self):
        """Area of each face. [keep?]
        """
        # Compute normal vector (length is face area)
        nnfnorms = np.cross(self.ppts[:, 1] - self.ppts[:, 0], 
                            self.ppts[:, 2] - self.ppts[:, 0])
        # Compute vector length
        return np.sqrt((nnfnorms**2).sum(-1))

    @property
    @_memo
    def cotangent_weights(self):
        """Cotangent of angle opposite each vertex in each face.
        """
        ppts = self.ppts
        cots1 = ((ppts[:, 1]-ppts[:, 0]) *
                 (ppts[:, 2]-ppts[:, 0])).sum(1) / np.sqrt((np.cross(ppts[:, 1]-ppts[:, 0], 
                                                                   ppts[:, 2]-ppts[:, 0])**2).sum(1))
        cots2 = ((ppts[:, 2]-ppts[:, 1]) *
                 (ppts[:, 0]-ppts[:, 1])).sum(1) / np.sqrt((np.cross(ppts[:, 2]-ppts[:, 1], 
                                                                   ppts[:, 0]-ppts[:, 1])**2).sum(1))
        cots3 = ((ppts[:, 0]-ppts[:, 2]) *
                 (ppts[:, 1]-ppts[:, 2])).sum(1) / np.sqrt((np.cross(ppts[:, 0]-ppts[:, 2], 
                                                                   ppts[:, 1]-ppts[:, 2])**2).sum(1))

        # Then we have to sanitize the fuck out of everything..
        cots = np.vstack([cots1, cots2, cots3])
        cots[np.isinf(cots)] = 0
        cots[np.isnan(cots)] = 0
        return cots

    @property
    @_memo
    def laplace_operator(self):
        """Laplace-Beltrami operator for this surface. A sparse adjacency matrix with
        edge weights determined by the cotangents of the angles opposite each edge.
        Returns a 4-tuple (B, D, W, V) where D is the 'lumped mass matrix', W is the weighted
        adjacency matrix, and V is a diagonal matrix that normalizes the adjacencies.
        The 'stiffness matrix', A, can be computed as V - W.

        The full LB operator can be computed as D^{-1} (V - W).
        
        B is the finite element method (FEM) 'mass matrix', which replaces D in FEM analyses.
        
        See 'Discrete Laplace-Beltrami operators for shape analysis and segmentation'
        by Reuter et al., 2009 for details.
        """
        ## Lumped mass matrix
        D = self.connected.dot(self.face_areas) / 3.0

        ## Stiffness matrix
        npt = len(self.pts)
        cots1, cots2, cots3 = self.cotangent_weights
        # W is weighted adjacency matrix
        W1 = sparse.coo_matrix((cots1, (self.polys[:, 1], self.polys[:, 2])), (npt, npt))
        W2 = sparse.coo_matrix((cots2, (self.polys[:, 2], self.polys[:, 0])), (npt, npt))
        W3 = sparse.coo_matrix((cots3, (self.polys[:, 0], self.polys[:, 1])), (npt, npt))
        W = (W1 + W1.T + W2 + W2.T + W3 + W3.T).tocsr() / 2.0
        
        # V is sum of each col
        V = sparse.dia_matrix((np.array(W.sum(0)).ravel(), [0]), (npt, npt))
        
        # A is stiffness matrix
        #A = W - V # negative operator -- more useful in practice

        # For FEM:
        Be1 = sparse.coo_matrix((self.face_areas, (self.polys[:, 1], self.polys[:, 2])), (npt, npt))
        Be2 = sparse.coo_matrix((self.face_areas, (self.polys[:, 2], self.polys[:, 0])), (npt, npt))
        Be3 = sparse.coo_matrix((self.face_areas, (self.polys[:, 0], self.polys[:, 1])), (npt, npt))
        Bd = self.connected.dot(self.face_areas) / 6
        dBd = sparse.dia_matrix((Bd, [0]), (len(D), len(D)))
        B = (Be1 + Be1.T + Be2 + Be2.T + Be3 + Be3.T)/12 + dBd
        return B, D, W, V

    def mean_curvature(self):
        """Compute mean curvature of this surface using the Laplace-Beltrami operator.
        Curvature is computed at each vertex. It's probably pretty noisy, and should
        be smoothed using smooth().

        Negative values of mean curvature mean that the surface is folded inward
        (as in a sulcus), positive values of curvature mean that the surface is
        folded outward (as on a gyrus).

        Returns
        -------
        curv : 1D ndarray, shape (total_verts, )
            The mean curvature at each vertex.
        """
        B, D, W, V = self.laplace_operator
        npt = len(D)
        Dinv = sparse.dia_matrix((D**-1, [0]), (npt, npt)).tocsr() # construct Dinv
        L = Dinv.dot((V-W))
        curv = (L.dot(self.pts) * self.vertex_normals).sum(1)
        return curv

    def smooth(self, scalars, factor=1.0, iterations=1):
        """Smooth vertex-wise function given by `scalars` across the surface using
        mean curvature flow method (see http://brickisland.net/cs177fa12/?p=302).

        Amount of smoothing is controlled by `factor`.

        Parameters
        ----------
        scalars : 1D ndarray, shape (total_verts, )
            A scalar-valued function across the cortex, such as the curvature
            supplied by mean_curvature.
        factor : float, optional
            Amount of smoothing to perform, larger values smooth more.
        iterations : int, optional
            Number of times to repeat smoothing, larger values smooths more.

        Returns
        -------
        smscalars : 1D ndarray, shape (total_verts, )
            Smoothed scalar values.
        """
        if factor == 0.0:
            return scalars
        
        B, D, W, V = self.laplace_operator
        npt = len(D)
        lfac = sparse.dia_matrix((D, [0]), (npt, npt)) - factor * (W-V)
        goodrows = np.nonzero(~np.array(lfac.sum(0) == 0).ravel())[0]
        lfac_solver = sparse.linalg.dsolve.factorized(lfac[goodrows][:, goodrows])
        to_smooth = scalars
        for _ in range(iterations):
            from_smooth = lfac_solver((D * to_smooth)[goodrows])
            to_smooth[goodrows] = from_smooth
        smscalars = np.zeros(scalars.shape)
        smscalars[goodrows] = from_smooth
        return smscalars
        
    @property
    @_memo
    def avg_edge_length(self):
        """Average length of all edges in the surface.
        """
        adj = self.adj
        tadj = sparse.triu(adj, 1) # only entries above main diagonal, in coo format
        edgelens = np.sqrt(((self.pts[tadj.row] - self.pts[tadj.col])**2).sum(1))
        return edgelens.mean()

    def surface_gradient(self, scalars, at_verts=True):
        """Gradient of a function with values `scalars` at each vertex on the surface.
        If `at_verts`, returns values at each vertex. Otherwise, returns values at each
        face.

        Parameters
        ----------
        scalars : 1D ndarray, shape (total_verts, )
            A scalar-valued function across the cortex.
        at_verts : bool, optional
            If True (default), values will be returned for each vertex. Otherwise, 
            values will be retruned for each face.

        Returns
        -------
        gradu : 2D ndarray, shape (total_verts, 3) or (total_polys, 3)
            Contains the x-, y-, and z-axis gradients of the given `scalars` at either
            each vertex (if `at_verts` is True) or each face.
        """
        pu = scalars[self.polys]
        fe12, fe23, fe31 = [f.T for f in self._facenorm_cross_edge]
        pu1, pu2, pu3 = pu.T
        fa = self.face_areas

        # numexpr is much faster than doing this using numpy!
        #gradu = ((fe12.T * pu[:, 2] +
        #          fe23.T * pu[:, 0] +
        #          fe31.T * pu[:, 1]) / (2 * self.face_areas)).T
        gradu = np.nan_to_num(ne.evaluate("(fe12 * pu3 + fe23 * pu1 + fe31 * pu2) / (2 * fa)").T)
        
        if at_verts:
            return (self.connected.dot(gradu).T / self.connected.sum(1).A.squeeze()).T
        return gradu

    def _create_biharmonic_solver(self, boundary_verts, clip_D=0.1):
        """Set up biharmonic equation with Dirichlet boundary conditions on the cortical
        mesh and precompute Cholesky factorization for solving it. The vertices listed in
        `boundary_verts` are considered part of the boundary, and will not be included in
        the factorization.

        To facilitate Cholesky decomposition (which requires a symmetric matrix), the
        squared Laplace-Beltrami operator is separated into left-hand-side (L2) and
        right-hand-side (Dinv) parts. If we write the L-B operator as the product of
        the stiffness matrix (V-W) and the inverse mass matrix (Dinv), the biharmonic
        problem is as follows (with `\b` denoting non-boundary vertices)

        .. math::
        
            L^2_{\\b} \phi = -\rho_{\\b} \\
            \left[ D^{-1} (V-W) D^{-1} (V-W) \right]_{\\b} \phi = -\rho_{\\b} \\
            \left[ (V-W) D^{-1} (V-W) \right]_{\\b} \phi = -\left[D \rho\right]_{\\b}

        Parameters
        ----------
        boundary_verts : list or ndarray of length V
            Indices of vertices that will be part of the Dirichlet boundary.

        Returns
        -------
        lhs : sparse matrix
            Left side of biharmonic problem, (V-W) D^{-1} (V-W)
        rhs : sparse matrix, dia
            Right side of biharmonic problem, D
        Dinv : sparse matrix, dia
            Inverse mass matrix, D^{-1}
        lhsfac : cholesky Factor object
            Factorized left side, solves biharmonic problem
        notboundary : ndarray, int
            Indices of non-boundary vertices
        """
        try:
            from sksparse.sparse.cholmod import cholesky
        except ImportError:
            from scikits.sparse.cholmod import cholesky
        B, D, W, V = self.laplace_operator
        npt = len(D)

        g = np.nonzero(D > 0)[0] # Find vertices with non-zero mass
        #g = np.nonzero((L.sum(0) != 0).A.ravel())[0] # Find vertices with non-zero mass
        notboundary = np.setdiff1d(np.arange(npt)[g], boundary_verts) # find non-boundary verts
        D = np.clip(D, clip_D, D.max())

        Dinv = sparse.dia_matrix((D**-1, [0]), (npt, npt)).tocsr() # construct Dinv
        L = Dinv.dot((V-W)) # construct Laplace-Beltrami operator
        
        lhs = (V-W).dot(L) # construct left side, almost squared L-B operator
        lhsfac = cholesky(lhs[notboundary][:, notboundary]) # factorize
        
        return lhs, D, Dinv, lhsfac, notboundary

    def _create_interp(self, verts, bhsolver=None):
        """Creates interpolator that will interpolate values at the given `verts` using
        biharmonic interpolation.

        Parameters
        ----------
        verts : 1D array-like of ints
            Indices of vertices that will serve as knot points for interpolation.
        bhsolver : (lhs, rhs, Dinv, lhsfac, notboundary), optional
            A 5-tuple representing a biharmonic equation solver. This structure
            is created by _create_biharmonic_solver.
        
        Returns
        -------
        _interp : function
            Function that will interpolate a given set of values across the surface.
            The values can be 1D or 2D (number of dimensions by len `verts`). Any
            number of dimensions can be interpolated simultaneously.
        """
        if bhsolver is None:
            lhs, D, Dinv, lhsfac, notb = self._create_biharmonic_solver(verts)
        else:
            lhs, D, Dinv, lhsfac, notb = bhsolver
        
        npt = len(D)
        def _interp(vals):
            """Interpolate function with values `vals` at the knot points."""
            v2 = np.atleast_2d(vals)
            nd, nv = v2.shape
            ij = np.zeros((2, nv*nd))
            ij[0] = np.array(verts)[np.repeat(np.arange(nv), nd)]
            ij[1] = np.tile(np.arange(nd), nv)
            
            r = sparse.csr_matrix((vals.T.ravel(), ij), shape=(npt, nd))
            vr = lhs.dot(r)
            
            #phi = lhsfac.solve_A(-vr.todense()[notb]) # 29.9ms
            phi = lhsfac.solve_A(-vr[notb].todense()) # 28.2ms
            # phi = lhsfac.solve_A(-vr[notb]).todense() # 29.3ms
            
            tphi = np.zeros((npt, nd))
            tphi[notb] = phi
            tphi[verts] = v2.T
            
            return tphi

        return _interp

    def interp(self, verts, vals):
        """Interpolates a function between N knot points `verts` with the values `vals`.
        `vals` can be a D x N array to interpolate multiple functions with the same
        knot points.

        Using this function directly is unnecessarily expensive if you want to interpolate
        many different values between the same knot points. Instead, you should directly
        create an interpolator function using _create_interp, and then call that function.
        In fact, that's exactly what this function does.

        See _create_biharmonic_solver for math details.

        Parameters
        ----------
        verts : 1D array-like of ints
            Indices of vertices that will serve as knot points for interpolation.
        vals : 2D ndarray, shape (dimensions, len(verts))
            Values at the knot points. Can be multidimensional.

        Returns
        -------
        tphi : 2D ndarray, shape (total_verts, dimensions)
            Interpolated value at every vertex on the surface.
        """
        return self._create_interp(verts)(vals)

    @property
    @_memo
    def _facenorm_cross_edge(self):
        ppts = self.ppts
        fnorms = self.face_normals
        fe12 = np.cross(fnorms, ppts[:, 1] - ppts[:, 0])
        fe23 = np.cross(fnorms, ppts[:, 2] - ppts[:, 1])
        fe31 = np.cross(fnorms, ppts[:, 0] - ppts[:, 2])
        return fe12, fe23, fe31

    def geodesic_distance(self, verts, m=2.0, fem=False):
        """Minimum mesh geodesic distance (in mm) from each vertex in surface to any
        vertex in the collection `verts`.

        Geodesic distance is estimated using heat-based method (see 'Geodesics in Heat', 
        Crane et al, 2012). Diffusion of heat along the mesh is simulated and then
        used to infer geodesic distance. The duration of the simulation is controlled
        by the parameter `m`. Larger values of `m` will smooth & regularize the distance
        computation. Smaller values of `m` will roughen and will usually increase error
        in the distance computation. The default value of 1.0 is probably pretty good.

        This function caches some data (sparse LU factorizations of the laplace-beltrami
        operator and the weighted adjacency matrix), so it will be much faster on
        subsequent runs.

        The time taken by this function is independent of the number of vertices in verts.

        Parameters
        ----------
        verts : 1D array-like of ints
            Set of vertices to compute distance from. This function returns the shortest
            distance to any of these vertices from every vertex in the surface.
        m : float, optional
            Reverse Euler step length. The optimal value is likely between 0.5 and 1.5.
            Default is 1.0, which should be fine for most cases.
        fem : bool, optional
            Whether to use Finite Element Method lumped mass matrix. Wasn't used in 
            Crane 2012 paper. Doesn't seem to help any.

        Returns
        -------
        dist : 1D ndarray, shape (total_verts, )
            Geodesic distance (in mm) from each vertex in the surface to the closest
            vertex in `verts`.
        """
        npt = len(self.pts)
        if m not in self._rlfac_solvers:
            B, D, W, V = self.laplace_operator
            nLC = W - V # negative laplace matrix
            if not fem:
                spD = sparse.dia_matrix((D, [0]), (npt, npt)).tocsr() # lumped mass matrix
            else:
                spD = B
            
            t = m * self.avg_edge_length ** 2 # time of heat evolution
            lfac = spD - t * nLC # backward Euler matrix

            # Exclude rows with zero weight (these break the sparse LU, that finicky fuck)
            goodrows = np.nonzero(~np.array(lfac.sum(0) == 0).ravel())[0]
            self._goodrows = goodrows
            self._rlfac_solvers[m] = sparse.linalg.dsolve.factorized(lfac[goodrows][:, goodrows])
            self._nLC_solvers[m] = sparse.linalg.dsolve.factorized(nLC[goodrows][:, goodrows])

        # Solve system to get u, the heat values
        u0 = np.zeros((npt, )) # initial heat values
        u0[verts] = 1.0
        goodu = self._rlfac_solvers[m](u0[self._goodrows])
        u = np.zeros((npt, ))
        u[self._goodrows] = goodu

        # Compute grad u at each face
        gradu = self.surface_gradient(u, at_verts=False)
        
        # Compute X (normalized grad u)
        #X = np.nan_to_num((-gradu.T / np.sqrt((gradu**2).sum(1))).T)
        graduT = gradu.T
        gusum = ne.evaluate("sum(gradu ** 2, 1)")
        X = np.nan_to_num(ne.evaluate("-graduT / sqrt(gusum)").T)

        # Compute integrated divergence of X at each vertex
        ppts = self.ppts
        #x1 = x2 = x3 = np.zeros((X.shape[0], ))
        c32, c13, c21 = self._cot_edge
        x1 = 0.5 * (c32 * X).sum(1)
        x2 = 0.5 * (c13 * X).sum(1)
        x3 = 0.5 * (c21 * X).sum(1)
        
        conn1, conn2, conn3 = self._polyconn
        divx = conn1.dot(x1) + conn2.dot(x2) + conn3.dot(x3)

        # Compute phi (distance)
        goodphi = self._nLC_solvers[m](divx[self._goodrows])
        phi = np.zeros((npt, ))
        phi[self._goodrows] = goodphi - goodphi.min()

        # Ensure that distance is zero for selected verts
        phi[verts] = 0.0

        return phi

    @property
    @_memo
    def _cot_edge(self):
        ppts = self.ppts
        cots1, cots2, cots3 = self.cotangent_weights
        c3 = cots3[:, np.newaxis] * (ppts[:, 1] - ppts[:, 0])
        c2 = cots2[:, np.newaxis] * (ppts[:, 0] - ppts[:, 2])
        c1 = cots1[:, np.newaxis] * (ppts[:, 2] - ppts[:, 1])
        c32 = c3 - c2
        c13 = c1 - c3
        c21 = c2 - c1
        return c32, c13, c21

    @property
    @_memo
    def _polyconn(self):
        npt = len(self.pts)
        npoly = len(self.polys)
        o = np.ones((npoly, ))
        c1 = sparse.coo_matrix((o, (self.polys[:, 0], range(npoly))), (npt, npoly)).tocsr()
        c2 = sparse.coo_matrix((o, (self.polys[:, 1], range(npoly))), (npt, npoly)).tocsr()
        c3 = sparse.coo_matrix((o, (self.polys[:, 2], range(npoly))), (npt, npoly)).tocsr()
        return c1, c2, c3

    @property
    @_memo
    def graph(self):
        """NetworkX undirected graph representing this Surface.
        """
        import networkx as nx
        def iter_surfedges(tris):
            for a, b, c in tris:
                yield a, b
                yield b, c
                yield a, c

        def make_surface_graph(tris):
            graph = nx.Graph()
            graph.add_edges_from(iter_surfedges(tris))
            return graph

        return make_surface_graph(self.polys)
    # ML additions:
    #@property
    #@_memo
    # Don't want _memo, b/c input k makes it complicated...?
    def evecs(self, k=None):
        B, D, W, V = self.laplace_operator
        A = V-W
        if k is None:
            # All eigenvectors of LBO
            n = int(len(self.pts)-1)
        else:
            n = k
        evals, evecs = la.eigsh(A, M=B, k=n, which="SM")
        return evals, evecs

    def evec_varexp(self, nevs=None):
        """Compute the amount of variance in vertex position explained by each LBO eigenvector

        STILL WIP. Unclear how best to turn this into a measure of variance explained. Currently
        it's just error, which is not a great way to do it, and also seems broken...
        """
        if nevs is None:
            nevs = len(self.pts)-1
        # Possibly too expensive w/ large meshes...
        eigvals, eigvecs = self.evecs(k=nevs)
        print("-- done computing eigenvalues --")
        pt_cov = np.cov(self.pts)
        varexp = np.zeros((nevs, ))
        for n in range(nevs):
            newpts = self.reconstruct_evecs(n, eigvecs=eigvecs)
            if n%5==0:
                print('done with %d reconstructions'%n)
            # Possibly too expensive w/ large meshes:
            reconst_cov = np.cov(newpts.todense()) 
            # Compare newpts to pts
            varexp[n] = 1-(np.var(reconst_cov-pt_cov)/np.var(pt_cov))
        return varexp

    def _map_colors(self, v, cmap=None):
        """Normalize a vector to 0-1, apply colormap to it, return list of colors"""
        if cmap is None:
            from matplotlib import cm
            cmap = cm.RdBu_r
        v -= np.min(v)
        v /= np.max(v)
        return cmap(v)

    def _set_vertex_colors(self, col_list, name='Col'):
        """Set mesh vertex colors to a specified color"""
        from matplotlib import cm
        # Get mesh
        me = self.ob.data 
        # Get vertex color
        me.vertex_colors.new(name=name)
        color_layer = me.vertex_colors[name]
        i = 0
        for poly in me.polygons:
            for idx in poly.vertices: #loop_indices:
                color_layer.data[i].color = col_list[idx, :3]
                i += 1

    def show_evecs(self, nevs=5, cmap=None, evs=None):
        if evs is None:
            evals, evs = self.evecs(k=nevs) # evals, evecs = 
            #evs = evecs[:, :nevs]
        else:
            evs = evs[:, :nevs]
        for iv, v in enumerate(evs.T):
            clist = self._map_colors(v, cmap=cmap)
            self._set_vertex_colors(clist, 'EigenVec #%d'%iv)

    def reconstruct_evecs(self, n, eigvecs=None, opt='a'):
        if eigvecs is None:
            eigvals, eigvecs = self.evecs(k=n)
        pts_sp = sparse.csr_matrix(self.pts)
        ev_sp = sparse.csr_matrix(eigvecs)
        B, D, W, V = self.laplace_operator
        if opt=='a':
            #c = (v' * B)* evecs(:, 1:Nmax) # matlab code
            c = (pts_sp.T.dot(B)).dot(ev_sp[:, :n])
            #vsmooth = evecs(:, 1:Nmax) * c'; # matlab code
            newpts = ev_sp[:, :n].dot(c.T)
        elif opt=='b':
            ev2 = ev_sp[:, :n].dot(ev_sp[:, :n].T)
            newpts = ev2.dot(B.T).dot(pts_sp)
        return newpts

    def add_shapekey(self, newpts, name='key', relative_to=None):
        """Add a shape key to a given the shape's blender object (self.shape), with vertices in 
        position newpts (newpts is a list of vertices as long as self.pts)"""
        # Check for 'basis' shape key?
        self.ob.shape_key_add(name=name)
        skey = self.ob.data.shape_keys.key_blocks[name]
        for iv, loc in enumerate(newpts):
            skey.data[iv].co = bmu.Vector(loc)
        if relative_to is not None:
            skey.relative_key=self.ob.data.shape_keys.key_blocks[relative_to]

    def triangulate(self):
        """Make sure mesh is triangular, and thus amenable to manifold shape analysis

        This is a BLENDER OPERATOR.
        """
        # Set mode to object mode?
        # Object must be in the current scene to apply modifiers.
        bpy.context.scene.objects.link(self.ob)
        grab_only(self.ob)
        bpy.context.scene.update() # unnecessary?
        # Create & apply modifier
        self.ob.modifiers.new('tri', 'TRIANGULATE')
        self.ob.modifiers['tri'].quad_method = 'BEAUTY' # do it the slow, pretty way
        self.ob.modifiers['tri'].ngon_method = 'BEAUTY' # do it the slow, pretty way
        bpy.ops.object.modifier_apply(modifier='tri', apply_as='DATA')
        # Un-link again (?)
        bpy.context.scene.objects.unlink(self.ob)

    #/ML additions
    def get_graph(self):
        return self.graph

    def extract_chunk(self, nfaces=100, seed=None, auxpts=None):
        '''Extract a chunk of the surface using breadth first search, for testing purposes'''
        node = seed
        if seed is None:
            node = np.random.randint(len(self.pts))

        ptmap = dict()
        queue = [node]
        faces = set()
        visited = set([node])
        while len(faces) < nfaces and len(queue) > 0:
            node = queue.pop(0)
            for face in self.connected[node].indices:
                if face not in faces:
                    faces.add(face)
                    for pt in self.polys[face]:
                        if pt not in visited:
                            visited.add(pt)
                            queue.append(pt)

        pts, aux, polys = [], [], []
        for face in faces:
            for pt in self.polys[face]:
                if pt not in ptmap:
                    ptmap[pt] = len(pts)
                    pts.append(self.pts[pt])
                    if auxpts is not None:
                        aux.append(auxpts[pt])
            polys.append([ptmap[p] for p in self.polys[face]])

        if auxpts is not None:
            return np.array(pts), np.array(aux), np.array(polys)

        return np.array(pts), np.array(polys)

    def polyhedra(self, wm):
        '''Iterates through the polyhedra that make up the closest volume to a certain vertex'''
        for p, facerow in enumerate(self.connected):
            faces = facerow.indices
            pts, polys = _ptset(), _quadset()
            if len(faces) > 0:
                poly = np.roll(self.polys[faces[0]], -np.nonzero(self.polys[faces[0]] == p)[0][0])
                assert pts[wm[p]] == 0
                assert pts[self.pts[p]] == 1
                pts[wm[poly[[0, 1]]].mean(0)]
                pts[self.pts[poly[[0, 1]]].mean(0)]

                for face in faces:
                    poly = np.roll(self.polys[face], -np.nonzero(self.polys[face] == p)[0][0])
                    a = pts[wm[poly].mean(0)]
                    b = pts[self.pts[poly].mean(0)]
                    c = pts[wm[poly[[0, 2]]].mean(0)]
                    d = pts[self.pts[poly[[0, 2]]].mean(0)]
                    e = pts[wm[poly[[0, 1]]].mean(0)]
                    f = pts[self.pts[poly[[0, 1]]].mean(0)]

                    polys((0, c, a, e))
                    polys((1, f, b, d))
                    polys((1, d, c, 0))
                    polys((1, 0, e, f))
                    polys((f, e, a, b))
                    polys((d, b, a, c))

            yield pts.points, np.array(list(polys.triangles))

    def patches(self, auxpts=None, n=1):
        def align_polys(p, polys):
            x, y = np.nonzero(polys == p)
            y = np.vstack([y, (y+1)%3, (y+2)%3]).T
            return polys[np.tile(x, [3, 1]).T, y]

        def half_edge_align(p, pts, polys):
            poly = align_polys(p, polys)
            mid   = pts[poly].mean(1)
            left  = pts[poly[:, [0, 2]]].mean(1)
            right = pts[poly[:, [0, 1]]].mean(1)
            s1 = np.array(np.broadcast_arrays(pts[p], mid, left)).swapaxes(0, 1)
            s2 = np.array(np.broadcast_arrays(pts[p], mid, right)).swapaxes(0, 1)
            return np.vstack([s1, s2])

        def half_edge(p, pts, polys):
            poly = align_polys(p, polys)
            mid   = pts[poly].mean(1)
            left  = pts[poly[:, [0, 2]]].mean(1)
            right = pts[poly[:, [0, 1]]].mean(1)
            stack = np.vstack([mid, left, right, pts[p]])
            return stack[(distance.cdist(stack, stack) == 0).sum(0) == 1]

        for p, facerow in enumerate(self.connected):
            faces = facerow.indices
            if len(faces) > 0:
                if n == 1:
                    if auxpts is not None:
                        pidx = np.unique(self.polys[faces])
                        yield np.vstack([self.pts[pidx], auxpts[pidx]])
                    else:
                        yield self.pts[self.polys[faces]]
                elif n == 0.5:
                    if auxpts is not None:
                        pts = half_edge(p, self.pts, self.polys[faces])
                        aux = half_edge(p, auxpts, self.polys[faces])
                        yield np.vstack([pts, aux])
                    else:
                        yield half_edge_align(p, self.pts, self.polys[faces])
                else:
                    raise ValueError
            else:
                yield None

    def edge_collapse(self, p1, p2, target):
        raise NotImplementedError
        face1 = self.connected[p1]
        face2 = self.connected[p2]


# ? 
class _ptset(object):
    def __init__(self):
        self.idx = OrderedDict()
    def __getitem__(self, idx):
        idx = tuple(idx)
        if idx not in self.idx:
            self.idx[idx] = len(self.idx)
        return self.idx[idx]

    @property
    def points(self):
        return np.array(list(self.idx.keys()))

# ? 
class _quadset(object):
    def __init__(self):
        self.polys = dict()

    def __call__(self, quad):
        idx = tuple(sorted(quad))
        if idx in self.polys:
            del self.polys[idx]
        else:
            self.polys[idx] = quad

    @property
    def triangles(self):
        for quad in list(self.polys.values()):
            yield quad[:3]
            yield [quad[0], quad[2], quad[3]]



def tetra_vol(pts):
    '''Volume of a tetrahedron'''
    tetra = pts[1:] - pts[0]
    return np.abs(np.dot(tetra[0], np.cross(tetra[1], tetra[2]))) / 6

def brick_vol(pts):
    '''Volume of a triangular prism'''
    return tetra_vol(pts[[0, 1, 2, 4]]) + tetra_vol(pts[[0, 2, 3, 4]]) + tetra_vol(pts[[2, 3, 4, 5]])

def sort_polys(polys):
    amin = polys.argmin(1)
    xind = np.arange(len(polys))
    return np.array([polys[xind, amin], polys[xind, (amin+1)%3], polys[xind, (amin+2)%3]]).T

def face_area(pts):
    '''Area of triangles

    Parameters
    ----------
    pts : array_like
        n x 3 x 3 array with n triangles, 3 pts, and (x, y, z) coordinates
    '''
    return 0.5 * np.sqrt((np.cross(pts[:, 1]-pts[:, 0], pts[:, 2]-pts[:, 0])**2).sum(1))

def face_volume(pts1, pts2, polys):
    '''Volume of each face in a polyhedron sheet'''
    vols = np.zeros((len(polys), ))
    for i, face in enumerate(polys):
        vols[i] = brick_vol(np.append(pts1[face], pts2[face], axis=0))
        if i % 1000 == 0:
            print(i)
    return vols

def decimate(pts, polys):
    from tvtk.api import tvtk
    pd = tvtk.PolyData(points=pts, polys=polys)
    dec = tvtk.DecimatePro(input=pd)
    dec.set(preserve_topology=True, splitting=False, boundary_vertex_deletion=False, target_reduction=1.0)
    dec.update()
    dpts = dec.output.points.to_array()
    dpolys = dec.output.polys.to_array().reshape(-1, 4)[:, 1:]
    return dpts, dpolys

def inside_convex_poly(pts):
    """Returns a function that checks if inputs are inside the convex hull of polyhedron defined by pts

    Alternative method to check is to get faces of the convex hull, then check if each normal is pointed away from each point.
    As it turns out, this is vastly slower than using qhull's find_simplex, even though the simplex is not needed.
    """
    tri = Delaunay(pts)
    return lambda x: tri.find_simplex(x) != -1

def make_cube(center=(.5, .5, .5), size=1):
    pts = np.array([(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0), 
                    (0, 0, 1), (1, 0, 1), (0, 1, 1), (1, 1, 1)], dtype=float)
    pts -= (.5, .5, .5)
    polys = np.array([(0, 2, 3), (0, 3, 1), (0, 1, 4), (1, 5, 4), 
                      (1, 3, 5), (3, 7, 5), (2, 7, 3), (2, 6, 7), 
                      (0, 6, 2), (0, 4, 6), (4, 7, 6), (4, 5, 7)], dtype=np.uint32)
    return pts * size + center, polys

def boundary_edges(polys):
    '''Returns the edges that are on the boundary of a mesh, as defined by belonging to only 1 face'''
    # AKA non-manifold edges? 
    edges = dict()
    for i, poly in enumerate(np.sort(polys)):
        for a, b in [(0, 1), (1, 2), (0, 2)]:
            key = poly[a], poly[b]
            if key not in edges:
                edges[key] = []
            edges[key].append(i)

    epts = []
    for edge, faces in edges.items():
        if len(faces) == 1:
            epts.append(edge)

    return np.array(epts)

def trace_poly(edges):
    '''Given a disjoint set of edges, yield complete linked polygons'''
    idx = dict((i, set([])) for i in np.unique(edges))
    for i, (x, y) in enumerate(edges):
        idx[x].add(i)
        idx[y].add(i)

    eset = set(range(len(edges)))
    while len(eset) > 0:
        eidx = eset.pop()
        poly = list(edges[eidx])
        stack = set([eidx])
        while poly[-1] != poly[0] or len(poly) == 1:
            next = list(idx[poly[-1]] - stack)[0]
            eset.remove(next)
            stack.add(next)
            if edges[next][0] == poly[-1]:
                poly.append(edges[next][1])
            elif edges[next][1] == poly[-1]:
                poly.append(edges[next][0])
            else:
                raise Exception

        yield poly

def rasterize(poly, shape=(256, 256)):
    #ImageDraw sucks at its job, so we'll use imagemagick to do rasterization
    import subprocess as sp
    import cStringIO
    import shlex
    from PIL import Image
    
    polygon = " ".join(["%0.3f, %0.3f"%tuple(p[::-1]) for p in np.array(poly)-(.5, .5)])
    cmd = 'convert -size %dx%d xc:black -fill white -stroke none -draw "polygon %s" PNG32:-'%(shape[0], shape[1], polygon)
    proc = sp.Popen(shlex.split(cmd), stdout=sp.PIPE)
    png = cStringIO.StringIO(proc.communicate()[0])
    im = Image.open(png)

    # For PNG8:
    # mode, palette = im.palette.getdata()
    # lut = np.fromstring(palette, dtype=np.uint8).reshape(-1, 3)
    # if (lut == 255).any():
    #     white = np.nonzero((lut == 255).all(1))[0][0]
    #     return np.array(im) == white
    # return np.zeros(shape, dtype=bool)
    return (np.array(im)[:, :, 0] > 128).T

def voxelize(pts, polys, shape=(256, 256, 256), center=(128, 128, 128), mp=True):
    from tvtk.api import tvtk
    from PIL import Image, ImageDraw
    
    pd = tvtk.PolyData(points=pts + center + (0, 0, 0), polys=polys)
    plane = tvtk.Planes(normals=[(0, 0, 1)], points=[(0, 0, 0)])
    clip = tvtk.ClipPolyData(clip_function=plane, input=pd)
    feats = tvtk.FeatureEdges(
        manifold_edges=False, 
        non_manifold_edges=False, 
        feature_edges=False, 
        boundary_edges=True, 
        input=clip.output)

    def func(i):
        plane.points = [(0, 0, i)]
        feats.update()
        vox = np.zeros(shape[:2][::-1], np.uint8)
        if feats.output.number_of_lines > 0:
            epts = feats.output.points.to_array()
            edges = feats.output.lines.to_array().reshape(-1, 3)[:, 1:]
            for poly in trace_poly(edges):
                vox += rasterize(epts[poly][:, :2]+[.5, .5], shape=shape[:2][::-1])
        return vox % 2

    if mp:
        from . import mp
        layers = mp.map(func, range(shape[2]))
    else:
        layers = map(func, range(shape[2]))

    return np.array(layers).T

def measure_volume(pts, polys):
    from tvtk.api import tvtk
    pd = tvtk.PolyData(points=pts, polys=polys)
    mp = tvtk.MassProperties(input=pd)
    return mp.volume

### MARK(ish) CODE ###

def _computeAB(pts, polys):
    """Finds the A and B terms for Laplace-Beltrami eigendecomposition...
    
    Based on M. Reuter's tutorial code in Matlab, available at 
    Ok yeah I have no idea what I'm doing but let's see if this works.
    Parameters
    ----------
    pts : array [n x 3]
        vertex locations in 3D
    polys : array [n x 3]
        indices into `pts` per polygon; max entry should be len(pts)
    """

    npts = pts.shape[0]
    npolys = polys.shape[0]
    #vdeg = accumarray(polys(:), 1) # Original matlab code
    vdeg = np.bincount(polys.flatten()) # FAIRLY SURE this is the correct python analog
    maxdeg = np.max(vdeg)
    
    A = sparse.coo_matrix((npts, npts))
    B = sparse.coo_matrix((npts, npts))
    # linear local matrices on unit triangle:
    tB = (np.ones((3, 3)) + np.eye(3) ) / 24.0

    tA00 = np.array([[ 0.5, -0.5,  0.0], 
                     [-0.5,  0.5,  0.0], 
                     [ 0.0,  0.0,  0.0]])
     
    tA11 = np.array([[ 0.5,  0.0, -0.5], 
                     [0.0,  0.0,  0.0], 
                     [-0.5,  0.0,  0.5]])
        
    tA0110 = np.array([[ 1.0, -0.5, -0.5], 
                       [-0.5,  0.0,  0.5], 
                       [-0.5,  0.5,  0.0]])
    # Loop over polygons
    for ti in range(npolys):
        # get polygon indices
        i1, i2, i3 = polys[ti]
        # get vertex locations 
        v1 = pts[i1, :]
        v2 = pts[i2, :]
        v3 = pts[i3, :]
        # define two vectors for two sides of the triangle
        v2mv1 = v2-v1;
        v3mv1 = v3-v1;
        # (not third side? no.)
        # get local matrices for this polygon ("element" in original code)
        a0 = v3mv1.dot(v3mv1.T)
        a1 = v2mv1.dot(v2mv1.T)
        a0110 = v2mv1.dot(v3mv1.T)
        cr = np.cross(v2mv1, v3mv1)
        vol = np.linalg.norm(cr, 2)
        # MATRIX OR SCALAR?
        localB = vol * tB
        localA = (1.0/vol) * (a0*tA00 + a1*tA11 - a0110 * tA0110)
        # Add locally-computed operators to global matrices:
        xcoo, ycoo = np.meshgrid([i1, i2, i3], [i1, i2, i3])
        localAsparse = sparse.coo_matrix((localA.flatten(), (ycoo.flatten(), xcoo.flatten())), shape=(npts, npts))
        localBsparse = sparse.coo_matrix((localB.flatten(), (ycoo.flatten(), xcoo.flatten())), shape=(npts, npts))
        A = A + localAsparse
        B = B + localBsparse
    # Change sparse matrix format to optimize computation rather than construction:
    A = A.tocsr()
    B = B.tocsr()
    return A, B


# def get_evecs(ob, k=None):
# 	"""Get eigenvectors and eigenvalues of Laplace-Beltrami operator for a manifold mesh object.

# 	k is the number of eigenvectors to compute.

# 	"""
# 	pts, polys = pts_polys(ob)
# 	# Make shape object from 
# 	A, B = _computeAB(pts, polys)
# 	if k is None:
# 		n = int(len(pts)*.8)
# 	else:
# 		n = k
# 	evals, evecs = la.eigsh(A, M=B, k=n, which="SM")
# 	return evals, evecs




def construct_evecs(ob, evecs, B, n):
    pts, polys = pts_polys(ob)
    #c = (v' * B)* evecs(:, 1:Nmax) # matlab code
    c = (pts.T.dot(B)).dot(evecs[:, :n])
    #vsmooth = evecs(:, 1:Nmax) * c'; # matlab code
    newpts = evecs[:, :n].dot(c.T)

    # or: 
    ev2 = evecs[:, :n].dot(evecs[:, :n].T)
    newpts = ev2.dot(B.T).dot(pts)
    # Add as a shape key
    #if ob.data.shape_keys is None:
    #	ob.shape_key_add(name='Basis')
    nm = "%d eigenvectors"%n
    ob.shape_key_add(name=nm)
    skey = ob.data.shape_keys.key_blocks[nm]
    for iv, loc in enumerate(newpts):
        skey.data[iv].co = bmu.Vector(loc)

def make_vertex_color_material(ob):
	# start in object mode
	raise NotImplementedError('WORK IN PROGRESS!')
	"""
	Currently example code from http://blenderscripting.blogspot.nl/2013/03/vertex-color-map.html
	"""
	my_object = bpy.data.objects['Cube'].data
	color_map_collection = my_object.vertex_colors
	if len(color_map_collection) == 0:
	    color_map_collection.new()
	 
	"""
	let us assume for sake of brevity that there is now 
	a vertex color map called  'Col'    
	"""
	 
	color_map = color_map_collection['Col']
	 
	# or you could avoid using the vertex color map name
	# color_map = color_map_collection.active  
	 
	i = 0
	for poly in my_object.polygons:
	    for idx in poly.loop_indices:
	        rgb = [random.random() for i in range(3)]
	        color_map.data[i].color = rgb
	        i += 1
	 
	mat = bpy.data.materials.new('vertex_material')
	mat.use_vertex_color_paint = True
	mat.use_vertex_color_light = True  # material affected by lights
	 
	my_object.materials.append(mat)

def show_ica(ob, ):
	pass

# Test script:
"""
from bvp.utils import shape
ob = C.object
pts, polys = shape.pts_polys(ob)
A, B = shape._computeAB(pts, polys)
evals, evecs = shape.get_evecs(ob)


# reconstruction by eigenvectors
for n in [4, 5, 6, 7, 8, 9, 10]: #, 16, 32, 64, 128, 512]:
	shape.construct_evecs(ob, evecs, B, n)
	if n == 4:
		old_nm = 'Basis'
	nm = '%d eigenvectors'%n
	ob.data.shape_keys.key_blocks[nm].relative_key=ob.data.shape_keys.key_blocks[old_nm]
	old_nm = nm


# animate eigenvectors
fr = 31
nsec_per_ev = 1
fs = 30
for t, k in enumerate(list(ob.data.shape_keys.key_blocks)[1:]): # skip basis
	k.value = 0.0
	k.keyframe_insert('value', frame=fr+t*fs)
	k.value = 1.0
	k.keyframe_insert('value', frame=fr+(t+1)*fs)

# colors
nevs = 4
for nevs in range(6):
	cmap = shape.map_colors(evecs[:, nevs-1])
	shape.set_vertex_colors(ob, cmap, name='eigenvector %d'%nevs)

# TO DO: Make vertex color materials
# There seems to be a limit of 6 vertex color groups (?) per mesh


# Look into ICA:
http://scikit-learn.org/dev/auto_examples/decomposition/plot_ica_blind_source_separation.html

Also currently working on getting Blender running w/ system python. 
Failing, but working on it.

remove .../python/(lib/python3.X) from Blender app

# Set blender system python environment variable:
export BLENDER_SYSTEM_PYTHON="/Users/mark/anaconda/envs/py34" # NOT THIS PART:/lib/python3.4/"

found bundled python: /Users/mark/anaconda/envs/py34 # STOP HERE! before lib/pythonX.X/...


"""