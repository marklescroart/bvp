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
            g_ob = grp
        else:
            g_ob = bvpu.blender.find_group_parent(grp)
        # Objects are stored at max dim. 10 for easier viewability /manipulation
        # Allow for asymmetrical scaling for weirdo-looking objects? (currently no)
        sz = float(self.size3D)/10. # TODO 10 is default size for objects in files. Should be a variable, perhaps
        g_ob.scale *= sz #setattr(grp, 'scale', bmu.Vector((sz, sz, sz))) # uniform x, y, z scale
        if self.pos3D is not None:
            setattr(g_ob, 'location', self.pos3D)
        if self.rot3D is not None:
            setattr(g_ob, 'rotation_euler', self.rot3D)
        # Get armature, if an armature exists for this object
        if is_proxy:
            armatures = [x for x in G.dupli_group.objects if x.type=='ARMATURE']
        elif isinstance(G, bpy.types.Group):
            armatures = [x for x in G.objects if x.type=='ARMATURE']
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
        if is_proxy:
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
            self.ApplyPose(pose_armature, self.pose)
        if not self.action is None:
            # Get bvpAction if not already a bvpAction object
            if isinstance(self.action,dict):
                self.action = bvp.bvpAction(**self.action)
            self.ApplyAction(pose_armature, self.action)
        # Deal with particle systems. Use of particle systems in general is not advised, since
        # they complicate sizing and drastically slow renders.
        if is_proxy:
            for o in G.dupli_group.objects:
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

    def ApplyAction(self, arm, action):
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
        fdir = os.path.join(bvp.Settings['Paths']['LibDir'], 'Actions/')
        act = bvpu.blender.add_action(action.name, action.fname, fdir)
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

