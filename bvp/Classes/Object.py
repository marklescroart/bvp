"""
.B.lender .V.ision .Project class for storage of abstraction of a Blender object

To do: Move Shape to this file? 
Add methods for re-doing textures, rendering point cloud, rendering axes, etc.

"""
## NOTE! See http://western-skies.blogspot.com/2008/02/simple-complete-example-of-python.html for __getstate__() and __setstate__() methods

# Imports
import os
import random
import warnings
from .MappedClass import MappedClass
from .. import utils as bvpu
from ..options import config

try:
    import bpy
    import mathutils as bmu
    is_blender = True
except ImportError: 
    is_blender = False

class Object(MappedClass):
    """Layer of abstraction for objects (imported from other files) in Blender scenes.
    """
    def __init__(self, name='DummyObject', type='Object', fname=None, action=None, pose=None, 
        pos3D=(0., 0., 0.), size3D=3., rot3D=(0., 0., 0.), n_faces=None, n_vertices=None, n_poses=0,
        basic_category=None, semantic_category=None, wordnet_label=None, armature=None, 
        constraints=None, real_world_size=None, _id=None, _rev=None, dbi=None):
        """ Class to store an abstraction of an object in a BVP scene. 

        Stores all necessary information to define an object in a scene: identifying information for
        the object in the database of all BVP objects (in `kwargs`, for database with interface `dbi`), 
        as well as (optionally) position, size, rotation, pose, and action information.

        Parameters
        ----------
        name : string 
            name of group to which object belongs in .blend file; should be unique, if possible
        pose : int | None
            Index for pose in object's pose library (if object has an armature with a pose library)
        action : Action object | dict (?)
            Action to be applied to object's armature
        pos3D : tuple or bpy.Vector
            Position [X, Y, Z] in 3D. If the object has an action attached to it, this is the 
            starting position for the action. 
        size3D : float | 3.0
            Size of largest dimension. Set to "None" to use object's real world size? (TO DO??)
        rot3D : bpy euler or tuple | (0., 0., 0.)
            rotation (xyz euler) in 3D
        
        _id : uuid string
            ID for object in database
        semantic_category : list
            semantic category(ies) to which object belongs
        real_world_size : float
            Size of object in meters
        armature : string
            List of possible armatures for object. FOR NOW, there are few armatures, so they are only
            stored as strings. As / if we get more, it may be worthwhile to create a mapped class for 
            armatures.
        dbi : DBInterface object | None
            Database interface object for local/network BVP database of objects. 

        Notes
        -----
        """
        # Set inputs to properties
        inpt = locals()
        self.type = 'Object'
        for k, v in inpt.items(): 
            if not k in ('self', 'type'):
                setattr(self, k, v)

        self._temp_fields = ['pos2D', 'pos3D','rot3D', 'size3D', 'action', 'pose']
        self._data_fields = []
        self._db_fields = []
        # What to do here?
        self.pos2D=None # location in the image plane (normalized 0-1)
        # TODO: Determine if this is still necessary (this relates to props stored in .blend files, prob.)
        if isinstance(self.real_world_size, (list, tuple)):
            self.real_world_size = self.real_world_size[0]

    def __repr__(self):
        """Display string"""
        S = '\n ~O~ Object "%s" ~O~\n'%(self.name)
        if self.fname:
            S+='Parent File: {}\n'.format(self.fpath)
        if self.semantic_category:
            S+=self.semantic_category[0]
            for s in self.semantic_category[1:]: S+=', %s'%s
            S+='\n'
        if self.pos3D:
            S+='Position: (x=%.2f, y=%.2f, z=%.2f) '%tuple(self.pos3D)
        if self.size3D:
            S+='Size: %.2f '%self.size3D
        if self.pose:
            S+='Pose: #%d'%self.pose
        if self.pos3D or self.size3D or self.pose:
            S+='\n'
        if self.n_vertices:
            S+='%d Verts; %d Faces'%(self.n_vertices, self.n_faces)
        return(S)
 
    def place(self, scn=None, proxy=True):
        """Places object into Blender scene, with pose & animation information

        Parameters
        ----------
        scn : string scene name | None
            If provided, the object will be linked to the named scene. If a scene
            named `scn` does not exist, it will be created.
        proxy : bool
            If True, places a proxy object (non-editable linked version of the object)
            into the scene. This is sufficient for most rendering purposes, and minimizes
            the complexity of the scene if you are working within Blender. 
        """
        # Optionally link to a specific scene
        scn = bvpu.blender.set_scene(scn)
        if self.name=='DummyObject':
            # Default object
            uv = bpy.ops.mesh.primitive_uv_sphere_add
            default_diameter=10.
            uv(size=default_diameter/2.)
            bvpu.blender.set_cursor((0, 0, -default_diameter/2.))
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
            bpy.ops.transform.translate(value=(0, 0, default_diameter/2.))
            bvpu.blender.set_cursor((0, 0, 0))
            grp = bpy.context.object
        else:
            grp = bvpu.blender.add_group(self.name, self.fname, self.path, proxy=proxy)
        # Select only this object as active object
        bvpu.blender.grab_only(grp) 
        if isinstance(grp, bpy.types.Object):
            grp_ob = grp
        else:
            grp_ob = bvpu.blender.find_group_parent(grp)
        # Objects are stored at max dim. 10 for easier viewability /manipulation
        # Allow for asymmetrical scaling for weirdo-looking objects? (currently no)
        sz = float(self.size3D)/10. # TODO 10 is default size for objects in files. Should be a variable, perhaps
        grp_ob.scale *= sz #setattr(grp, 'scale', bmu.Vector((sz, sz, sz))) # uniform x, y, z scale
        if self.pos3D is not None:
            setattr(grp_ob, 'location', self.pos3D)
        if self.rot3D is not None:
            setattr(grp_ob, 'rotation_euler', self.rot3D)
        # Get armature, if an armature exists for this object
        if proxy:
            armatures = [x for x in grp.dupli_group.objects if x.type=='ARMATURE']
        elif isinstance(grp, bpy.types.Group):
            armatures = [x for x in grp.objects if x.type=='ARMATURE']
        else:
            # This should raise an exception...
            armatures = []
        # Select one armature for poses
        if len(armatures)>0:
            # Some armature object detected. Proceed with pose / action.
            if len(armatures)>1:
                # Mayhaps this should raise an error...
                warnings.warn('Multiple armatures detected, this is probably an irregularity in the file...')
                # Try to deal with it by selecting the armature with a pose library attached:
                pose_test = [a for a in armatures if not a.pose_library is None]
                if len(pose_test)==0:
                    armature = armatures[0]
                elif len(pose_test)==1:
                    armature = pose_test[0]
                else:
                    raise Exception("Aborting - all armatures have pose libraries, I don't know what to do")
            elif len(armatures)==1:
                armature = armatures[0]
        else:
            armature = None
        if proxy:
            bpy.ops.object.proxy_make(object=armature.name) #object=pOb.name,type=armatures.name)
            pose_armature = bpy.context.object
            pose_armature.pose_library = armature.pose_library
        else:
            pose_armature = armature
        # Update self w/ list of poses??
        if pose_armature is not None and pose_armature.pose_library is not None:
            self.poses = [x.name for x in pose_armature.pose_library.pose_markers]

        # Set pose, action
        if not self.pose is None:
            self.apply_pose(pose_armature, self.pose)
        if not self.action is None:
            # Get Action if not already an Action object
            #if isinstance(self.action, dict):
            #    self.action = bvp.bvpAction(**self.action)
            # TODO: REPLACE ABOVE with 
            self.apply_action(pose_armature, self.action)
        # Deal with particle systems. Use of particle systems in general is not advised, since
        # they complicate sizing and drastically slow renders.
        if proxy:
            for o in grp.dupli_group.objects:
                # Get the MODIFIER object that contains the particle system
                particle_modifier = [p for p in o.modifiers if p.type=='PARTICLE_SYSTEM']
                for psm in particle_modifier:
                    # Option 1: Turn off the whole modifier (this seems to work)
                    if self.size3D  < 3.:
                        psm.show_render = False
                        psm.show_viewport = False
                    # Option 2: shorten / lengthen w/ object size
                    # NOTE: This doesn't work, since many particle systems are modified
                    # after creation (e.g., hair is commonly styled). Again, avoid if 
                    # possible...
        scn.update()
        # Switch frame & update again, because some poses / effects 
        # don't seem to take effect until the frame changes
        scn.frame_current+=1
        scn.update()
        scn.frame_current-=1
        scn.update()

    def place_full(self, scn=None, objects=True, materials=True, textures=True):
        """Import full copy of object (all meshes, materials, etc)

        PROBABLY BROKEN CURRENTLY (2014.09)

        USE WITH CAUTION. Only for modifying meshes / materials, which you PROBABLY DON'T WANT TO DO.

        Parameters
        ----------
        scn : scene within file (?) | None
            Don't know if this is even usable (2014.02.05)
        """
        # Optionally link to a differet scene
        scn = bvpu.blender.set_scene(scn)

        if self.name is None:
            print('Empty object! Using sphere instead!')
            uv = bpy.ops.mesh.primitive_uv_sphere_add
            uv(size=5)
            bvpu.blender.set_cursor((0, 0, -5.))
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
            bpy.ops.transform.translate(value=(0, 0, 5))
            bvpu.blender.set_cursor((0, 0, 0))
        else:
            fdir = os.path.join(bvp.Settings['Paths']['LibDir'], 'Objects/')
            bvpu.blender.add_group(self.name, self.fname, fdir)
            # 
        grp = bpy.context.object
        sz = float(self.size3D)/10. # Objects are stored at max dim. 10 for easier viewability /manipulation
        setattr(grp, 'scale', bmu.Vector((sz, sz, sz))) # uniform x, y, z scale
        if self.pos3D:
            setattr(grp, 'location', self.pos3D)
        if self.rot3D:
            # Use bpy.ops.transform here instead? Some objects may not have position set to zero properly!
            setattr(grp, 'rotation_euler', self.rot3D)
        if self.pose or self.pose==0: # allow for pose index to equal zero, but not None
            Arm, Pose = self.GetPoses(grp)
            self.apply_pose(Arm, self.pose)
        # Deal with particle systems:
        if not self.name is None:
            for o in grp.dupli_group.objects:
                # Get the MODIFIER object that contains the particle system
                particle_modifier = [p for p in o.modifiers if p.type=='PARTICLE_SYSTEM']
                for psm in particle_modifier:
                    #print('Object %s has particle system %s'%(o.name, ps.name))
                    # Option 1: Turn off the whole modifier (this seems to work)
                    if self.size3D  < 3.:
                        psm.show_render = False
                        psm.show_viewport = False
                    # Option 2: shorten / lengthen w/ object size
                    #psm.particle_system (set hair normal lower doesn't seem to work...s)
        scn.update()
        # Because some poses / effects don't seem to take effect until the frame changes:
        scn.frame_current+=1
        scn.update()
        scn.frame_current-=1
        scn.update()

    def apply_action(self, arm, action):
        """Apply an action to an armature.

        Kept separate from Object __init__ function so to be able to interactively apply actions 
        in an open Blender session.

        Make this a method of Action instead??

        Parameters
        ----------
        arm : bpy.data.object containing armature
            Armature object to which the action is applied.
        action : Action
            Action to be applied. Must have file_name and path attributes
        """
        # 
        print(action.fpath, action.name)
        act = bvpu.blender.add_action(action.name, action.fname, action.path)
        if arm.animation_data is None:
            arm.animation_data_create()
        arm.animation_data.action = act

    def apply_pose(self, Arm, PoseIdx):
        """Apply a pose to an armature.

        Parameters
        ----------
        Arm : bpy.data.object contianing armature
            Armature to which to apply pose
        PoseIdx : scalar 
            Index for pose in the armature's pose library

        Notes
        -----
        This function only applies WHOLE-ARMATURE poses (for now). Later it may be useful to update
        this function to pose individual bones of an armature.
        
        """
        # Set mode to pose mode
        bvpu.blender.grab_only(Arm)
        bpy.ops.object.posemode_toggle()
        bpy.ops.pose.select_all(action="SELECT")
        bpy.ops.poselib.apply_pose(pose_index=PoseIdx)
        # Set back to previous mode 
        # (IMPORTANT: otherwise Blender may puke and die with next command)
        bpy.ops.object.posemode_toggle()

    @property
    def max_xyz_pos(self):
        """Returns the maximum x,y,z coordinates of an object

        If the object has an action, then the action's max_xyz is added to the object's coordinates. If not, then the object's coordinates are returned as is.

        TODO: Include error handling. Possibly make the bounding box a complete class of its own.

        Parameters
        ----------
        self: self
        
        Returns
        -------
        (x,y,z): 3-tuple of the object's maximum x,y, and z coordinates respectively.
        """
        #
        if self.action:
            sf = self.size3D/10
            return (sf*self.action.max_xyz[0] + self.pos3D[0],sf*self.action.max_xyz[1] + self.pos3D[1],sf*self.action.max_xyz[2] + self.pos3D[2])
        else:
            return self.pos3D

    @property
    def min_xyz_pos(self):
        """Returns the minimum x,y,z coordinates of an object

        If the object has an action, then the action's min_xyz is added to the object's coordinates. If not, then the object's coordinates are returned as is.

        TODO: Include error handling. Possibly make the bounding box a complete class of its own.

        Parameters
        ----------
        self: self

        Returns
        -------
        (x,y,z): 3-tuple of the object's minimum x,y, and z coordinates respectively.
        """
        #
        sf = self.size3D/10
        if self.action:
            return (sf*self.action.min_xyz[0] + self.pos3D[0],sf*self.action.min_xyz[1] + self.pos3D[1],sf*self.action.min_xyz[2] + self.pos3D[2])
        else:
            return self.pos3D

    @property
    def bounding_box_center(self):
        """Calculates the center for the object's bounding box by averaging the max and min positions.

        The bounding box for the object is defined as an xyz-aligned cuboid with one vertex as the max position, and its diagonally opposite vertex as the min position. This function calculates its center

        TODO: Include error handling. Possibly make the bounding box a complete class of its own.

        Parameters
        ----------
        self: self
        
        Returns
        -------
        (x,y,z): 3-tuple of the x,y,z coordinates of the center of the object's bounding box.
        """   
        # 
        if self.action is not None:
            return self.pos3D
        else:
            max_pos =  self.max_xyz_pos
            min_pos =  self.min_xyz_pos
            return ((max_pos[0]+min_pos[0])/2,(max_pos[1]+min_pos[1])/2,(max_pos[2]+min_pos[2])/2)

    @property
    def bounding_box_dimensions(self):
        """Calculates the dimensions for the object's bounding box by differencing the max and min positions.

        The bounding box for the object is defined as an xyz-aligned cuboid with one vertex as the max position, and its diagonally opposite vertex as the min position. This function calculates its dimensions

        TODO: Include error handling. Possibly make the bounding box a complete class of its own.

        Parameters
        ----------
        self: self
        
        Returns
        -------
        (x,y,z): 3-tuple of the the x,y,z dimensions of the object's bounding box
        """
        # 
        max_pos =  self.max_xyz_pos
        min_pos =  self.min_xyz_pos
        return ((max_pos[0]-min_pos[0])+self.size3D,(max_pos[1]-min_pos[1])+self.size3D,(max_pos[2]-min_pos[2])+self.size3D)

    def collides_with(self, ob2):
        """Returns whether or not this object's bounding box collides  with the bounding box of ob2

        The bounding box for the object is defined as an xyz-aligned cuboid with one vertex as the max position, and its diagonally opposite vertex as the min position. This function calculates its dimensions

        TODO: Include error handling. Possibly make the bounding box a complete class of its own.

        Parameters
        ----------
        self: self
        
        Returns
        -------
        Bool collides: True if there are collisions, False if there are none.
        """
        # 
        c1 = self.bounding_box_center
        d1 = self.bounding_box_dimensions
        c2 = ob2.bounding_box_center
        d2 = ob2.bounding_box_dimensions
        
        x_collision = abs(c1[0]-c2[0]) < (d1[0]+d2[0])/2
        y_collision = abs(c1[1]-c2[1]) < (d1[1]+d2[1])/2
        z_collision = abs(c1[2]-c2[2]) < (d1[2]+d2[2])/2

        collides = x_collision and y_collision and z_collision

        return collides

    @property
    def min_xyz_trajectory(self):
        """Returns the min point of the object's bounding box at some points on the trajectory of its motion in xyz

        Parameters
        ----------
        self: self
        
        Returns
        -------
        List of tuples: list of (default 5) positions at equally spaced points in time
        """
        if self.action:
            sf = self.size3D/10
            min_points = self.action.min_xyz_trajectory
            return [(sf*pt[0], sf*pt[1], sf*pt[2]) for pt in min_points]
        else:
            return [self.pos3D]

    @property
    def max_xyz_trajectory(self):
        """Returns the max point of the object's bounding box at some points on the trajectory of its motion in xyz

        Parameters
        ----------
        self: self
        
        Returns
        -------
        List of tuples: list of (default 5) positions at equally spaced points in time
        """
        if self.action:
            sf = self.size3D/10
            max_points = self.action.max_xyz_trajectory
            return [(sf*pt[0], sf*pt[1], sf*pt[2]) for pt in max_points]
        else:
            return [self.pos3D]

    @property
    def xyz_trajectory(self):
        min_pt = self.min_xyz_trajectory
        max_pt = self.max_xyz_trajectory
        pos = self.pos3D
        return [(pos[0]+(mi[0]+ma[0])/2,pos[1]+(mi[1]+ma[1])/2, pos[2]+mi[2]) for mi, ma in zip(min_pt, max_pt)]
    