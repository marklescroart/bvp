"""
Class for general constraints on random distributions. 
"""
# Imports
import sys
import copy
import random
import numpy as np
import bvp.utils as bvpu
from bvp.Classes.object import Object # Should this be here...? Unclear. 

verbosity_level = 3

class Constraint(object):
    """General class to hold constraints on position, etc"""
    def __init__(self, X=None):
        """General constraints (Mean, Std, Min, Max) on random distributions (rectangular or normal)

        See sample_w_constr() for usage. Superordinate class for PosConstriant, ObConstraint, CamConstraint.

        """
        self.X = X

    def sample_w_constr(self, mu=None, sigma=None, mn=None, mx=None):
        """Get random sample given mean, std, min, max.

        Parameters
        ----------
        mu : scalar
            mean of distribution
        sigma : scalar
            standard deviation of distribution
        mn : scalar
            minimum of distribution
        mx : scalar
            max of distribution
        
        Notes
        -----
        If Mean (Input[0]) is None, returns uniform random sample, Min <= x <= Max
        If Mean is not None, returns x ~N(Mean, Std), Min <= x <= Max

        """
        if all([mu is None, mn is None, mx is None]):
            raise ValueError('Insufficient constraints specified')
        if mu is None:
            n = np.random.uniform(low=mn, high=mx)
        else:
            if mx is None:
                mx = np.inf
            if mn is None:
                mn = -np.inf
            if sigma is None:
                sigma = 1.0
            n = np.random.normal(loc=mu, scale=sigma)
            n = np.clip(n, mn, mx)
        return n

class PosConstraint(Constraint):
    """General constraint on 3D position"""
    def __init__(self, X=None, Y=None, Z=None, theta=None, phi=None, r=None, origin=(0., 0., 0.)):
        """Class to store 3D position constraints for objects / cameras / whatever in Blender.

        All inputs (X, Y, ...) are 4-element tuples: (Mean, Std, Min, Max)
        For rectangular X, Y, Z constraints, only specify X, Y, and Z
        For spherical constraints, only specify theta, phi, and r 
        XYZ constraints, if present, override spherical constraints
        """
        super(PosConstraint, self).__init__(X)
        # Set all inputs as class properties
        inpt = locals()
        for i in inpt.keys():
            if not i=='self':
                setattr(self, i, inpt[i])
        
    #def constr2xyz(self, ConstrObj):
    def sampleXYZ(self):
        """
        Sample one position (X, Y, Z) from position distribution given spherical / XYZ constraints

        XYZ constraint will override spherical constraints if they are present.

        ML 2012.01.31
        """
        if not self.X and not self.theta:
            raise Exception('Ya hafta provide either rectangular or spherical constraints on the distribution of positions!')
        # Calling this within Blender, code should never get to here - location should be defined
        if not self.X:
            theta_offset = 270 # To make angles in Blender more interpretable
            # Use spherical constraints  ## THETA AND PHI MAY BE BACKWARDS FROM CONVENTION!! as is its, theta is Azimuth, phi is elevation
            if not self.theta:
                theta = np.random.rand()*360.
            else:
                theta = self.sample_w_constr(*self.theta)+theta_offset
            phi = self.sample_w_constr(*self.phi)
            r = self.sample_w_constr(*self.r)
            # Constrain position
            x, y, z = bvpu.math.sph2cart(r, theta, phi) # w/ theta, phi in degrees
            x = x+self.origin[0]
            y = y+self.origin[1]
            z = z+self.origin[2]
        else:
            # Use XYZ constraints:
            x = self.sample_w_constr(*self.X)
            y = self.sample_w_constr(*self.Y)
            z = self.sample_w_constr(*self.Z)
        # Check for obstacles! 
        return x, y, z      

class ObConstraint(PosConstraint):
    """Constraints on objects, specifically"""
    def __init__(self, X=None, Y=None, Z=None, 
                theta=(None, None, 0., 360.), phi=(0., 0., 0., 0.), r=(0., 5., -25., 25.), 
                origin=(0., 0., 0.), sz=(6., 1., 3., 10.), Zrot=(None, None, -180., 180.)):
        """Class to store 3D position constraints for objects

        All inputs (X, Y, ...) are 4-element lists: [Mean, Std, Min, Max]
        For rectangular X, Y, Z constraints, only specify X, Y, and Z
        For spherical constraints, only specify theta, phi, and r 

        "obstacles" is a list of Objects (with a size and position) that 
        are to be avoided in positioning objects

        ML 2012.10
        """
        self.type = 'ObConstraint'
        super(ObConstraint, self).__init__(X=X, Y=Y, Z=Z, theta=theta, phi=phi, r=r, origin=origin)
        # Set all inputs as class properties
        inpt = locals()
        for i in inpt.keys():
            if not i=='self':
                setattr(self, i, inpt[i])
    
    def checkXYZS_3D(self, obj, obstacles=None, check_bounds=True):
        """Verify that a particular position and size is acceptable given 
        `obstacles` and the position constraints of this object (in 3-D). 
        
        Parameters
        ----------
        obj : bvp.Object
            the object being placed
        obstacles : list
            list of bvp.Object instances to specify positions of obstacles to avoid
        
        Returns
        -------
        BGboundOK = boolean; True if XYZpos is within boundary constraints
        ObDistOK = boolean; True if XYZpos does not overlap with other objects/obstacles 
        """
        # (1) Check distance from allowable object position boundaries (X, Y, and/or r)
        bg_bound_ok_3d = [True, True, True, True]
        if check_bounds:
            minXYZpos = obj.min_xyz_pos
            maxXYZpos = obj.max_xyz_pos
            Sz = obj.size3D
            tolerance_factor = 5
            X_OK, Y_OK, r_OK, Z_OK = True, True, True, True # True by default
            #TODO: What is the correct way to take object size into account?
            if self.X:
                xA = True if self.X[2] is None else (minXYZpos[0]>=self.X[2])
                xB = True if self.X[3] is None else (maxXYZpos[0]<=self.X[3])
                X_OK = xA and xB
            if self.Y:
                yA = True if self.Y[2] is None else (minXYZpos[1]>=self.Y[2])
                yB = True if self.Y[3] is None else (maxXYZpos[1]<=self.Y[3])
                Y_OK = yA and yB
            if self.Z:
                if self.Z[2] == self.Z[3]:
                    zA = True if self.Z[2] is None else (minXYZpos[2] >= self.Z[2]-Sz/tolerance_factor)
                    zB = True if self.Z[2] is None else (maxXYZpos[2] <= self.Z[3] + self.Sz[3] - Sz)
                else:
                    zA = True if self.Z[2] is None else (minXYZpos[2]>=self.Z[2]-Sz/tolerance_factor)
                    zB = True if self.Z[3] is None else (maxXYZpos[2]<=self.Z[3])
                Z_OK = (zA and zB)
            if self.r:
                oX, oY, oZ = self.origin
                maxR = ((maxXYZpos[0]-oX)**2 + (maxXYZpos[1]-oY)**2 + (maxXYZpos[2]-oZ)**2)**.5
                minR = ((minXYZpos[0]-oX)**2 + (minXYZpos[1]-oY)**2 + (minXYZpos[2]-oZ)**2)**.5
                rA = True if self.r[2] is None else (minR)>=self.r[2]
                rB = True if self.r[3] is None else (maxR)<=self.r[3]
                r_OK = rA and rB
            bg_bound_ok_3d = [X_OK, Y_OK, Z_OK, r_OK] # all([...])
        # (2) Check distance from other objects in 3D
        if obstacles is not None:
            n_obj = len(obstacles)
        else:
            n_obj = 0
        ob_dist_ok_3d = [True] * n_obj
        for c in range(n_obj):
            # print(obstacles[c])
            ob_dist_ok_3d[c] = not obj.collides_with(obstacles[c])
        return bg_bound_ok_3d, ob_dist_ok_3d

    def checkXYZS_2D(self, obj, camera, obstacles=None, edge_dist=0., object_overlap=50.):
        """
        Verify that a particular position and size is acceptable given "obstacles" obstacles and 
        the position constraints of this object (in 2D images space). 
        
        Inputs:
            obj = the object being placed
            camera = Camera object (for computing perspective)
            obstacles = list of "Object" instances to specify positions of obstacles to avoid
            edge_dist = proportion of object that can go outside of the 2D image (0.-100.)
            object_overlap = proportion of object that can overlap with other objects (0.-100.)
        Returns:
            ImBoundOK = boolean; True if 2D projection of XYZpos is less than (edge_dist) outside of image boundary 
            ObDistOK = boolean; True if 2D projection of XYZpos overlaps less than (object_overlap) with other objects/obstacles 
        """
        # (TODO: Make flexible for edge_dist, object_overlap being 0-1 or 0-100?)
        #TODO: Currently only looks at object one_wall_distances in the first frame. It is computationally hard, and possibly unnecessary to check it for every frame.
        edge_ok_list = []
        obdst_ok_list = []
        ob_positions = obj.xyz_trajectory
        num_frames = len(ob_positions)
        cam_frames_idx = np.floor(np.linspace(0, camera.frames[-1], num_frames, endpoint = True)).astype(np.int) #select 5 equally spaced camera frames
        cam_fix_location = list(np.array([np.linspace(camera.fix_location[0][i], camera.fix_location[-1][i],camera.frames[-1]) for i in range(3)]).T) #interpolate cam fixation location for those frames
        cam_location = list(np.array([np.linspace(camera.location[0][i], camera.location[-1][i], camera.frames[-1]) for i in range(3)]).T) #same for camera position
               
        for frame_num in range(num_frames):
            object_pos = ob_positions[frame_num]
            tmp_ob = Object(pos3D=object_pos, size3D=obj.size3D)
            tmp_ip_top, tmp_ip_bot, tmp_ip_L, tmp_ip_r = bvpu.math.perspective_projection(object_pos, 
                            cam_location[frame_num],
                            cam_fix_location[frame_num], 
                            camera_lens=camera.lens,
                            image_size=(100, 100),)
            TmpObSz_X = abs(tmp_ip_r[0]-tmp_ip_L[0])
            TmpObSz_Y = abs(tmp_ip_bot[1]-tmp_ip_top[1])
            Tmpimage_position = [np.mean([tmp_ip_r[0], tmp_ip_L[0]]), np.mean([tmp_ip_bot[1], tmp_ip_top[1]])]
            ### --- (1) Check distance from screen edges --- ###
            top_OK = edge_dist < tmp_ip_top[1]
            Bot_OK = 100-edge_dist > tmp_ip_bot[1]
            L_OK = edge_dist < tmp_ip_L[0]
            R_OK = 100-edge_dist > tmp_ip_r[0]
            edge_ok_2d = all([top_OK, Bot_OK, L_OK, R_OK])
            ### --- (2) Check distance from other objects in 2D --- ###
            if obstacles:
                n_obj = len(obstacles)
            else:
                n_obj = 0
            obstPos2D_List = []
            Dist_List = []
            Dthresh_List = []
            ObstSz_List = []
            ob_dist_ok_2d = [True for x in range(n_obj)]
            for c in range(n_obj):
                # Get position of obstacle
                obstIP_top, obstIP_Bot, obstIP_L, obstIP_r = bvpu.math.perspective_projection(obstacles[c], camera, image_size=(1., 1.))
                obstSz_X = abs(obstIP_r[0]-obstIP_L[0])
                obstSz_Y = abs(obstIP_Bot[1]-obstIP_top[1])
                obstPos2D = [np.mean([obstIP_r[0], obstIP_L[0]]), np.mean([obstIP_Bot[1], obstIP_top[1]])]
                ObstSz2D = np.mean([obstSz_X, obstSz_Y])
                ObjSz2D = np.mean([TmpObSz_X, TmpObSz_Y])
                # Note: this is an approximation! But we're ok for now (2012.10.08) with overlap being a rough measure
                PixDstThresh = (ObstSz2D/2. + ObjSz2D/2.) - (min([ObjSz2D, ObstSz2D]) * object_overlap)
                ob_dist_ok_2d[c] = bvpu.math.vecDist(Tmpimage_position, obstPos2D) > PixDstThresh
                # For debugging
                obstPos2D_List.append(obstPos2D) 
                Dist_List.append(bvpu.math.vecDist(Tmpimage_position, obstPos2D))
                Dthresh_List.append(PixDstThresh)
                ObstSz_List.append(ObstSz2D)
            edge_ok_list.append(edge_ok_2d)
            obdst_ok_list.append(ob_dist_ok_2d)
        return all(edge_ok_list), [all([obdst_ok[i] for obdst_ok in obdst_ok_list]) for i in range(len(obdst_ok_list[0]))]

    def check_size_2d(self, Obj, camera, min_size_2d):
        """Check whether (projected) 2D size of objects meets a minimum size criterion         
        """
        tmp_ip_top, tmp_ip_bot, tmp_ip_L, tmp_ip_r = bvpu.math.perspective_projection(Obj, camera, image_size=(1., 1.))
        TmpObSz_X = abs(tmp_ip_r[0]-tmp_ip_L[0])
        TmpObSz_Y = abs(tmp_ip_bot[1]-tmp_ip_top[1])
        SzOK_2D = sum([TmpObSz_X, TmpObSz_Y])/2. > min_size_2d
        return SzOK_2D

    def sampleXYZ(self, obj, camera, obstacles=None, edge_dist=0., object_overlap=50., raise_error=False, n_iter=100, min_size_2d=0.):
        """Randomly sample object positions across the 3D space of a scene

        ... given constraints (in 3D) on that scene and the position of a camera.
        Currently only works for first frame! 

        Takes into account the size of the object to be positioned as 
        well as (optionally) the size and location of obstacles (other 
        objects) in the scene.

        Parameters
        ----------
        obj = the object being placed
        camera = Camera object
        obstacles = list of Objects to be avoided 
        edge_dist = Proportion of object by which objects must avoid the
            image border. Default=0 (touching edge is OK) Specify as a
            proportion (e.g., .1, .2, etc). Negative values mean that it
            is OK for objects to go off the side of the image. 
        object_overlap = Proportion of image by which objects must avoid 
            the centers of other objects. Default = 50 (50% of 2D 
            object size)
        raise_error = option to raise an error if no position can be found.
            default is False, which causes the function to return None
            instead of a position. Other errors will still be raised if 
            they occur.
        n_iter = number of attempts to make at finding a scene arrangement
            that works with constraints.
        min_size_2d = minimum size of an object in 2D, given as proportion of screen (0-1)
        
        Returns
        ------- 
        Position (x, y, z)

        NOTE: sampleXY (sampling across image space, but w/ 3D constraints)
        is currently (2012.02.22) the preferred method! (see NOTES in code)
        
        """


        """
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

        #TODO: May be broken as of 2016/09/27 
        """
        #Compute
        Sz = obj.size3D
        XYZpos = obj.pos3D
        TooClose = True
        Iter = 1
        if obstacles:
            n_obj = len(obstacles)
        else:
            n_obj = 0
        while TooClose and Iter<n_iter:
            if verbosity_level > 9:
                print("--------- Iteration %d ---------"%Iter)
            # Draw random position to start:
            c = copy.copy
            kws = dict((k, getattr(self, k).copy()) for k in ['X', 'Y', 'Z', 'r', 'theta', 'phi'])
            tmpC = PosConstraint(**kws)
            # change x, y position (and/or radius) limits to reflect the size of the object 
            # (can't come closer to limit than Sz/2)
            ToLimit = ['X', 'Y', 'r']
            for pNm in ToLimit:
                value = getattr(tmpC, pNm)
                if value: # (?) if any(value): (?)
                    if value[2]:
                        value[2]+=Sz/2. # increase min by Sz/2
                    if value[3]:
                        value[3]-=Sz/2. # decrease max by Sz/2
                print(pNm + '='+ str(value))
                setattr(tmpC, pNm, value)
            tmp_pos = tmpC.sampleXYZ()
            bound_ok_3d, ob_dist_ok_3d = self.checkXYZS_3D(obj, obstacles=obstacles)
            edge_ok_2d, ob_dist_ok_2d = self.checkXYZS_2D(obj, camera, obstacles=obstacles, edge_dist=edge_dist, object_overlap=object_overlap)
            SzOK_2D = self.check_size_2d(obj, camera, min_size_2d)
            if all(ob_dist_ok_3d) and all(ob_dist_ok_2d) and all(bound_ok_3d) and edge_ok_2d:
                TooClose = False
                tmp_ob = obj
                tmp_ip_top, tmp_ip_bot, tmp_ip_L, tmp_ip_r = bvpu.math.perspective_projection(tmp_ob, camera, image_size=(1., 1.))
                image_position = [np.mean([tmp_ip_r[0], tmp_ip_L[0]]), np.mean([tmp_ip_bot[1], tmp_ip_top[1]])]
                return tmp_pos, image_position
            else:
                if verbosity_level > 9:
                    Reason = ''
                    if not all(ob_dist_ok_3d):
                        Add = 'Bad 3D Dist!\n'
                        for iO, O in enumerate(obstacles):
                            Add += 'Dist %d = %.2f, Sz = %.2f\n'%(iO, bvpu.math.vecDist(tmp_pos, O.pos3D), O.size3D)
                        Reason += Add
                    if not all(ob_dist_ok_2d):
                        Add = 'Bad 2D Dist!\n'
                        for iO, O in enumerate(obstacles):
                            Add+= 'Dist %d: %s to %s\n'%(iO, str(obstPos2D_List[iO]), str(Tmpimage_position))
                        Reason+=Add
                    if not edge_ok_2d:
                        Reason+='Edge2D bad!\n%s\n'%(str([top_OK, Bot_OK, L_OK, R_OK]))
                    if not SzOK_2D:
                        Reason+='Object too small / size ratio bad!'
                    print('Rejected for:\n%s'%Reason)
            Iter += 1
        # Raise error if n_iter is reached
        if Iter==n_iter:
            if raise_error:
                raise Exception('Iterated %d x without finding good position!'%n_iter)
            else: 
                return None, None
    def sampleXY(self, obj, camera, obstacles=None, image_position_count=None, edge_dist=0., object_overlap=.50, raise_error=False, n_iter=100, min_size_2d=0.):
        """
        Usage: sampleXY(Sz, camera, obstacles=None, image_position_count=None, edge_dist=0., object_overlap=.50, raise_error=False, n_iter=100, min_size_2d=0.)

        Randomly sample across the 2D space of the image, given object 
        constraints (in 3D) on the scene and the position of a camera*.
        Takes into account the size of the object to be positioned as 
        well as (optionally) the size and location of obstacles (other 
        objects) in the scene.

        * Currently only for first frame! (2012.02.19)

        Inputs: 
        obj = object being placed
        camera = Camera object
        obstacles = list of Objects to be avoided 
        image_position_count = Class that keeps track of which image positions have been sampled 
            already. Can be omitted for single scenes.
        edge_dist = Proportion of object by which objects must avoid the
            image border. Default=0 (touching edge is OK) Specify as a
            proportion (e.g., .1, .2, etc). Negative values mean that it
            is OK for objects to go off the side of the image. 
        object_overlap = Proportion of image by which objects must avoid 
            the centers of other objects. Default = .50 (50% of 2D 
            object size)
        raise_error = option to raise an error if no position can be found.
            default is False, which causes the function to return None
            instead of a position. 
        n_iter = number of attempts to make at finding a scene arrangement
            that works with constraints.

        Outputs: 
        Position (x, y, z), ImagePosition (x, y)

        NOTE: This is currently (2012.08) the preferred method for sampling
        object positions in a scene. See notes in sampleXYZ for more.
        
        ML 2012.02
        """
        #Compute
        if not image_position_count:
            image_position_count = bvpu.math.image_positionCount(0, 0, image_size=1., n_bins=5, e=1)
        TooClose = True
        Iter = 1
        if obstacles:
            n_obj = len(obstacles)
        else:
            n_obj = 0
        while TooClose and Iter<n_iter:
            if verbosity_level > 9: 
                print("--------- Iteration %d ---------"%Iter)
            #TODO adjust uniform sampling to work with object trajectory position; currently only looks at initial state.
            #Zbase = self.sampleXYZ(Sz, camera)[2]
            Zbase = self.origin[2]
            Sz = obj.size3D
            # Draw random (x, y) image position to start:
            image_position = image_position_count.sampleXY() 
            oPosZ = bvpu.math.perspective_projection_inv(image_position, 
                                                         camera.location[0], 
                                                         camera.fix_location[0],
                                                         Z=100,
                                                         camera_fov=None,
                                                         camera_lens=camera.lens,)
            oPosUp = bvpu.math.line_plane_intersection(camera.location[0], oPosZ, P0=(0, 0, Zbase+Sz/2.))
            tmp_pos = oPosUp
            tmp_pos[2] -= Sz/2.
            tmp_ob = Object(pos3D=tmp_pos, size3D=Sz, action = obj.action)
            # Check on 3D bounds
            bound_ok_3d, ob_dist_ok_3d = self.checkXYZS_3D(tmp_ob, obstacles=obstacles)
           # bound_ok_3d = [True for i in bound_ok_3d] #Adding these for debugging purposes. Make sure to remove later
            # Check on 2D bounds
            #TODO Insert loop here that checks tmpOb cam compatibility at different points
            edge_ok_2d, ob_dist_ok_2d = self.checkXYZS_2D(tmp_ob, camera, obstacles=obstacles, edge_dist=edge_dist, object_overlap=object_overlap)
            # Instantiate temp object and...
            # ... check on 2D size

            SzOK_2D = self.check_size_2d(tmp_ob, camera, min_size_2d)

            if all(ob_dist_ok_3d) and all(ob_dist_ok_2d) and edge_ok_2d and all(bound_ok_3d) and SzOK_2D:
                TooClose = False
                tmp_pos = bvpu.basics.make_blender_safe(tmp_pos, 'float')
                if verbosity_level > 7:
                    print('\nFinal image positions:')
                    for ii, dd in enumerate(obstPos2D_List):
                        print('ObPosX, Y=(%.2f, %.2f), ObstPosX, Y=%.2f, %.2f, D=%.2f'%(Tmpimage_position[1], Tmpimage_position[0], dd[1], dd[0], Dist_List[ii]))
                        print('ObSz = %.2f, ObstSz = %.2f, Dthresh = %.2f\n'%(ObjSz2D, ObstSz_List[ii], Dthresh_List[ii]))
                return tmp_pos, image_position
            else:
                if verbosity_level > 9000: #TODO: Temporarily disabled because it is outdated, and breaks things
                    Reason = ''
                    if not all(ob_dist_ok_3d):
                        Add = 'Bad 3D Dist!\n'
                        for iO, O in enumerate(obstacles):
                            Add += 'Dist %d = %.2f, Sz = %.2f\n'%(iO, bvpu.math.vecDist(tmp_pos, O.pos3D), O.size3D)
                        Reason += Add
                    if not all(ob_dist_ok_2d):
                        Add = 'Bad 2D Dist!\n'
                        for iO, O in enumerate(obstacles):
                            Add+= 'Dist %d: %s to %s\n'%(iO, str(obstPos2D_List[iO]), str(Tmpimage_position))
                        Reason+=Add
                    if not edge_ok_2d:
                        Reason+='Edge2D bad!\n%s\n'%(str([top_OK, Bot_OK, L_OK, R_OK]))
                    if not EdgeOK_3D:
                        Reason+='Edge3D bad! (Object(s) out of bounds)'
                    if not SzOK_2D:
                        Reason+='Object too small / size ratio bad! '
                    print('Rejected for:\n%s'%Reason)
            Iter += 1
        # Raise error if n_iter is reached
        if Iter==n_iter:
            if raise_error:
                raise Exception('MaxAttemptReached', 'Iterated %d x without finding good position!'%n_iter)
            else:
                if verbosity_level > 3:
                    print('Warning! Iterated %d x without finding good position!'%n_iter)
                else:
                    sys.stdout.write('.')
                return None, None
    def sampleSize(self):
        """
        sample size from self.Sz
        """
        Sz = self.sample_w_constr(*self.Sz)
        return Sz
    def sampleRot(self, camera=None):
        """
        sample rotation from self.zRot (only rotation around Z axis for now!)
        If "camera" argument is provided, rotation is constrained to be within 90 deg. of camera!
        """
        if not camera is None:
            import random
            vector_fn = bvpu.math.vector_fn
            # Get vector from fixation->camera
            cVec = vector_fn(camera.fix_location[0])-vector_fn(camera.location[0])
            # Convert to X, Y, Z Euler angles
            x, y, z = bvpu.math.vector_to_eulerxyz(cVec)
            if round(np.random.rand()):
                posNeg=1
            else:
                posNeg=-1
            zRot = z + np.random.rand()*90.*posNeg
            zRot = bvpu.math.bnp.radians(zRot)
        else:
            zRot = self.sample_w_constr(*self.zRot)
        return (0, 0, zRot)


class CamConstraint(PosConstraint):
    """Constraints to specify camera & fixation position"""
    def __init__(self, 
        r=(30., 3., 20., 40.), 
        theta=(0., 60., -135., 135.), 
        phi=(17.5, 2.5, 12.5, 45.5), 
        origin=(0., 0., 0.), 
        X=None, 
        Y=None, 
        Z=None, 
        fixX=(0., 1., -3., 3.), 
        fixY=(0., 3., -3., 3.), 
        fixZ=(2., .5, .0, 3.5), 
        speed=(3., 1., 0., 6.), 
        max_path_angle=30,
        pan=True, 
        zoom=True):
        """
        Extension of PosConstraint to have:/
        *camera speed (measured in Blender Units*) per second, takes fps as input
        *pan / zoom constraints (True/False for whether pan/zoom are allowed)

        for pan, constrain radius
        for zoom, constrain theta and phi
        ... and draw another position


        NOTES: 

        What circle positions mean in Blender space, from the -y perspective @x=0 :
                      (+y)
                      90
                135         45
            180                 0  (or 360)
                225         315
                      270
                      (-y)
        THUS: to achieve 0 at dead-on (top position from -y), subtract 270 from all thetas
        """
        inpt = locals()
        for k, v in inpt.items():
            if not k=='self':
                setattr(self, k, v)

    def __repr__(self):
        S = 'CamConstraint:\n'+self.__dict__.__repr__()
        return(S)

    def sample_fixation_location(self, frames=None, obj=None, method='mean'):
        """
        Sample fixation positions. Returns a list of (X, Y, Z) position tuples, nFrames long

        TO DO: 
        More constraints? max angle to change wrt camera? fixation change speed constraints?
        """
        #TODO : Why did this break?
        fix_location = list()
        for ii in range(len(frames)):
            # So far: No computation of how far apart the frames are, so no computation of how fast the fixation point is moving. ADD??
            if not obj:
                Tmpfix_location = (self.sample_w_constr(*self.fixX), self.sample_w_constr(*self.fixY), self.sample_w_constr(*self.fixZ))
            else:
                if method == 'mean':
                    ObPos = [o.bounding_box_center for o in obj]
                    ObDims = [o.bounding_box_dimensions for o in obj]
                    posX = sum([x[0]*y[0] for x,y in zip(ObPos, ObDims)])/sum([y[0] for y in ObDims])
                    posY = sum([x[1]*y[1] for x,y in zip(ObPos, ObDims)])/sum([y[1] for y in ObDims])
                    Tmpfix_location = (posX, posY, self.sample_w_constr(*self.fixZ))
                else:
                    ObPos = [o.pos3D for o in obj]
                    ObPosX = [None, None, min([x[0] for x in ObPos]), max([x[0] for x in ObPos])] # (Mean, Std, Min, Max) for sample_w_constr
                    ObPosY = [None, None, min([x[1] for x in ObPos]), max([x[1] for x in ObPos])]
                    #ObPosZ = [None, None, min([x[2] for x in ObPos]), max([x[2] for x in ObPos])] # use if we ever decide to do floating objects??
                    Tmpfix_location = (self.sample_w_constr(ObPosX), self.sample_w_constr(ObPosY), self.sample_w_constr(*self.fixZ))
            # Necessary??
            #Tmpfix_location = tuple([a+b for a, b in zip(Tmpfix_location, self.origin)])
            fix_location.append(Tmpfix_location)
        return fix_location

    def sample_camera_location(self, frames=None, fps=15, n_attempts=1000, n_samples=500):
        """Sample a new camera position given constraints on position and movement

        Parameters
        ----------
        frames : list
            list of frames at which to sample a new camera location
        fps : scalar, int
            desired frame rate of movie
        n_attempts : scalar, int
            number of attempts to try to get a whole trajectory
        n_samples : scalar, int
            number of positions to sample for each frame to find an acceptable next frame within the constraints

        Returns
        -------
        List of (x, y, z) positions for each keyframe in "frames"

        Notes
        -----
        Only tested up to 2 frames (i.e., len(frames)==2) as of 2012.02.15
        """
        theta_offset = 270.
        failed = True
        ct = 0
        while failed and ct < n_attempts:
            location = []
            ct+=1
            for ifr, fr in enumerate(frames):
                if ifr==0: 
                    # For first frame, simply get a position
                    tmp_pos = self.sampleXYZ()
                else:
                    newR, newTheta, newPhi = bvpu.math.cart2sph(tmp_pos[0]-self.origin[0], tmp_pos[1]-self.origin[1], tmp_pos[2]-self.origin[2])
                    if verbosity_level > 5: 
                        print('computed first theta to be: %.3f'%(newTheta))
                    newTheta = bvpu.math.circ_dist(newTheta - theta_offset, 0.)
                    if verbosity_level > 5: 
                        print('changed theta to: %.3f'%(newTheta))
                    """ All bvpu.math.cart2sph need update with origin!! """
                    if self.speed is not None:
                        # Compute n_samples positions in a circle around last position
                        # If speed has a distribution, this will potentially allow for multiple possible positions
                        radii_from_original_pos = [self.sample_w_constr(*self.speed) * (fr-frames[ifr-1]) / fps for x in range(n_samples)]
                        # cpos will give potential new positions at allowable radii around original position
                        cpos = bvpu.math.circle_pos(radii_from_original_pos, n_samples, tmp_pos[0], tmp_pos[1]) # Gives x, y; z will be same
                        if (self.max_path_angle is not None) and (ifr > 1):
                            # Optionally smooth angle trajectory
                            vector = np.array(location[ifr-1]) - np.array(location[ifr-2])
                            current_angle = np.degrees(np.arctan2(*vector[:2]))
                            theta_min = current_angle - self.max_path_angle
                            theta_max = current_angle + self.max_path_angle
                            cpos = bvpu.math.arc_pos(radii_from_original_pos, n_samples, theta_min, theta_max, tmp_pos[0], tmp_pos[1]) # Gives x, y; z will be same
                        if self.X:
                            # Remove sampled new positions if they don't satisfy original Cartesian constraints:
                            old_pos = location[ifr-1]
                            new_xyz = [np.hstack([xy, old_pos[2]]) for xy in cpos if (self.X[2]<=xy[0]<=self.X[3]) and (self.Y[2]<=xy[1]<=self.Y[3])]
                            # Convert to spherical coordinates for later computations to allow zoom / pan
                            nPosSphBl = [bvpu.math.cart2sph(*xyz, origin=self.origin) for xyz in new_xyz]
                            nPosSphCs = [[xx[0], bvpu.math.circ_dist(xx[1]-theta_offset, 0.), xx[2]] for xx in nPosSphBl]
                        elif self.theta:
                            # Convert circle coordinates to spherical coordinates (for each potential new position)
                            # "Bl" denotes un-corrected Blender coordinate angles (NOT intuitive angles, which are the units for constraints)
                            nPosSphBl = [bvpu.math.cart2sph(cpos[ii][0], cpos[ii][1], location[ifr-1][2], origin=self.origin) for ii in range(n_samples)]
                            # returns r, theta, phi
                            # account for theta offset in original conversion from spherical to cartesian
                            # "Cs" means this is now converted to units of constraints
                            nPosSphCs = [[xx[0], bvpu.math.circ_dist(xx[1]-theta_offset, 0.), xx[2]] for xx in nPosSphBl]
                            # Clip new positions if they don't satisfy original spherical constraints
                            nPosSphCs = [xx for xx in nPosSphCs if (self.r[2]<=xx[0]<=self.r[3]) and (self.theta[2]<=xx[1]<=self.theta[3]) and (self.phi[2]<=xx[2]<=self.phi[3])]
                            # We are now left with a list of positions in spherical coordinates that are the 
                            # correct distance away and in permissible positions wrt the original constraints
                    else: 
                        # If no speed is specified, just sample from original distribution again
                        new_xyz = [self.sampleXYZ() for x in range(n_samples)]
                        nPosSphBl = [bvpu.math.cart2sph(*xyz, origin=self.origin) for xyz in new_xyz]
                        nPosSphCs = [[xx[0], bvpu.math.circ_dist(xx[1]-theta_offset, 0.), xx[2]] for xx in nPosSphBl]
                    
                    # Now filter sampled positions (nPosSphCs) by pan/zoom constraints
                    if not self.pan and not self.zoom:
                        # Repeat same position
                        pPosSphBl = [bvpu.math.cart2sph(location[ifr-1][0]-self.origin[0], location[ifr-1][1]-self.origin[1], location[ifr-1][2]-self.origin[2])]
                        pPosSphCs = [[xx[0], bvpu.math.circ_dist(xx[1]-theta_offset, 0.), xx[2]] for xx in pPosSphBl]
                    elif self.pan and self.zoom:
                        # Any movement is possible; all positions up to now are fine
                        pPosSphCs = nPosSphCs
                    elif not self.pan and self.zoom:
                        # Constrain theta within some wiggle range
                        WiggleThresh = 3. # permissible azimuth angle variation for pure zooms, in degrees
                        thetaDist = [abs(newTheta-xx[1]) for xx in nPosSphCs]
                        pPosSphCs = [nPosSphCs[ii] for ii, xx in enumerate(thetaDist) if xx < WiggleThresh]
                    elif not self.zoom and self.pan:
                        # constrain r within some wiggle range
                        WiggleThresh = newR*.05 # permissible distance to vary in radius from center - 5% of original radius
                        rDist = [abs(newR-xx[0]) for xx in nPosSphCs]
                        pPosSphCs = [nPosSphCs[ii] for ii, xx in enumerate(rDist) if xx < WiggleThresh]             
                    else:
                        raise Exception('This is a sad state of affairs. This line should never be reached.')
                    
                    # Keep one sampled position or loop again if no samples
                    if len(pPosSphCs) == 0:
                        # No positions satisfy constraints!
                        break
                    else:
                        # Sample pPos (spherical coordinates for all possible new positions)    
                        r1, theta1, phi1 = random.choice(pPosSphCs)
                        tmp_pos = bvpu.math.sph2cart(r1, theta1+theta_offset, phi1, origin=self.origin)
                location.append(tmp_pos)
                if fr==frames[-1]:
                    failed=False
        if failed:
            raise Exception(['Could not find camera trajectory to match constraints!'])
        else:
            return location

# THIS SHOULD BE CONVERTED TO CLASS METHOD from_background(),  
# SEPARATELY FOR EACH TYPE OF CONSTRAINT.
def get_constraint(grp, LockZtoFloor=True): #self, bgLibDir='/auto/k6/mark/BlenderFiles/Scenes/'):
    """Get constraints on object & camera position for a particular background
    
    Parameters
    ----------


    * Camera constraints must have "cam" in their name
    * Object constraints must have "ob" in their name

    For Cartesian (XYZ) constraints: 
    * Empties must have "XYZ" in their name
    Interprets empty cubes as minima/maxima in XYZ
    Interprets empty spheres as means/stds in XYZ (not possible to have 
    non-circular Gaussians as of 2012.02)

    For polar (rho, phi, theta) constraints:
    * Empties must have "rho", "phi", or "theta" in their name, as well as _min
    Interprets empty arrows as 

    returns obConstraint, camConstraint

    TODO: 
    Camera focal length and clipping plane should be determined by "RealWorldSize" property 
    """
    if bpy.app.version < (2, 80,0):
        dtype = 'empty_draw_type'
    else:
        dtype = 'empty_display_type'
    # Get camera constraints
    ConstrType = [['cam', 'fix'], ['ob']]
    theta_offset = 270
    fn = [CamConstraint, ObConstraint]
    Out = list()
    for cFn, cTypeL in zip(fn, ConstrType):
        cParams = [dict()]
        for cType in cTypeL:
            cParams[0]['origin'] = [0, 0, 0]
            if cType=='fix':
                dimAdd = 'fix'
            else:
                dimAdd = ''
            ConstrOb = [o for o in grp.objects if o.type=='EMPTY' and cType in o.name.lower()] 
            # Size constraints (object only!)
            SzConstr =  [n for n in ConstrOb if 'size' in n.name.lower() and cType=='ob']
            if SzConstr:
                cParams[0]['Sz'] = [None, None, None, None]
            for sz in SzConstr:
                # obsize should be done with spheres! (min/max only for now!)
                if getattr(sz, dtype)=='SPHERE' and '_min' in sz.name:
                    cParams[0]['Sz'][2] = sz.scale[0]
                elif getattr(sz, dtype)=='SPHERE' and '_max' in sz.name:
                    cParams[0]['Sz'][3] = sz.scale[0]   
            # Cartesian position constraints (object, camera)
            XYZconstr = [n for n in ConstrOb if 'xyz' in n.name.lower()]
            if XYZconstr:
                print('Found XYZ cartesian constraints!')
                cParams = [copy.copy(cParams[0]) for r in range(len(XYZconstr))]
                
            for iE, xyz in enumerate(XYZconstr):
                for ii, dim in enumerate(['X', 'Y', 'Z']):
                    cParams[iE][dimAdd+dim] = [None, None, None, None]
                    if getattr(xyz, dtype)=='CUBE':
                        # Interpret XYZ cubes as minima / maxima
                        if dim=='Z' and cType=='ob' and LockZtoFloor:
                            # Lock to height of bottom of cube
                            cParams[iE][dimAdd+dim][2] = xyz.location[ii]-xyz.scale[ii] # min
                            cParams[iE][dimAdd+dim][3] = xyz.location[ii]-xyz.scale[ii] # max
                            cParams[iE]['origin'][ii] = xyz.location[ii]-xyz.scale[ii]
                        else:
                            cParams[iE][dimAdd+dim][2] = xyz.location[ii]-xyz.scale[ii] # min
                            cParams[iE][dimAdd+dim][3] = xyz.location[ii]+xyz.scale[ii] # max
                            cParams[iE]['origin'][ii] = xyz.location[ii]
                    elif getattr(xyz, dtype)=='SPHERE':
                        # Interpret XYZ spheres as mean / std
                        cParams[iE][dimAdd+dim][0] = xyz.location[ii] # mean
                        cParams[iE][dimAdd+dim][1] = xyz.scale[0] # std # NOTE! only 1 dim for STD for now!
            # Polar position constraints (object, camera)
            if cType=='fix':
                continue
                # Fixation can only have X, Y, Z constraints for now!
            pDims = ['r', 'phi', 'theta']
            # First: find origin for spherical coordinates. Should be sphere defining radius min / max:
            OriginOb = [o for o in ConstrOb if 'r_' in o.name.lower()]
            if OriginOb:
                rptOrigin = OriginOb[0].location
                if not all([o.location==rptOrigin for o in OriginOb]):
                    raise Exception('Inconsistent origins for spherical coordinates!')
                #rptOrigin = tuple(rptOrigin)
                cParams['origin'] = tuple(rptOrigin)
            
            # Second: Get spherical constraints wrt that origin
            for dim in pDims: #pDims = ['r', 'phi', 'theta']
                # Potentially problematic: IF xyz is already filled, fill nulls for all cParams in list of cParams
                for iE in range(len(cParams)):
                    cParams[iE][dimAdd+dim] = [None, None, None, None]
                    ob = [o for o in ConstrOb if dim in o.name.lower()]
                    for o in ob:
                        # interpret spheres or arrows w/ "_min" or "_max" in their name as limits
                        if '_min' in o.name.lower() and getattr(o, dtype)=='SINGLE_ARROW':
                            cParams[iE][dimAdd+dim][2] = xyz2constr(list(o.location), dim, rptOrigin)
                            if dim=='theta':
                                cParams[iE][dimAdd+dim][2] = circ_dist(cParams[iE][dimAdd+dim][2]-theta_offset, 0.)
                        elif '_min' in o.name.lower() and getattr(o, dtype)=='SPHERE':
                            cParams[iE][dimAdd+dim][2] = o.scale[0]
                        elif '_max' in o.name.lower() and getattr(o, dtype)=='SINGLE_ARROW':
                            cParams[iE][dimAdd+dim][3] = xyz2constr(list(o.location), dim, rptOrigin)
                            if dim=='theta':
                                cParams[iE][dimAdd+dim][3] = circ_dist(cParams[iE][dimAdd+dim][3]-theta_offset, 0.)
                        elif '_max' in o.name.lower() and getattr(o, dtype)=='SPHERE':
                            cParams[iE][dimAdd+dim][3] = o.scale[0]
                        elif getattr(o, dtype)=='SPHERE':
                            # interpret sphere w/out "min" or "max" as mean+std
                            ## Interpretation of std here is a little fucked up: 
                            ## the visual display of the sphere will NOT correspond 
                            ## to the desired angle. But it should work.
                            cParams[iE][dimAdd+dim][0] = xyz2constr(list(o.location), dim, rptOrigin)
                            if dim=='theta':
                                cParams[iE][dimAdd+dim][0] = circ_dist(cParams[iE][dimAdd+dim][0]-theta_offset, 0.)
                            cParams[iE][dimAdd+dim][1] = o.scale[0]
                    if not any(cParams[iE][dimAdd+dim]):
                        # If no constraints are present, simply ignore
                        cParams[iE][dimAdd+dim] = None
        toAppend = [cFn(**cp) for cp in cParams]
        if len(toAppend)==1:
            toAppend = toAppend[0]
        Out.append(toAppend)
    return Out

"""Super duper WIP: need to refactor above code to extract constraints for each draw type

Sphere: if _min, get scale, map to max
        if _max, get scale, map to max
        if _meanstd, get ?? map to mean, std


"""

def _get_group_objects(grp):
    if bpy.app.version < (2, 80, 0):
        btype = bpy.types.Group
    else:
        btype = bpy.types.Collection
    if grp is None:
        ob_list = list(bpy.context.scene.objects)
    elif isinstance(grp, bpy.types.Object):
        # Test for existence of dupli group
        ob_list = list(grp.dupli_group.objects)
    elif isinstance(grp, btype):
        ob_list = list(grp.objects)
    else:
        raise ValueError("Unclear what to do with input of type {}".format(type(grp)))
    return ob_list


def _constraint_from_sphere(sphere, constraint_dict, param, constr):
    """Get constraints on position from empty sphere in a blender scene
    
    Parameters
    ----------
    sphere : empty object 
        Emtpy w/ draw type=='SPHERE'
    constraint_dict : dict
        dictionary of constraints so far
    param : string
        key to fill in for dictionary
    """

    value = sphere.scale[0]
    # Special cases
    if param == 'theta':
        value = circ_dist('wtf is this location?' - theta_offset, 0.)
    # Map min, max to size
    if constr == 'min':
        constraint_dict[param][2] = sphere.scale[0]
    elif constr == 'max':
        constraint_dict[param][3] = sphere.scale[0]
    elif constr == 'meanstd':
        # interpret sphere w/out "min" or "max" as mean+std
        # Interpretation of std here is a little confusing: 
        # the visual display of the sphere will NOT correspond 
        # to the desired angle. But it should work.
        # dim = X, Y, or Z; or r, phi, or theta
        #constraint_dict[dim] = xyz2constr(list(o.location), dim, rptOrigin)
        #if dim=='theta':
        #    constraint_dict[iE][dimAdd+dim][0] = value
        #constraint_dict[iE][dimAdd+dim][1] = o.scale[0]
        pass


def _constraint_from_cube(cube, constraint_dict, ctype=None):
    pass

def _constraint_from_arrow(arrow, constraint_dict, ctype=None):
    pass


_empty_mapping = dict(SPHERE=_constraint_from_sphere,
                      CUBE=_constraint_from_cube,
                      SINGLE_ARROW=_constraint_from_arrow,
                      )


def get_constraints(grp):
    if bpy.app.version < (2, 80,0):
        dtype = 'empty_draw_type'
    else:
        dtype = 'empty_display_type'
    constraints = dict(cam={}, fix={}, ob={})
    empties = [m for m in _get_group_objects(grp) if m.type=='EMPTY']
    # TODO: insert check for both spherical and cartesian constraints on objects, camera, or fixation
    for ce in empties:
        ctype, param, constr = ce.name.split('_')
        # e.g.: 'cam', 'theta', 'min'
        prefix = 'fix' if ctype=='fix' else ''
        constraints[ctype] = _empty_mapping[getattr(ce, dtype)](ce, constraints[ctype], param, constr, prefix=prefix)
    if isempty(constraints['ob']):
        ob = None
    else:
        ob = constraints['ob']
    if (isempty(constraints['fix']) and isempty(constraints['cam'])):
        cam = None
    else:
        cam = CamConstraint(**constraints['cam'], **constraints['fix'])
    return ob, cam


class SLConstraint(Constraint):
    """
    Class to contain constraints for properties of a scene list
    
    WIP
    """
    def __init__(self):
        """Computes concretely what will be in each scene and where. 

        Commits probabilities into instances.
        """
        pass
        '''

        Fields to set: 

        Minutes
        Seconds
        Scenes
        ScnList
        # Compute number of scenes / duration if not given
        # Build in check for inconsistencies?
        if not self.Minutes and not self.Seconds and not self.nScenes:
            raise Exception('Please specify either nScenes, Minutes, or Seconds')
        if not self.Minutes and not self.Seconds:
            self.Seconds = self.nScenes * self.sPerScene_mean
        if not self.Minutes:
            self.Minutes = self.Seconds / 60.
        if not self.Seconds:
            self.Seconds = self.Minutes * 60.
        if not self.nScenes:
            self.nScenes = bvpu.basics.make_blender_safe(np.floor(self.Seconds / self.sPerScene_mean))

        self.nObjectsPerCat = [len(o) for o in self.Lib.objects.values()]
        # Special case for humans with poses:
        nPoses = 5
        # TEMP!
        #print('Pre-increase of human cat:')
        #print(self.nObjectsPerCat)
        Categories = self.Lib.objects.keys()
        if "Human" in Categories:
            hIdx = Categories.index("Human")
            self.nObjectsPerCat[hIdx] = self.nObjectsPerCat[hIdx] * nPoses
        self.nObjects = sum(self.nObjectsPerCat)
        # TEMP!
        #print('Post-increase of human cat:')
        #print(self.nObjectsPerCat)

        self.nBGsPerCat = [len(bg) for bg in self.Lib.bgs.values()]
        self.nBGs = sum(self.nBGsPerCat)

        self.nSkiesPerCat = [len(s) for s in self.Lib.skies.values()]
        self.nSkies = sum(self.nSkiesPerCat)

        # Frames and objects per scene will vary with the task in any given experiment... 
        # for now, this is rather simple (i.e., we will not try to account for every task we might ever want to perform)
        # Scene temporal duration
        self.nFramesPerScene = np.random.randn(self.nScenes)*self.sPerScene_std + self.sPerScene_mean
        self.nFramesPerScene = np.minimum(self.nFramesPerScene, self.sPerScene_max)
        self.nFramesPerScene = np.maximum(self.nFramesPerScene, self.sPerScene_min)
        # Note conversion of seconds to frames 
        self.nFramesPerScene = bvpu.basics.make_blender_safe(np.round(self.nFramesPerScene * self.FrameRate))
        self.nFramesTotal = sum(self.nFramesPerScene)
        # Compute nFramesTotal to match Seconds exactly 
        while self.nFramesTotal < self.Seconds*self.FrameRate:
            self.nFramesPerScene[np.random.randint(self.nScenes)] += 1
            self.nFramesTotal = sum(self.nFramesPerScene)
        while self.nFramesTotal > self.Seconds*self.FrameRate:
            self.nFramesPerScene[np.random.randint(self.nScenes)] -= 1
            self.nFramesTotal = sum(self.nFramesPerScene)
        ### --- Scene Objects --- ###
        # Set object count per scene
        self.nObjPerScene = np.round(np.random.randn(self.nScenes)*self.nObj_std + self.nObj_mean) #self.nScenes
        self.nObjPerScene = np.minimum(self.nObjPerScene, self.nObj_max)
        self.nObjPerScene = np.maximum(self.nObjPerScene, self.nObj_min)
        self.nObjPerScene = bvpu.basics.make_blender_safe(self.nObjPerScene)
        # Set object categories per scene
        self.nObjectsUsed = bvpu.basics.make_blender_safe(np.sum(self.nObjPerScene))
        
        # Get indices for objects, bgs, skies by category (imaginary part), exemplar (real part) 
        # ??? NOTE: These functions can be replaced with different functions to sample from object, background, or sky categories differently...
        if not self.obIdx:
            obIdx = self.MakeListFromLib(Type='Obj')
        else:
            obIdx = self.obIdx
        if not self.bgIdx:
            bgIdx = self.MakeListFromLib(Type='BG')
        else:
            bgIdx = self.bgIdx
        if not self.skyIdx:
            skyIdx = self.MakeListFromLib(Type='Sky')
        else:
            skyIdx = self.skyIdx
        
        ### --- Get rendering options --- ###
        self.RenderOptions = RenderOptions(self.rParams)
        ### --- Create each scene (make concrete from probablistic constraints) --- ###
        self.ScnList = []
        #print('Trying to create %d Scenes'%self.nScenes)
        for iScn in range(self.nScenes):
            # Get object category / exemplar number
            ScOb = []
            for o in range(self.nObjPerScene[iScn]):
                if verbosity_level > 3: print('Running object number %d'%o)
                # This is a shitty way to do this - better would be a matrix. Fix??
                ObTmp = obIdx.pop(0) 
                if verbosity_level > 3: print('CatIdx = %d'%ObTmp.imag)
                if verbosity_level > 3: print('ObIdx = %d'%ObTmp.real)
                Cat = self.Lib.objects.keys()[int(ObTmp.imag)]
                if verbosity_level > 3: print(Cat)
                if Cat in PosedCategories:
                    obII = int(bvpu.floor(ObTmp.real/nPoses))
                    Pose = int(bvpu.mod(ObTmp.real, nPoses))
                else:
                    obII = int(ObTmp.real)
                    Pose = None
                grp, Fil = self.Lib.objects[Cat][obII]
                oParams = {
                    'categ':Cat, #bvpu.basics.make_blender_safe(ObTmp.imag), 
                    'exemp':grp, #bvpu.basics.make_blender_safe(ObTmp.real), 
                    'obFile':Fil, #self.obFiles, 
                    'obLibDir':os.path.join(self.Lib.LibDir, 'Objects'), #self.obLibDir, 
                    'pose':Pose, 
                    'rot3D':None, # Set??
                    'pos3D':None, # Set??
                    }
                # Update oparams w/ self.oparams for general stuff for this scene list?? (fixed size, location, rotation???)
                # Make Rotation wrt camera???
                ScOb.append(Object(oParams))
            
            # Get BG
            if bgIdx:
                Cat = self.Lib.bgs.keys()[int(bgIdx[iScn].imag)]
                grp, Fil = self.Lib.bgs[Cat][int(bgIdx[iScn].real)]
                bgParams = {
                    'categ':Cat, #bvpu.basics.make_blender_safe(bgIdx[iScn].imag), 
                    'exemp':grp, #bvpu.basics.make_blender_safe(bgIdx[iScn].real), 
                    'bgFile':Fil, 
                    'bgLibDir':os.path.join(self.Lib.LibDir, 'Backgrounds'), #self.bgLibDir, 
                    #'oParams':{}
                    }
                bgParams.update(self.bgParams)
                ScBG = Background(bgParams)
            else:
                # Create default BG (empty)
                ScBG = Background(self.bgParams)
                
            # Get Sky
            if skyIdx:
                Cat = self.Lib.skies.keys()[int(skyIdx[iScn].imag)]
                grp, Fil = self.Lib.skies[Cat][int(skyIdx[iScn].real)]          
                skyParams = {
                    'categ':Cat, #bvpu.basics.make_blender_safe(skyIdx[iScn].imag), 
                    'exemp':grp, #bvpu.basics.make_blender_safe(skyIdx[iScn].real), 
                    'skyLibDir':os.path.join(self.Lib.LibDir, 'Skies'), #self.skyLibDir, 
                    #'skyFiles':self.skyFiles, 
                    'skyFile':Fil
                    #'skyList':self.skyList, 
                    }
                skyParams.update(self.skyParams)
                ScSky = Sky(skyParams)
            else:
                # Create default sky
                ScSky = Sky(self.skyParams)
            # Get Camera
            # GET cParams from BG??? have to do that here???
            ScCam = Camera(self.cParams)
            # Timing
            self.ScnParams = fixedKeyDict({
                'frame_start':1, 
                'frame_end':self.nFramesPerScene[iScn]
                })
            newScnParams = {
                'Num':iScn+1, 
                'Obj':ScOb, 
                'BG':ScBG, 
                'Sky':ScSky, 
                'camera':ScCam, 
                'ScnParams':self.ScnParams, 
                }
            Scn = Scene(newScnParams)
            # Object positions are committed as scene is created...
            self.ScnList.append(Scn)
    def MakeListFromLib(self, Type='Obj'):
        """
        Usage: Idx = MakeListFromLib(Type='Obj')
        
        Creates an index/list of (objects, bgs) for each scene, given a bvpLibrary
        Input "Type" specifies which type of scene element ('Obj', 'BG', 'Sky') is to be arranged into a list. (case doesn't matter)
        
        Each (object, bg, etc) is used an equal number of times
        Potentially replace this function with other ways to sample from object categories...? 
        (sampling more from some categories than others, guaranteeing an equal number of exemplars from each category, etc)
        ML 2011.10.31
        """
        if Type.lower()=='obj':
            List = self.nObjectsPerCat
            nUsed = self.nObjectsUsed
        elif Type.lower()=='bg':
            List = self.nBGsPerCat
            nUsed = self.nScenes
        elif Type.lower()=='sky':
            List = self.nSkiesPerCat
            nUsed = self.nScenes
        else:
            raise Exception('WTF - don''t know what to do with Type=%s'%Type)
        nAvail = sum(List)
        if nAvail==0:
            return None
        Idx = np.concatenate([np.arange(o)+n*1j for n, o in enumerate(List)])
        # decide how many repetitions of each object to use
        nReps = np.floor(float(nUsed)/float(nAvail))
        nExtra = nUsed - nReps * nAvail
        ShufIdx = np.random.permutation(nAvail)[:nExtra]
        Idx = np.concatenate([np.tile(Idx, nReps), Idx[ShufIdx]])
        np.random.shuffle(Idx) # shuffle objects
        ### NOTE! this leaves open the possiblity that multiple objects of the same type will be in the same scene. OK...
        Idx = Idx.tolist()
        return Idx
        '''
