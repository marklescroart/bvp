## NOTE! See http://western-skies.blogspot.com/2008/02/simple-complete-example-of-python.html for __getstate__() and __setstate__() methods

# Imports.
import os
from ..utils.blender import add_group
from .MappedClass import MappedClass

try:
    import bpy
    is_blender = True
except ImportError:
    is_blender = False

# Class def
class Shadow(MappedClass):
    """
    Class for abstract blender scene backgrounds
    """
    def __init__(self, name=None, fname=None, semantic_category=None, real_world_size=None,
        n_vertices=None, n_faces=None, type='Shadow', dbi=None, _id=None, _rev=None): 
        """Class to store shadows 
                
        Notes
        -----
        As of 2011.10.19, there is only one shadow category (noise). May add more...
        Buildings
        Natural
        Inside
        etc.
        """
        # Map inputs to properties
        inpt = locals()
        self.type = 'Shadow'
        for k, v in inpt.items(): 
            if not k in ('self', 'type'):
                if v == 'None':
                    setattr(self, k, None)
                else:
                    setattr(self, k, v)
        # Set _temp_params, etc.
        self._temp_fields = []
        self._data_fields = []
        self._db_fields = []

    def __repr__(self):
        S = '\n ~S~ Shadow "%s" ~S~\n'%self.name
        return S
        
    def place(self, scn=None, scale=None):
        """Adds shadow object to Blender scene
        """
        if not scn:
            scn = bpy.context.scene # Get current scene if input not supplied
        if self.name:
            # Add group of mesh object(s)
            shadow_ob = add_group(self.name, self.fname, self.path)
        if scale is not None:
            sz = scale / self.real_world_size[0] # most skies are 100x100 in area
            bpy.ops.transform.resize(value=(sz, sz, sz))            