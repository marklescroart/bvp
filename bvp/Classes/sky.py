## NOTE! See http : //western-skies.blogspot.com/2008/02/simple-complete-example-of-python.html for __getstate__() and __setstate__() methods

# Imports
import os
import math as bnp
from six import string_types
from .. import utils as bvpu
from .mapped_class import MappedClass

try:
    import bpy
    is_blender = True
except ImportError: 
    is_blender = False

class Sky(MappedClass):
    """Class for skies and lighting (sun, lamps, world) for scenes    
    """
    def __init__(self, name='default_outdoor', light_location=None, light_type=None, light_rotation=None, 
        semantic_category=None, real_world_size=100., fname=None, n_faces=None, n_vertices=None, 
        world_params=None, world_lighting=None, type='Sky', dbi=None, _id=None, _rev=None):
        """ Class for skies & lights in Blender scenes

        Parameters
        ----------
        fname : string file name
            .blend file housing this sky
        name : string
            group name to be imported from category file, e.g. 'BG_Sky001'
        semantic_category - semantic category of this sky - a list, e.g. ['dome', 'day', 'sunny']
        light_location : tuple / list or tuple / list of tuples /lists
            location of light(s) for scene.
            NOTE: THIS CURRENTLY DOES NOTHING FOR IMPORTED SCENES. GET RID OF ME??
        light_rotation : tuple / list or tuple / list of tuples /lists
            rotation of light(s) for scene. Single lights should always be on the y=0, x<0 half-plane, 
            w/ rotation (x, 0, 90) (w/ a negative x value)
            NOTE: THIS CURRENTLY DOES NOTHING FOR IMPORTED SCENES. GET RID OF ME?? 

        Other Parameters
        ----------------        
        world_params : dict | None
            Usually, world parameters for skies are stored in the library .blend files for each sky. 
            However, those parameters can be optionally over-ridden by this dictionary, which 
            specifyies Blender world parameters. Fields are:
            'horizon_color' : (.55, .65, .75)
            'use_sky_paper' : False
            'use_sky_blend' : False
            'use_sky_real' : False
        world_lighting : dict | None
            Same as `world_params`, for lighting parameters. Fields are:
            'use_ambient_occlusion' : True
            'ao_factor' : 1.0
            'use_indirect_light' : True
            'indirect_factor' : 1.0
            'use_environment_light' : True
            'environment_energy' : 0.7
        """
        # Map inputs to properties
        inpt = locals()
        self.type = 'Sky'
        for k, v in inpt.items(): 
            if not k in ('self', 'type'):
                if v == 'None':
                    setattr(self, k, None)
                else:
                    setattr(self, k, v)
        # Set _temp_params, etc.
        self._temp_fields = []
        self._data_fields = []

        # TO DO: delete me once we've verified that it's OK with current blender files
        if isinstance(self.real_world_size, (list, tuple)):
            self.real_world_size = self.real_world_size[0]
        
        # These defaults should all be instantiated as scenes within an included .blend file. 
        # i.e. different scenes with names default_indoor, default_outdoor, default_display, default_simple
        if self.name=='default_outdoor':
            # Default sky: sun
            self.light_type = 'SUN'
            self.light_location = (0., 0., 35.)
            self.light_rotation = (0.6503279805183411, 0.055217113345861435, 1.8663908243179321)
            self.world_params = bvpu.basics.fixedKeyDict({
                    # Sky color
                    'horizon_color' : (.55, .65, .75), # bluish
                    'use_sky_paper' : False, 
                    'use_sky_blend' : False, 
                    'use_sky_real' : False, 
                    })
                    # Stars? Mist? 
            self.world_lighting = bvpu.basics.fixedKeyDict({
                    # World lighting settings (defaults for no bg, no sky, no lights, just blank scene + camera)
                    # AO
                    'use_ambient_occlusion' : True, 
                    'ao_factor' : .3, 
                    # Indirect lighting
                    'use_indirect_light' : False, # Nice, but expensive
                    'indirect_factor' : 0.5, 
                    'indirect_bounces' : 2, 
                    'gather_method' : 'APPROXIMATE', 
                    # Environment lighting
                    'use_environment_light' : True, 
                    'environment_energy' : 0.55, 
                    'environment_color' : 'SKY_COLOR', 
                    })
        elif self.name=='default_indoor':
            # Indoor lighting
            self.light_type = 'SUN' # Make this a few point lights??
            self.light_location = [[0, 0, 25]]
            self.light_rotation = [[0, 0, 0]]            
            self.world_params = bvpu.basics.fixedKeyDict({
                    # Sky color
                    'horizon_color' : (.6, .55, .43), #brownish
                    'use_sky_paper' : False, 
                    'use_sky_blend' : False, 
                    'use_sky_real' : False, 
                    })
                    # Stars? Mist? 
            self.world_lighting = bvpu.basics.fixedKeyDict({
                    # World lighting settings (defaults for no bg, no sky, no lights, just blank scene + camera)
                    # AO
                    'use_ambient_occlusion' : True, 
                    'ao_factor' : .3, 
                    # Indirect lighting
                    'use_indirect_light' : False, # Nice, but expensive
                    'indirect_factor' : 0.5, 
                    'indirect_bounces' : 2, 
                    'gather_method' : 'APPROXIMATE', 
                    # Environment lighting
                    'use_environment_light' : True, 
                    'environment_energy' : 0.4, # Most have other light sources in the scene
                    'environment_color' : 'SKY_COLOR', 
                    })
        elif self.name in ('none', None):
            # No lights, just environment settings
            self.world_params = bvpu.basics.fixedKeyDict({
                    # Sky color
                    'horizon_color' : (.5, .5, .5), #flat gray
                    'use_sky_paper' : False, 
                    'use_sky_blend' : False, 
                    'use_sky_real' : False, 
                    })
                    # Stars? Mist? 
            self.world_lighting = bvpu.basics.fixedKeyDict({
                    # World lighting settings (defaults for no bg, no sky, no lights, just blank scene + camera)
                    # AO
                    'use_ambient_occlusion' : True, 
                    'ao_factor' : .3, 
                    # Indirect lighting
                    'use_indirect_light' : False, # Nice, but expensive
                    'indirect_factor' : 0.5, 
                    'indirect_bounces' : 2, 
                    'gather_method' : 'APPROXIMATE', 
                    # Environment lighting
                    'use_environment_light' : True, 
                    'environment_energy' : 0.5, 
                    'environment_color' : 'SKY_COLOR', 
                    })

    def place(self, number=0, scn=None, scale=None, proxy=True):
        """Adds sky to Blender scene
        """
        # Make file local, if it isn't already
        self.cloud_download()
        lamp_ob = []
        if scn is None:
            scn = bpy.context.scene # Get current scene if input not supplied
        if not self.name in [None, 'default_indoor', 'default_outdoor', 'none']:
            # Add proxies of mesh objects
            sky_ob = bvpu.blender.add_group(self.name, self.fname, self.path, proxy=proxy)
            if scale is not None:
                print('Resizing...')
                sz = scale / self.real_world_size # most skies are 100x100 in area
                bpy.ops.transform.resize(value=(sz, sz, sz))
            if proxy:
                for o in sky_ob.dupli_group.objects:
                    bvpu.blender.grab_only(sky_ob)
                    bpy.ops.object.proxy_make(object=o.name) #, object=sky_ob.name, type=o.name)
                    new_ob = bpy.context.object
                    if new_ob.type=='MESH': # This better be the sky dome
                        bvpu.blender.set_layers(new_ob, [9])
                        new_ob.name=sky_ob.name
                        new_ob.pass_index = 100
                    else:
                        # Save lamp objects for more below
                        lamp_ob.append(new_ob)
            else:
                for o in sky_ob.users_group[0].objects:
                    # Unclear what layers these will be on
                    # If it varies, need to set pass index to 100
                    #if 
                    o.pass_index = 100

            # Get rid of linked group now that mesh objects and lamps are imported
            bpy.context.scene.objects.unlink(sky_ob)
            # Rename lamps
            for l in lamp_ob:
                l.name = 'BG_Lamp%04d'%(number)
            # Add world
            world = self.add_world() # Relies on world being named same thing as sky group... Could be problematic, but anything else is a worse pain
            scn.world.name = 's%04dworld'%(number) 
            
            scn.update()
            
        else:
            # Clear other lamps
            for ob in bpy.context.scene.objects: 
                if ob.type=='LAMP':
                    bpy.context.scene.objects.unlink(ob)
            if self.light_type is not None:
                # TO DO: Multiple lamps for defaults? 
                new_lamp = bpy.data.lamps.new('Default lamp', self.light_type)
                lamp_ob = bpy.data.objects.new('Default lamp', new_lamp)
                lamp_ob.rotation_euler = self.light_rotation
                lamp_ob.location = self.light_location

        if not scn.world:
            scn.world = bpy.data.worlds.new('s%04dworld'%number)

        if self.world_params is not None:
            for k, v in self.world_params.items():
                setattr(scn.world, k, v)
        if self.world_lighting is not None:
            for k, v in self.world_lighting.items():
                setattr(scn.world.light_settings, k, v)
        
        # (TEMP?) Over-ride of Ambient Occlusion (AO) for more efficient renders:
        scn.world.light_settings.gather_method = 'RAYTRACE'
        scn.world.light_settings.use_ambient_occlusion = False 
        scn.update()
        # (/TEMP?) Over-ride of AO
        
    def add_world(self, scn=None):
        """Adds a specified world from a specified file, as in bvp.utils.blender.add_group()

        NOTE! Currently (2012.02) worlds and sky groups must have the same (unique) name!
        """
        if not scn:
            scn = bpy.context.scene
        bpy.ops.wm.link_append(
            directory=os.path.join(self.path, self.fname)+"\\World\\", # i.e., directory WITHIN .blend file (Scenes / Objects / World / etc)
            filepath="//"+self.fname+"\\World\\"+self.name, # local filepath within .blend file to the world to be imported
            filename=self.name, # "filename" being the name of the data block, i.e. the name of the world.
            link=False, 
            relative_path=False, 
            autoselect=True)
        scn.world = bpy.data.worlds[self.name]

    def __repr__(self):
        S = '\n ~S~ Sky "%s" ~S~\n'%(self.name)
        if self.fname:
            S+='Parent File: %s\n'%self.fname
        if self.semantic_category:
            S+=self.semantic_category[0]
            for s in self.semantic_category[1 : ]: S+=', %s'%s
            S+='\n'
        if self.n_vertices:
            S+='%d Verts; %d Faces'%(self.n_vertices, self.n_faces)
        return(S)
