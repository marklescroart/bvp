# Imports
import os
from ..utils.blender import add_group
from .Constraint import ObConstraint, CamConstraint
# Should be moved, along with test below
from .Object import Object
from .Camera import Camera
from .Scene import Scene
from .Sky import Sky

try:
    import bpy
    import mathutils as bmu
    is_blender = True
except ImportError:
    is_blender = False

class Background(object):
    """Backgrounds for scenes"""
    def __init__(self, name='DummyBackground', fname=None, n_vertices=None, n_faces=None, lens=50., 
        semantic_category=None, object_semantic_category='all', sky_semantic_category='all',
        camera_constraint=None, object_constraints=None, obstacles=None, 
        bvptype='background', _id=None, _rev=None, dbi=None): 
        """Class to store Backgrounds (floor, walls, maybe lights, + constraints on objects) 

        A Background consists of a floor, background objects (walls, maybe trees, etc), maybe 
        lights, and constraints that partly determine the locations of objects, actions*, 
        and cameras in a scene. Each Background is stored as a group in a .blend file. 
        All elements of the background (floor, walls, buildings, emtpy objects defining 
        bounds of space, what have you) should be in this group. 
        
        Parameters
        ----------
        name: string 
            a unique identifier for the BG in question. Either a string 
                (interpreted to be the name of the BG group) or a lambda function
                (See bvpLibrary "getSceneComponent" function)

        """
        # Quick setting of attributes
        inpt = locals()
        self.bvptype = 'background'
        for k, v in inpt: 
            if not k in ('self', 'bvptype'):
                setattr(self, k, v)

    def __repr__(self):
        rstr = ('\n bvp Background {name}\n'
                '\t File: {fname}\n'
                '\t [{sem_cat}]\n'
                '\t [{wn_lab}]\n'
                '\t Size: {sz}, Lens: {cam}\n'
                '\t Vertices: {verts}, Faces: {face}\n'
                '\t Skies allowed: {skies}\n'
                '\t Objects allowed: {obj}\n'
                )
        sem_cat = [] if self.semantic_category is None else self.semantic_category
        wn_lab = [] if self.wordnet_label is None else self.wordnet_label
        skies = [] if self.sky_semantic_category is None else self.sky_semantic_category
        obj = [] if self.object_semantic_category is None else self.object_semantic_category
        rstr.format(name=self.name, fname=self.fname, 
                    sem_cat=', '.join(sem_cat),
                    wn_lab =', '.join(wn_lab),
                    sz=self.real_world_size, lens=self.lens,
                    verts=self.n_vertices, face=self.n_faces,
                    skies=', '.join(skies), obj=', '.join(obj))
        return(rstr)

    def place(self, scn=None):
        """
        Adds background to Blender scene
        """
        if not scn:
            scn = bpy.context.scene # Get current scene if input not supplied
        if self.name is not None:
            # Add group of mesh object(s)
            #fDir, fNm = os.path.split(self.fname)
            bg_dir = os.path.join(config.get('path','db_dir'), 'background')
            add_group(self.name, self.fname, bg_dir)
        else:
            print("BG is empty!")
            
    def test_background(self, frames=(1, 1), object_list=(), n_objects=0, edge_dist=0., object_overlap=0.50):
        """
        Tests object / camera constraints to see if they are working
        ** And shadows??

        Should be grouped with other testing functions, not here. Move.
        """
        Cam = Camera(frames=frames)
        Sky = Sky('*'+self.sky_semantic_category[0], Lib) # Choose a sky according to semantic category of BG ## RELIES ON ONLY ONE ENTRY FOR SKY SEMANTIC CAT! Should be most specific specifier...
        scn = Scene(0, BG=self, Cam=Cam, Sky=Sky, FrameRange=frames)
        if not object_list and not n_objects:
            object_list = [Object('*animal', Lib, size3D=None), Object('*vehicle', Lib, size3D=None), Object('*appliance', Lib, size3D=None)]
            n_objects = 0
        elif not object_list and n_objects:
            object_list = [Object(None, None, size3D=None) for x in range(n_objects)]
        scn.populate_scene(object_listist=object_list, ResetCam=True, RaiseError=True, nIter=100, edge_dist=edge_dist, object_overlap=object_overlap)
        if is_blender:
            RO = RenderOptions()
            scn.Create(RO)
            # Add spheres if there are blank objects:
            uv = bpy.ops.mesh.primitive_uv_sphere_add
            for o in range(n_objects):
                print('Sz of obj %d = %.2f'%(o, scn.Obj[o].size3D))
                ObSz = scn.Obj[o].size3D/2.
                pos = bmu.Vector(scn.Obj[o].pos3D) + bmu.Vector([0, 0, ObSz])
                uv(location=pos, size=ObSz)
