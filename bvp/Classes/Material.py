## NOTE! See http://western-skies.blogspot.com/2008/02/simple-complete-example-of-python.html for __getstate__() and __setstate__() methods

# Imports.
import os
from .MappedClass import MappedClass

try:
    import bpy
    is_blender = True
except ImportError:
    is_blender = False

# Class def
class Material(MappedClass):
    """
    Class for abstract blender scene backgrounds
    """
    def __init__(self, name=None, fname=None, semantic_category=None, wordnet_label=None, 
                 type='Material', dbi=None, _id=None, _rev=None): 
        """Class to store materials

        Just a pointer to the file in which the material lives for now.
                
        """
        # Map inputs to properties
        inpt = locals()
        self.type = 'Material'
        for k, v in inpt.items(): 
            if not k in ('self', 'type'):
                setattr(self, k, v)
        # Set _temp_params, etc.
        self._temp_fields = []
        self._data_fields = []
        self._db_fields = []

    def __repr__(self):
        S = '\n ~M~ Material "{name}" ~M~\n    ({fname})'.format(name=self.name,
            fpath=self.fpath)
        return S