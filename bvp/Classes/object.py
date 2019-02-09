"""
.B.lender .V.ision .Project class for storage of abstraction of a Blender object

To do: Move Shape to this file? 
Add methods for re-doing textures, rendering point cloud, rendering axes, etc.

"""
## NOTE! See http://western-skies.blogspot.com/2008/02/simple-complete-example-of-python.html for __getstate__() and __setstate__() methods

# Imports
import os
import warnings
from .mapped_class import MappedClass
from bvp import utils
from bvp.options import config

try:
    import bpy
except ImportError: 
    pass

class Object(MappedClass):
    """Layer of abstraction for objects (imported from other files) in Blender scenes.
    """
    def __init__(self, name=None, type='Object', fname=None, action=None, pose=None, materials=None,
        pos3D=(0., 0., 0.), size3D=3., rot3D=(0., 0., 0.), n_faces=None, n_vertices=None, n_poses=0,
        basic_category=None, semantic_category=None, wordnet_label=None, armature=None, 
        constraints=None, real_world_size=None, _id=None, _rev=None, dbi=None, is_cycles=False, 
        is_realistic=False):
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
                if v == 'None':
                    setattr(self, k, None)
                else:
                    setattr(self, k, v)

        self._db_fields = [] # action?
        self._data_fields = ['pos2D', 'pos3D', 'rot3D', 'size3D', 'action', 'pose', 'materials']
        self._temp_fields = ['min_xyz_pos', 'max_xyz_pos', 'bounding_box_center', 
                             'bounding_box_dimensions', 'xyz_trajectory', 'max_xyz_trajectory',
                             'blender_object', 'blender_group', 'proxy']
        # Extras
        self.blender_object = None
        self.blender_group = None
        self.armature = None
        self.proxy = None
        self.pos2D = None # location in the image plane (normalized 0-1)
        # TODO: Determine if this is still necessary (this relates to props stored in .blend files, prob.)
        if isinstance(self.real_world_size, (list, tuple)):
            self.real_world_size = self.real_world_size[0]

    def __repr__(self):
        """Display string"""
        ob_str = '\n ~O~ Object "%s" ~O~\n'%(self.name)
        if self.fname:
            ob_str+='Parent File: {}\n'.format(self.fpath)
        if self.semantic_category:
            ob_str += ','.join(self.semantic_category) + '\n' #[0]
            #for s in self.semantic_category[1:]: ob_str+=', %s'%s
            #ob_str+='\n'
        # if self.pos3D:
        #     ob_str+='Position: (x=%.2f, y=%.2f, z=%.2f) '%tuple(self.pos3D)
        # if self.size3D:
        #     ob_str+='Size: %.2f '%self.size3D
        # if self.pose:
        #     ob_str+='Pose: #%d'%self.pose
        # if self.pos3D or self.size3D or self.pose:
        #     ob_str+='\n'
        # if self.n_vertices:
        #     ob_str+='%d Verts; %d Faces'%(self.n_vertices, self.n_faces)
        return(ob_str)
 
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
        # Make file local, if it isn't already
        self.cloud_download()
        prev_placed = self.blender_object is not None
        # Optionally link to a specific scene
        scn = utils.blender.set_scene(scn)
        # Get object (parent of group / proxy)
        if self.name is None:
            # Default object
            proxy = False
            self.blender_object = self.add_dummy()
        else:
            self.blender_object = utils.blender.add_group(self.name, self.fname, self.path, proxy=proxy)
        # Get group of meshes in this object / proxy object
        if proxy:
            self.blender_group = self.blender_object.dupli_group
        else:
            # HRMMM
            #assert len(self.blender_object.users_group) == 1
            self.blender_group = self.blender_object.users_group[0]
        # Position / rotation
        if self.pos3D is not None:
            self.blender_object.location = self.pos3D
        if self.rot3D is not None:
            self.blender_object.rotation_euler = self.rot3D
        # Get armature, if an armature exists for this object
        armatures = [x for x in self.blender_group.objects if x.type=='ARMATURE']
        # Select one armature for poses / actions, if armatures exist
        if len(armatures) == 0:
            armature = None
        else:
            # Some armature object detected. Proceed with pose / action.
            if len(armatures) > 1:
                raise Exception('Multiple armatures detected, this is probably an irregularity in the file...')
                # Try to deal with multiple armatures by selecting 
                # the armature with a pose library attached
                pose_test = [a for a in armatures if not a.pose_library is None]
                if len(pose_test)==0:
                    armature = armatures[0]
                elif len(pose_test)==1:
                    armature = pose_test[0]
                else:
                    raise Exception("Aborting - all armatures have pose libraries, I don't know what to do")
            elif len(armatures) == 1:
                armature = armatures[0]

        if proxy and armature is not None:
            bpy.ops.object.proxy_make(object=armature.name) #object=pOb.name,type=armatures.name)
            self.armature = bpy.context.object
            self.armature.pose_library = armature.pose_library
        else:
            self.armature = armature
        # Update self w/ list of poses
        if self.armature is not None and self.armature.pose_library is not None:
            self.poses = [x.name for x in self.armature.pose_library.pose_markers]
        # Set pose, action
        if not self.pose is None:
            self.apply_pose(self.armature, self.pose)
        if not self.action is None:
            self.apply_action(self.armature, self.action)
        if not self.materials is None:
            self.apply_materials(self.materials)
        # Deal with particle systems on imported objects. Use of particle 
        # systems in general is not advised, since they complicate sizing 
        # and drastically slow renders.
        for o in self.blender_group.objects:
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
        # Scale to correct size
        orig_size = 10. # By BVP convention, all objects are stored in library files w/ max dim of 10 units
        sz_factor = float(self.size3D) / orig_size
        # THIS IS A YOOOOGE HACK
        if not prev_placed:
            if self.armature is not None:
                self.armature.scale *= sz_factor
            else:
                self.blender_object.scale *= sz_factor
        self.proxy = proxy

        scn.update()
        # Switch frame & update again, because some poses and other effects 
        # don't seem to take effect until the frame changes
        scn.frame_current += 1
        scn.update()
        scn.frame_current -= 1
        scn.update()
        return self.blender_object

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
        act = action.link()
        if arm.animation_data is None:
            arm.animation_data_create()
        if act is None:
            # Necessary?
            raise ValueError("action linking returned `None`")
        arm.animation_data.action = act

    def apply_pose(self, armature, pose_index):
        """Apply a pose to an armature.

        Parameters
        ----------
        armature : bpy.data.object containing armature
            Armature to which to apply pose
        pose_index : scalar 
            Index for pose in the armature's pose library

        Notes
        -----
        This function only applies WHOLE-ARMATURE poses (for now). It would be useful 
        to update this function to pose individual bones of an armature.
        """
        # Set mode to pose mode
        utils.blender.grab_only(armature)
        bpy.ops.object.posemode_toggle()
        bpy.ops.pose.select_all(action="SELECT")
        bpy.ops.poselib.apply_pose(pose_index=pose_index)
        # Set back to previous mode; otherwise Blender may puke and die with next command
        bpy.ops.object.posemode_toggle()

    def apply_materials(self, materials):
        """Apply materials to already-placed object.
        
        Parameters
        ----------
        objects : list
            list of all blender objects in this group
        materials : list
            list of bvp materials to apply. ** CURRENTLY ONLY WORKS FOR ONE MATERIAL **
        """
        # TODO: Deal with uv. 
        # WIP error
        if len(materials) > 1:
            raise NotImplementedError('Multiple material assignment not working yet.')

        for i, material in enumerate(materials):
            mat = material.link()
            if self.proxy:
                utils.blender.apply_material(self.blender_object, mat, proxy_object=self.proxy, uv=False)
            else:
                for o in self.blender_group.objects:
                    if o.type=='MESH':
                        utils.blender.apply_material(o, mat, proxy_object=self.proxy, uv=False)


    def add_dummy(self):
        """Add a sphere
        
        TODO: options for what sort of shape (not just a sphere?)
        """
        blender_default_size = 10 # by convention... just making explicit here
        utils.blender.set_cursor((0, 0, 0))
        bpy.ops.mesh.primitive_uv_sphere_add(size=blender_default_size / 2.)
        utils.blender.set_cursor((0, 0, -blender_default_size / 2.))
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        bpy.ops.transform.translate(value=(0, 0, blender_default_size / 2.))
        utils.blender.set_cursor((0, 0, 0))
        obj = bpy.context.object
        grp = bpy.data.groups.new('dummy')
        grp.objects.link(obj)
        # Rotations don't matter; it's a sphere.
        return obj

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

    def collides_with(self, target):
        """Returns whether or not this object's bounding box collides  with the bounding box of target

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
        c2 = target.bounding_box_center
        d2 = target.bounding_box_dimensions
        
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
        pos = self.pos3D
        if self.action:
            sf = self.size3D/10
            min_points = self.action.min_xyz_trajectory
            return [(pos[0]+sf*pt[0], pos[1]+sf*pt[1], pos[2]+sf*pt[2]) for pt in min_points]
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
        pos = self.pos3D
        if self.action:
            sf = self.size3D/10
            max_points = self.action.max_xyz_trajectory
            return [(pos[0]+sf*pt[0], pos[1]+sf*pt[1], pos[2]+sf*pt[2]) for pt in max_points]
        else:
            return [self.pos3D]

    @property
    def xyz_trajectory(self):
        min_pt = self.min_xyz_trajectory
        max_pt = self.max_xyz_trajectory
        pos = self.pos3D
        return [((mi[0]+ma[0])/2,(mi[1]+ma[1])/2, mi[2]) for mi, ma in zip(min_pt, max_pt)]
    
