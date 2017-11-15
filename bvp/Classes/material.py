## NOTE! See http://western-skies.blogspot.com/2008/02/simple-complete-example-of-python.html for __getstate__() and __setstate__() methods

# Imports.
import os
from .mapped_class import MappedClass

try:
    import bpy
except ImportError:
    pass

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

    def link(self):
        """Link material to active Blender session
        """ 

        if self.name in bpy.data.materials:
            pass # Don't import twice
        else:
            bpy.ops.wm.append(
                filepath="//"+self.fname+"\\Material\\"+self.name, # local filepath within .blend file to the scene to be imported
                directory=self.fpath+"\\Material\\", # i.e., directory WITHIN .blend file (Scenes / Objects / Groups)
                filename=self.name, # "filename" is not the name of the file but the name of the data block, i.e. the name of the group. This stupid naming convention is due to Blender's API.
                link=True)

    def __repr__(self):
        S = '\n ~M~ Material "{name}" ~M~\n    ({fpath})'.format(name=self.name,
            fpath=self.fpath)
        return S