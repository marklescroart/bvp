# Imports
import os
import six
from bvp.utils.blender import add_group, grab_only, apply_material
from .constraint import ObConstraint, CamConstraint
from .mapped_class import MappedClass
from .object import Object

# Should be moved, along with test below
#from .Camera import Camera
#from .Scene import Scene
#from .Sky import Sky

try:
    import bpy
    import mathutils as bmu
    is_blender = True
except ImportError:
    is_blender = False

class Background(MappedClass):
    """Backgrounds for scenes"""
    def __init__(self, name='DummyBackground', fname=None, n_vertices=None, n_faces=None, 
        type='Background', wordnet_label=None, real_world_size=None, lens=50., is_cycles=None,
        semantic_category=None, object_semantic_category='all', sky_semantic_category='all',
        camera_constraints=None, object_constraints=None, obstacles=None, materials=None,
        _id=None, _rev=None, dbi=None): 
        """Class to store Backgrounds (floor, walls, maybe lights, + constraints on objects) 

        A Background consists of a floor, background objects (walls, maybe trees, etc), maybe 
        lights, and constraints that partly determine the locations of objects, actions*, 
        and cameras in a scene. Each Background is stored as a group in a .blend file. 
        All elements of the background (floor, walls, buildings, emtpy objects defining 
        bounds of space, what have you) should be in this group. 
        
        Parameters
        ---------
        name: string 
            a unique identifier for the BG in question. Either a string 
                (interpreted to be the name of the BG group) or a lambda function
                (See bvpLibrary "getSceneComponent" function)

        """
        # Quick setting of attributes
        inpt = locals()
        self.type = 'Background'
        for k, v in inpt.items(): 
            if not k in ('self', 'type'):
                if v == 'None':
                    setattr(self, k, None)
                else:
                    setattr(self, k, v)
        if isinstance(self.real_world_size, (list, tuple)):
            self.real_world_size = self.real_world_size[0]
        self._db_fields = []
        self._data_fields = ['materials']
        self._temp_fields = ['CamConstraint', 'ObConstraint']
        
        #mappedclass translation is not recursive, so we must set these manually. 
        #TODO Utkarsh: find better solution to this
        if self.camera_constraints is not None:
            self.CamConstraint = CamConstraint(**camera_constraints)
        if self.object_constraints is not None:
            self.ObConstraint = ObConstraint(**object_constraints)
        #if camera_constraints:
        #    for k in camera_constraints.keys():
        #        setattr(self.CamConstraint,k,camera_constraints[k])
        
        # self.obConstraints = ObConstraint()
        # if object_constraints:
        #     print(object_constraints)
        #     for k in object_constraints.keys():
        #         setattr(self.obConstraints,k,object_constraints[k])

        if obstacles is not None: # and obstacles.lower() != 'none'
            if isinstance(obstacles, list):
                #TODO: SemanticCat =/= semantic_category. Fix this at some point.
                self.obstacles = [Object(pos3D=obst['pos3D'],size3D=obst['size3D']) for obst in obstacles] 
            else:
                if isinstance(obstacles, six.string_types):
                    if obstacles.lower() != 'none':
                        raise Exception('String variable for `obstacles` in background not understood')
                    else:
                        # Fine.
                        pass 
                else:
                    print(obstacles)
    def place(self, scn=None, proxy=False):
        """
        Adds background to Blender scene
        """
        # Make file local, if it isn't already
        if self.path is not None:
            #
            self.cloud_download()
        if not scn:
            scn = bpy.context.scene # Get current scene if input not supplied
        if self.name is not 'DummyBackground':
            # Add group of mesh object(s)
            #print('{}, {}'.format(self.path, self.name))
            bg_ob = add_group(self.name, self.fname, self.path, proxy=proxy)
            # Next clause is a HACK because some background groups are not 
            # stored with a parent. Remove me when library is fixed.
            if isinstance(bg_ob, (list, tuple)):
                bg_ob = bg_ob[0]
            if not proxy:
                if bpy.app.version < (2, 80, 0):
                    bg_grp = bg_ob.users_group[0]
                else:
                    bg_grp = bg_ob.users_collection[0]
                for o in bg_grp.objects:
                    o.name = 'BG_' + o.name
        else:
            # Potentially add default background (with ground plane, other render settings...)
            print("BG is empty!")
        if self.materials is not None:
            if proxy:
                raise ValueError("Can't change materials of proxy objects. Use proxy=False.")
            if bpy.app.version < (2, 80, 0):
                self.apply_materials(bg_ob.users_group[0], self.materials)
            else:
                self.apply_materials(bg_ob.users_collection[0], self.materials)


    def apply_materials(self, bpy_grp, materials):
        """Apply materials to already-placed background.
        
        Parameters
        ----------
        objects : list
            list of all blender objects in this group
        materials : list
            list of bvp materials to apply. ** CURRENTLY ONLY WORKS FOR ONE MATERIAL **

        Notes
        -----
        TODO: Deal with uv in more sensible fashion
        """
        
        if len(materials) > 1:
            raise NotImplementedError('Multiple material assignment not working yet.')

        for i, material in enumerate(materials):
            mat = material.link()
            for o in bpy_grp.objects:
                if o.type in ('MESH', 'CURVE'): # More? 
                    apply_material(o, mat, uv=False)
  

    @classmethod
    def from_blender(cls, context, dbi):
        """Create an Action from a selected object in Blender. 

        This function only works within an active Blender session. The selected object must be an armature with
        an action linked to it. 

        Parameters
        ----------
        context : bpy context
            context for determining selected object, etc
        """
        # Idiot-proofing
        assert is_blender, "from_blender() only works within an active blender session."

        # Get relevant blender objects 
        wm = context.window_manager
        scn = context.scene
        ob = context.object
        grab_only(ob)

        # Compute parameters
        ## GET GROUP, USE WORDNET LABELS FOR GROUP
        if bpy.app.version < (2, 80, 0):
            grp = ob.users_group[0]
        else:
            grp = ob.users_collection[0]
        ## WordNet labels
        wordnet_label = [s.name for s in grp.Background.wordnet_label] # or whatever 
        semantic_category = [s.name for s in grp.Background.semantic_category] # OR whatever
        
        #  TODO: n_vertices, n_faces, lens (interactive manual input?), constraints.
        
        ## Parent file
        #pfile = act.Action.parent_file
        # The above value (pfile) is ignored for now. Need to eventually implement some way to take the contents 
        # of the current file (group/action/whatever) and save them (append them) to another specfied file
        # in the database. Currently NOT IMPLEMENTED.
        thisfile = os.path.dirname(bpy.data.filepath) #if len(bpy.data.filepath)>0 else pfile
        if thisfile=="":
            # Require saving in db-appropriate location 
            raise NotImplementedError("Please save this file into %s before trying to save to database."%(os.path.join(dbpath, 'Background/')))
        # Construct bvp Action
        bg = cls.__new__(cls)
        bg.__init__(name=grp.name, 
                    fname=thisfile, 
                    n_vertices=n_vertices, 
                    n_faces=n_faces, 
                    lens=lens, 
                    semantic_category=grp.Background.semantic_category, 
                    object_semantic_category=grp.Background.object_semantic_category, 
                    sky_semantic_category=grp.Background.sky_semantic_category,
                    camera_constraint=None, # Save these? Unclear... 
                    object_constraints=None, # same
                    obstacles=None, # same
                    dbi=dbi
                    )
        return bg
            
    # def test_background(self, frames=(1, 1), object_list=(), n_objects=0, edge_dist=0., object_overlap=0.50):
    #     """
    #     Tests object / camera constraints to see if they are working
    #     ** And shadows??

    #     Should be grouped with other testing functions, not here. Move.
    #     """
    #     Cam = Camera(frames=frames)
    #     Sky = Sky('*'+self.sky_semantic_category[0], Lib) # Choose a sky according to semantic category of BG ## RELIES ON ONLY ONE ENTRY FOR SKY SEMANTIC CAT! Should be most specific specifier...
    #     scn = Scene(0, BG=self, Cam=Cam, Sky=Sky, FrameRange=frames)
    #     if not object_list and not n_objects:
    #         object_list = [Object('*animal', Lib, size3D=None), Object('*vehicle', Lib, size3D=None), Object('*appliance', Lib, size3D=None)]
    #         n_objects = 0
    #     elif not object_list and n_objects:
    #         object_list = [Object(None, None, size3D=None) for x in range(n_objects)]
    #     scn.populate_scene(object_listist=object_list, ResetCam=True, RaiseError=True, nIter=100, edge_dist=edge_dist, object_overlap=object_overlap)
    #     if is_blender:
    #         RO = RenderOptions()
    #         scn.Create(RO)
    #         # Add spheres if there are blank objects:
    #         uv = bpy.ops.mesh.primitive_uv_sphere_add
    #         for o in range(n_objects):
    #             print('Sz of obj %d = %.2f'%(o, scn.Obj[o].size3D))
    #             ObSz = scn.Obj[o].size3D/2.
    #             pos = bmu.Vector(scn.Obj[o].pos3D) + bmu.Vector([0, 0, ObSz])
    #             uv(location=pos, size=ObSz)

    def __repr__(self):
        rstr = ('\nbvp Background {name}\n'
                '    File: {fname}\n'
                '    [{sem_cat}]\n'
                '    [{wn_lab}]\n'
                '    Size: {sz}, Lens: {lens}\n'
                '    Vertices: {verts}, Faces: {face}\n'
                '    Skies allowed: {skies}\n'
                '    Objects allowed: {obj}\n'
                )
        sem_cat = [] if self.semantic_category is None else self.semantic_category
        wn_lab = [] if self.wordnet_label is None else self.wordnet_label
        skies = [] if self.sky_semantic_category is None else self.sky_semantic_category
        obj = [] if self.object_semantic_category is None else self.object_semantic_category
        out = rstr.format(name=self.name, fname=self.fname, 
                    sem_cat=', '.join(sem_cat),
                    wn_lab =', '.join(wn_lab),
                    sz=self.real_world_size, lens=self.lens,
                    verts=self.n_vertices, face=self.n_faces,
                    skies=', '.join(skies), obj=', '.join(obj))
        return(out)
