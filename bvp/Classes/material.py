## NOTE! See http://western-skies.blogspot.com/2008/02/simple-complete-example-of-python.html for __getstate__() and __setstate__() methods

# Imports.
import os
from .mapped_class import MappedClass
from .. import utils
from ..options import config

IS_CYCLES = config.get('material', 'is_cycles')[0].lower() in ('t', 'y')

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
                 type='Material', is_cycles=None, dbi=None, _id=None, _rev=None): 
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
                link=False)
        return bpy.data.materials[self.name]

    @classmethod
    def from_blender(cls, name, dbi=None, **kwargs):
        fname = bpy.data.filepath
        ob = cls.__new__(cls)
        ob.__init__(dbi=dbinterface, name=name, fname=fname, **kwargs)
        return ob

    @classmethod
    def from_media(cls, fname, name, is_cycles=IS_CYCLES, dbi=None, **kwargs):
        """Create texture material from """
        if is_cycles:
            bpy.context.scene.render.engine = 'CYCLES'
        else:
            if bpy.app.version[1] > 79:
                bpy.context.scene.render.engine = 'BLENDER_EEVEE'
            else:
                bpy.context.scene.render.engine = 'BLENDER_RENDER'
        if isinstance(fname, list):
            # TODO: make this work.
            raise NotImplementedError('Image sequence not working yet...')
        _, ftype = os.path.splitext(fname)
        ftype = ftype.strip('.').lower()
        ftype_dict = dict(mp4='MOVIE',
                         ogv='MOVIE',
                         gif='MOVIE',
                         jpeg='IMAGE',
                         jpg='IMAGE',
                         png='IMAGE',
                         # More...
                         )
        if ftype not in ftype_dict:
            raise ValueError(('Unknown file type ({ftype}) - you might '
                              'need to modify `ftype_dict` in the code\n'
                              'to recognize this as an '
                              'image or movie...').format(ftype=ftype))
        mat = utils.blender.add_img_material(name, fname, 
                                             ftype_dict[ftype])
        # Make sure material is always saved in this file
        mat.use_fake_user = True
        # Saving main file is up to user... seems precipitous to save whole file here.
        blend_file = os.path.split(bpy.data.filepath)[1]
        # Instantiate class
        ob = cls.__new__(cls)
        ob.__init__(name=name, fname=blend_file, dbi=dbi, is_cycles=is_cycles, **kwargs)
        return ob


    def __repr__(self):
        S = '\n ~M~ Material "{name}" ~M~\n    ({fpath})'.format(name=self.name,
            fpath=self.fpath)
        return S