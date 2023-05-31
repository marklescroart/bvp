"""
TODO:

Might be nice to store specific presets of RenderOptions, for specific final
choices for rendering stimuli for a given experiment.

FOR NOW, this is not going to be a mapped class...

"""

# Imports
import os
import sys
import math as bnp
import numpy as np

from .. import utils as bvpu
from ..options import config

try:
    import bpy
    import mathutils as bmu
    is_blender = True
except ImportError:
    is_blender = False

RENDER_DIR = os.path.expanduser(config.get('path', 'render_dir'))
bvp_basedir = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                           '../', '../'))
render_file = os.path.abspath(os.path.join(bvp_basedir, 'Scripts',
                                           'BlenderRender.py'))

# The "type" input for compositor node creation has been arbitrarily changed
# numerous times throughout Blender API development. This is EXTREMELY
# IRRITATING. Nonetheless, the format may change again, so I've collected
# all the node type IDs here and use the variables below

if sys.platform == 'darwin':
    # print('Mac computer node names!')
    # RLayerNodeX = 'R_LAYERS'
    # CompositorNodeX = 'COMPOSITE'
    # OutputFileNodeX = 'OUTPUT_FILE'
    # ViewerNodeX = 'VIEWER'
    # SepRGBANodeX = 'CompositorNodeSepRGBA'
    # CombRGBANodeX = 'CompositorNodeCombRGBA'
    # IDmaskNodeX = 'ID_MASK'
    # MathNodeX = 'CompositorNodeMath'
    RLayerNode = 'CompositorNodeRLayers'
    CompositorNode = 'CompositorNodeComposite'
    OutputFileNode = 'CompositorNodeOutputFile'
    ViewerNode = 'CompositorNodeViewer'
    SepRGBANode = 'CompositorNodeSepRGBA'
    CombRGBANode = 'CompositorNodeCombRGBA'
    IDmaskNode = 'CompositorNodeIDMask'
    MathNode = 'CompositorNodeMath'

else:
    RLayerNode = 'CompositorNodeRLayers'
    CompositorNode = 'CompositorNodeComposite'
    OutputFileNode = 'CompositorNodeOutputFile'
    ViewerNode = 'CompositorNodeViewer'
    SepRGBANode = 'CompositorNodeSepRGBA'
    CombRGBANode = 'CompositorNodeCombRGBA'
    IDmaskNode = 'CompositorNodeIDMask'
    MathNode = 'CompositorNodeMath'


class RenderOptions(object):
    """Class for storing render options for a scene."""

    def __init__(self, blender_params=None, bvp_params=None):
        """Initialize rendering options for scenes in BVP framework.

        Parameters
        ----------
        blender_params : dict
            directly updates any blender scene.render params for the scene
        bvp_params : dict
            establishes more complex BVP options (whether to initialize node setup 
            for different render passes [some work, others don't], base path for 
            render directory, and which file to use to render BVP scenes).
            fields : defaults are as follows:
                ### --- Basic file / rendering stuff --- ###
                Type : 'FirstFrame', # other options :  All, FirstAndLastFrame, 'every4th'
                RenderFile : os.path.join(bvp.__path__[0], 'Scripts', 'BlenderRender.py') # File to call to render scenes
                BasePath : '/auto/k1/mark/Desktop/BlenderTemp/', # Base render path (TO DO: replace with bvp config settings)
                
                ### --- Render passes --- ###
                Image : True # Render RGB(A) images or not (alpha layer or not determined by blender_params )
                ObjectMasks : False # Render masks for all BVP objects in scene (working)
                Zdepth : False # Render Z depth pass 
                Normals : False, # Not yet implemented
                
                ### --- Work-in-progress render passes (NOT working as of 2015.05) --- ###
                Contours : False, #Freestyle, yet to be implemented
                Motion : False, # Render motion (ground truth optical flow) pass
                Voxels : False # Create voxelized version of each scene 
                Axes : False, # based on N.Cornea code, for now 
                Clay : False, # All shape, no material / texture (over-ride w/ plain [clay] material) lighting??

        Notes
        -----
        RenderOptions does not directly modify a scene's file path; it only provides the base file (parent directory) for all rendering.
        Scene's "apply_opts" function should be the only function to modify with bpy.context.scene.filepath (!!) (2012.03.12)

        """

        # May need some clever if statement here - checking on version of blender
        self.use_freestyle = False
        if self.use_freestyle:
            pass
            # Freestyle settings. Not used yet as of 2016.07
            #FSlineThickness = 3.0
            #FSlineCol = (0.0, 0.0, 0.0)
        self.use_antialiasing = True
        self.antialiasing_samples = '8'
        self.use_edge_enhance = False
        self.use_raytrace = True
        self.use_compositing = True
        self.use_textures = True
        self.use_sss = False
        self.use_shadows = True
        self.use_envmaps = False
        # File size
        self.engine = 'BLENDER_RENDER'
        self.resolution_x = 512
        self.resolution_y = 512
        self.resolution_percentage = 100
        self.tile_x = 64  # More?
        self.tile_y = 64  # More?
        # Fields not in bpy.data.scene.render class:
        # Image settings: File format and color mode
        self.image_settings = dict(color_mode='RGBA',
                                   file_format='PNG')

        self.DefaultLayerOpts = {}
        #     'use_zmask': False,
        #     'use_all_z': False,
        #     'use_solid': True,  # Necessary for almost everything
        #     'use_halo': False,
        #     'use_ztransp': False,
        #     'use_sky': False,
        #     'use_edge_enhance': False,
        #     'use_strand': False,
        #     'use_freestyle': False,
        #     'use_pass_combined': False,
        #     'use_pass_z': False,
        #     'use_pass_vector': False,
        #     'use_pass_normal': False,
        #     'use_pass_uv': False,
        #     'use_pass_mist': False,
        #     'use_pass_object_index': False,
        #     'use_pass_color': False,
        #     'use_pass_diffuse': False,
        #     'use_pass_specular': False,
        #     'use_pass_shadow': False,
        #     'use_pass_emit': False,
        #     'use_pass_ambient_occlusion': False,
        #     'use_pass_environment': False,
        #     'use_pass_indirect': False,
        #     'use_pass_reflection': False,
        #     'use_pass_refraction': False,
        # }
        # Proposition: get rid of above, replace (below) with:
        # to_set = {}
        # for this_property in dir(this_view_layer):
        #     if 'use' in this_property:
        #         to_set[this_property] = False
        if bpy.app.version < (2, 80, 0):
            self.DefaultLayerOpts['layers'] = tuple([True]*20)
        self.BVPopts = {
            # BVP specific rendering options
            "Image": True,
            "Voxels": False,  # Not yet implemented reliably.
            "ObjectMasks": False,
            "Motion": False,  # Not yet implemented reliably. Buggy AF
            "Zdepth": False,
            "Contours": False,  # Freestyle, yet to be implemented
            "Axes": False,  # based on N.Cornea code, for now - still unfinished
            "Normals": False,
            # Not yet implemented - All shape, no material / texture (over-ride w/ plain [clay] material) lighting??
            "Clay": False,
            "Type": 'FirstFrame',  # other options: "All", "FirstAndLastFrame", 'every4th'
            "RenderFile": render_file,
            "BasePath": RENDER_DIR,
        }
        node_grid_scale_x = 200
        node_grid_scale_y = 300
        n_steps_max = 8
        n_rows = 20  # overkill, but whatever
        tx = (np.arange(0, n_steps_max) - (n_steps_max / 2)) * node_grid_scale_x
        ty = - ((np.arange(0, n_rows) - (n_rows / 2)) * node_grid_scale_y)
        xg, yg = np.meshgrid(tx, ty)
        self._node_grid_locations = np.dstack([xg, yg])
        # Disallow updates that add fields
        self.__dict__ = bvpu.basics.fixedKeyDict(self.__dict__)
        # Update defaults w/ inputs
        if not bvp_params is None:
            # TO DO: Change this variable name. Big change, tho.
            self.BVPopts.update(bvp_params)
        if not blender_params is None:
            # TO DO: Clean this shit up. Sloppy organization.
            if 'DefaultLayerOpts' in blender_params.keys():
                DefaultLayerOpts = blender_params.pop('DefaultLayerOpts')
                self.DefaultLayerOpts.update(DefaultLayerOpts)
            self.__dict__.update(blender_params)

    def __repr__(self):
        S = 'Class "RenderOptions":\n'+self.__dict__.__repr__()
        return S

    def apply_opts(self, scn=None, objects_to_mask=None, use_occlusion=False):
        if scn is None:
            # Get current scene if input not supplied
            scn = bpy.context.scene
        # Backwards compatibility:
        if not 'Voxels' in self.BVPopts:
            self.BVPopts['Voxels'] = False
        if not 'Motion' in self.BVPopts:
            self.BVPopts['Motion'] = False
        scn.use_nodes = True
        ## MOVED BELOW
        # # Set only first layer to be active
        # if bpy.app.version < (2, 80, 0):
        #     scn.layers = [True]+[False]*19
        # else:
        #     # NEED TO FIGURE OUT WHAT TO DO HERE
        #     pass
        if '/Scenes/' not in self.BVPopts['BasePath']:
            aa, bb = os.path.split(self.BVPopts['BasePath'])
            self.BVPopts['BasePath'] = os.path.join(aa, 'Scenes', bb)
        # Set render path
        scn.render.filepath = self.BVPopts['BasePath']  # ???
        # Get all non-function attributes
        render_params_to_set = [x for x in self.__dict__.keys() if not hasattr(
            self.__dict__[x], '__call__') and not x in ['BVPopts', 
                                                        'DefaultLayerOpts', 
                                                        'image_settings',
                                                        '_node_grid_locations']]
        for rparam in render_params_to_set:
            try:
                # define __getattr__ or whatever so self[rparam] works
                setattr(scn.render, rparam, self.__dict__[rparam])
            except:
                print('Unable to set attribute %s!' % rparam)
        # Set image settings:
        scn.render.image_settings.file_format = self.image_settings['file_format']
        scn.render.image_settings.color_mode = self.image_settings['color_mode']

        # Re-set all nodes and render layers
        for n in scn.node_tree.nodes:
            scn.node_tree.nodes.remove(n)
        if bpy.app.version < (2, 80, 0):
            old_render_layers = bpy.context.scene.render.layers.keys()
            bpy.ops.scene.render_layer_add()
            for j in range(len(old_render_layers)):
                bpy.context.scene.render.layers.active_index = 0
                bpy.ops.scene.render_layer_remove()
            # Rename newly-added layer (with default properties) to default name
            # (Doing it in this order assures Blender won't make it, e.g., RenderLayer.001
            # if a layer named RenderLayer already exists)
            bpy.context.scene.render.layers[0].name = 'RenderLayer'
        else:
            old_view_layers = list(bpy.context.scene.view_layers)
            bpy.ops.scene.view_layer_add()
            for layer in old_view_layers:
                scn.view_layers.remove(layer)
            scn.view_layers[0].name = 'RenderLayer'

        # Add basic node setup:
        node_image_rl = scn.node_tree.nodes.new(type=RLayerNode)
        node_image_rl.location = self._node_grid_locations[0, 0]
        node_image_output = scn.node_tree.nodes.new(type=CompositorNode)
        node_image_output.location = self._node_grid_locations[0, -2]
        scn.node_tree.links.new(
            node_image_rl.outputs['Image'], node_image_output.inputs['Image'])
        scn.node_tree.links.new(
            node_image_rl.outputs['Alpha'], node_image_output.inputs['Alpha'])
        # Decide whether we're only rendering one type of output:
        single_output = sum([self.BVPopts['Image'], self.BVPopts['ObjectMasks'], self.BVPopts['Zdepth'],
                             self.BVPopts['Contours'], self.BVPopts['Axes'], self.BVPopts['Normals']]) == 1
        if bpy.app.version < (2, 80, 0):
            update = scn.update
        else:
            update = bpy.context.view_layer.update
        # Add compositor nodes for optional outputs:
        if self.BVPopts['Voxels']:
            self.SetUpVoxelization()
            update()
            return  # Special case! no other node-based options can be applied!
        if self.BVPopts['ObjectMasks']:
            self.add_object_masks(
                single_output=single_output, 
                objects_to_mask=objects_to_mask,
                use_occlusion=use_occlusion,
                )
        if self.BVPopts['Motion']:
            self.add_motion(single_output=single_output)
        if self.BVPopts['Zdepth']:
            self.add_depth(single_output=single_output)
        if self.BVPopts['Contours']:
            raise NotImplementedError('Not ready yet!')
        if self.BVPopts['Axes']:
            raise NotImplementedError('Not ready yet!')
        if self.BVPopts['Normals']:
            self.add_normals(single_output=single_output)
        if self.BVPopts['Clay']:
            raise NotImplementedError('Not ready yet!')
            #self.AddClayLayerNodes(Is_RenderOnlyClay=single_output)
        if not self.BVPopts['Image']:
            # Switch all properties from one of the file output nodes to the composite output
            # Grab a random output node to get path from it as main path
            all_output_nodes = [
                n for n in scn.node_tree.nodes if n.type == 'OUTPUT_FILE']
            output = all_output_nodes[0]
            # Find input to this node
            link_to_output = [
                this_link for this_link in scn.node_tree.links if this_link.to_node == output][0]
            node_input = link_to_output.from_socket
            # Remove all input to composite node:
            NodeComposite = [
                n for n in scn.node_tree.nodes if n.type == 'COMPOSITE'][0]
            L = [L for L in scn.node_tree.links if L.to_node == NodeComposite]
            for ll in L:
                scn.node_tree.links.remove(ll)
            # Make link from input to file output to composite output:
            scn.node_tree.links.new(node_input, NodeComposite.inputs['Image'])
            # Update Scene info to reflect node info:
            scn.render.filepath = output.base_path+output.file_slots[0].path
            scn.render.image_settings.file_format = output.format.file_format
            # Get rid of old file output
            scn.node_tree.nodes.remove(output)
            # Get rid of render layer that renders image:
            RL = scn.render.layers['RenderLayer']
            scn.render.layers.remove(RL)
            # Turn off raytracing??

        update()
        # Set only first layer to be active
        if bpy.app.version < (2, 80, 0):
            scn.layers = [True]+[False]*19
        else:
            # NEED TO FIGURE OUT WHAT TO DO HERE
            pass
    """
    Notes on nodes: The following functions add various types of compositor nodes to a scene in Blender.
    These allow output of other image files that represent other "meta-information" (e.g. Z depth, 
    normals, etc) that is separate from the pixel-by-pixel color / luminance information in standard images. 
    To add nodes: NewNode = nt.nodes.new(type=NodeType) 
    See top of code for list of node types used.
    """

    def add_object_masks(self, 
                        scn=None,
                        single_output=False,
                        objects_to_mask=None,
                        use_occlusion=True):
        """Adds compositor nodes to render out object masks.

        Parameters
        ----------
        scn : bpy.data.scene | None (default=None)
            Leave as default (None) for now. Placeholder for future code updates.
        single_output : bool
            Whether to render ONLY masks.

        Notes
        -----
        The current implementation relies on objects being linked into Blender scene (without creating proxies), or being 
        mesh objects. Older versions of the code filtered objects by whether or not they had any parent object. The old 
        way may be useful, if object insertion methods change.
        IMPORTANT: 
        If scenes are created with many objects off-camera, this code will create a mask for EVERY off-scene object. 
        These masks will not be in the scene, but blender will render an image (an all-black image) for each and 
        every one of them.
        """
        if not scn:
            scn = bpy.context.scene
        scn.use_nodes = True
        scn.render.use_compositing = True
        if bpy.app.version < (2, 80, 0):
            layers = scn.layers
        else:
            layers = scn.view_layers
            assert scn.render.engine == 'CYCLES', "'C.scene.render.engine must be 'CYCLES' for mask rendering!"
        #####################################################################################
        ### --- First: Allocate pass indices to objects (or group/collection-objects) --- ###
        #####################################################################################
        if bpy.app.version >= (2, 80, 0):
            scene_collections = list(scn.collection.children)
            if (len(scene_collections) == 1) and ('Collection' in scene_collections[0].name):
                # Basic setup is engaged
                bg_collection = scene_collections[0]
                bg_collection.name = 'bg_unmasked'
            elif 'bg_unmasked' in [x.name for x in scene_collections]:
                bg_collection = bpy.data.collections['bg_unmasked']
            else:
                bg_collection = None
        if objects_to_mask is None:
            # Also constraint objects...
            disallowed_names = ['BG_', 'CamTar', 'Shadow_']
            objects_to_mask = [o for o in bpy.context.scene.objects if not any(
                [x in o.name for x in disallowed_names])]
        print(">>> Masking:")
        print(objects_to_mask)
        object_count = 1
        to_skip = []
        for o in objects_to_mask:
            if o.name in to_skip:
                continue
            # Check for dupli groups:
            if o.type == 'EMPTY':
                if bpy.app.version < (2, 80, 0):
                    if o.dupli_group:
                        o.pass_index = object_count
                        for po in o.dupli_group.objects:
                            po.pass_index = object_count
                        #bvpu.blender.set_layers(o, [0, object_count])
                        object_count += 1
            # Check for mesh objects:
            elif o.type in ('MESH', 'CURVE'):
                print(o.type)
                print('assigning pass index %d to %s' % (object_count, o.name))
                o.pass_index = object_count
                # change w/ 2.8+
                #bvpu.blender.set_layers(o, [0, object_count])
                if bpy.app.version < (2, 80, 0):
                    ug = o.users_group
                else:
                    ug = o.users_collection
                
                if len(ug) > 0:
                    if ug[0].name != 'bg_unmasked':
                        # If group is top-level collection, do not 
                        # select all siblings
                        for sibling in ug[0].objects:
                            to_skip.append(sibling.name)
                            print('assigning pass index %d to %s' %
                                (object_count, sibling.name))
                            sibling.pass_index = object_count
                            # change w/ 2.8+
                            if bpy.app.version < (2, 80, 0):
                                bvpu.blender.set_layers(sibling, [0, object_count])
                object_count += 1
            # Other types of objects??
        n_objects_masked = object_count - 1
        #####################################################################
        ### ---            Second: Set up render layers:              --- ###
        #####################################################################
        render_layer_names = layers.keys()
        if not 'object_mask_00' in render_layer_names:
            for iob in range(n_objects_masked):
                ob_layer = layers.new('object_mask_%02d' % (iob))
                for this_property in dir(ob_layer):
                    if 'use' in this_property:
                        ob_layer.__setattr__(this_property, False)
                # Necessary for masks to work
                ob_layer.use = True
                ob_layer.use_solid = True
                ob_layer.use_pass_object_index = True
                # Necessary for object indices to work for transparent materials
                # Unclear what if anything to do in 2.8+
                if bpy.app.version < (2, 80, 0):
                    ob_layer.use_ztransp = True
                if use_occlusion:
                    # Do only one layer, and none of the below
                    break
                if bpy.app.version < (2, 80, 0):
                    # Set layers on which object appears
                    layers = [False for x in range(20)]
                    layers[iob+1] = True
                    ob_layer.layers = tuple(layers)
                else:
                    # Create new collection and remove other collections
                    # from this view layer
                    collection_name = 'object_mask_%02d'%iob
                    bvpu.blender.grab_only(objects_to_mask[iob])
                    bpy.ops.collection.create(name=collection_name)
                    new_collection = bpy.data.collections[collection_name]
                    if new_collection not in list(scn.collection.children):
                        scn.collection.children.link(new_collection)
        else:
            raise Exception('object_mask layers already exist!')
        # Loop through to remove 
        object_layers = [x for x in layers.keys() if 'object_mask' in x]
        object_collections = [x for x in bpy.data.collections if 'object' in x.name]
        assert len(object_layers) == len(objects_to_mask), '%d object layers, %d masks'%(len(object_layers), len(objects_to_mask))
        assert len(object_layers) == len(object_collections)

        for iob in range(n_objects_masked):
            ob_layer = layers['object_mask_%02d'%iob]
            for this_collection in ob_layer.layer_collection.children:
                if this_collection.name != 'object_mask_%02d'%iob:
                    this_collection.exclude = True

        #####################################################################
        ### ---            Third: Set up compositor nodes:            --- ###
        #####################################################################
        nt = scn.node_tree
        # Object index nodes (pass_index=100 is for skies!)
        pass_idx = [o.pass_index for o in scn.objects if o.pass_index < 100]
        max_pi = max(pass_idx)
        grid = self._node_grid_locations[6:6 + len(pass_idx) * 2, :]
        print('Found %d pass indices' % (max_pi))
        for iob in range(max_pi):
            # Render layer
            if use_occlusion:
                if iob == 0:
                    node_rl = nt.nodes.new(type=RLayerNode)
                    node_rl.layer = 'object_mask_%02d' % (iob)
                    node_rl.location = grid[iob * 2, 0]
            else:
                node_rl = nt.nodes.new(type=RLayerNode)
                node_rl.layer = 'object_mask_%02d' % (iob)
                node_rl.location = grid[iob * 2, 0]

            # View
            node_view = nt.nodes.new(ViewerNode)
            node_view.name = 'ID Mask %d View' % (iob)
            node_view.location = grid[iob*2 + 1, -1]
            # ID mask
            node_id_mask = nt.nodes.new(IDmaskNode)
            node_id_mask.name = 'ID Mask %d' % (iob)
            node_id_mask.index = iob+1
            node_id_mask.location = grid[iob * 2, 1]
            # Output
            node_file_output = nt.nodes.new(OutputFileNode)
            node_file_output.location = grid[iob * 2, -2]
            node_file_output.format.file_format = 'PNG'
            node_file_output.base_path = scn.render.filepath.replace(
                '/Scenes/', '/Masks/')
            endCut = node_file_output.base_path.index('Masks/')+len('Masks/')
            # Set unique name per frame
            node_file_output.file_slots[0].path = node_file_output.base_path[endCut:] + \
                '_m%02d' % (iob)
            node_file_output.name = 'Object %d' % (iob)
            # Set base path
            node_file_output.base_path = node_file_output.base_path[:endCut]

            # Link nodes
            nt.links.new(node_rl.outputs['IndexOB'],
                         node_id_mask.inputs['ID value'])
            nt.links.new(node_id_mask.outputs['Alpha'], node_file_output.inputs[0])
            nt.links.new(node_id_mask.outputs['Alpha'], node_view.inputs['Image'])
            
            
            

    def add_depth(self, scn=None, single_output=False):
        """Adds compositor nodes to render out Z buffer
        """
        if not scn:
            scn = bpy.context.scene
        scn.use_nodes = True
        scn.render.use_compositing = True
        grid = self._node_grid_locations[1:3]
        #####################################################################
        ### ---                Set up render layers:                  --- ###
        #####################################################################
        render_layer_names = scn.render.layers.keys()
        if not 'Zdepth' in render_layer_names:
            ob_layer = scn.render.layers.new('Zdepth')
            for k in self.DefaultLayerOpts.keys():
                ob_layer.__setattr__(k, self.DefaultLayerOpts[k])
            # Necessary for z depth to work for transparent materials ?
            ob_layer.use_ztransp = True
            ob_layer.use_pass_z = True  # Principal interest
            ob_layer.use_pass_object_index = True  # for masking out depth of sky dome
        else:
            raise Exception('Zdepth layer already exists!')
        ########################################################################
        ### ---                Set up compositor nodes:                  --- ###
        ########################################################################
        nt = scn.node_tree
        # Get all node names (keys)
        node_rl = nt.nodes.new(type=RLayerNode)
        node_rl.layer = 'Zdepth'
        node_rl.location = grid[0, 0]
        # Zero out all depth info from the sky dome (the sky doesn't have any depth!)
        node_sky_id = nt.nodes.new(IDmaskNode)
        # No AA for z depth! doesn't work to combine non-AA node w/ AA node!
        node_sky_id.use_antialiasing = False
        node_sky_id.index = 100
        node_sky_id.location = grid[1, 1]
        nt.links.new(node_rl.outputs['IndexOB'], node_sky_id.inputs['ID value'])
        # Invert (ID) alpha layer, so sky values are zero, objects/bg are 1
        node_invert_value = nt.nodes.new(MathNode)
        node_invert_value.operation = 'SUBTRACT'        
        node_invert_value.inputs[0].default_value = 1.0
        node_invert_value.location = grid[0, 2]
        nt.links.new(node_sky_id.outputs[0], node_invert_value.inputs[1])
        # Mask out sky by multiplying with inverted sky mask
        node_multiply = nt.nodes.new(MathNode)
        node_multiply.operation = 'MULTIPLY'
        node_multiply.location = grid[0, 3]
        nt.links.new(node_rl.outputs['Depth'], node_multiply.inputs[0])
        nt.links.new(node_invert_value.outputs[0], node_multiply.inputs[1])
        # Add 1000 to the sky to distinguish it from other masks
        node_multiply1000 = nt.nodes.new(MathNode)
        node_multiply1000.operation = 'MULTIPLY'
        node_multiply1000.inputs[0].default_value = 1000.0
        node_multiply1000.location = grid[1, 3]
        nt.links.new(node_multiply1000.inputs[1], node_sky_id.outputs[0])
        # Add 1000 value back to depth image
        node_add_1000 = nt.nodes.new(MathNode)
        node_add_1000.operation = 'ADD'
        node_add_1000.inputs[0].default_value = 1000.0
        node_add_1000.location = grid[0, 4]
        nt.links.new(node_multiply.outputs[0], node_add_1000.inputs[0])
        nt.links.new(node_multiply1000.outputs[0], node_add_1000.inputs[1])
        # Depth output node
        node_depth_output = nt.nodes.new(OutputFileNode)
        node_depth_output.location = grid[0, -2]
        node_depth_output.format.file_format = 'OPEN_EXR'  # Changed 2012.10.24
        if '/Masks/' in scn.render.filepath:
            node_depth_output.base_path = scn.render.filepath[0:-4]  # get rid of "_m01"
            node_depth_output.base_path = node_depth_output.base_path.replace(
                '/Masks/', '/Zdepth/')+'_z'
        elif '/Motion/' in scn.render.filepath:
            node_depth_output.base_path = scn.render.filepath[0:-4]  # get rid of "_mot"
            node_depth_output.base_path = node_depth_output.base_path.replace(
                '/Motion/', '/Zdepth/')+'_z'
        elif '/Normals/' in scn.render.filepath:
            node_depth_output.base_path = scn.render.filepath[0:-4]  # get rid of "_nor"
            node_depth_output.base_path = node_depth_output.base_path.replace(
                '/Normals/', '/Zdepth/')+'_z'
        else:
            node_depth_output.base_path = scn.render.filepath.replace(
                '/Scenes/', '/Zdepth/')
            # Set unique name per frame
            endCut = node_depth_output.base_path.index('Zdepth/')+len('Zdepth/')
            node_depth_output.file_slots[0].path = node_depth_output.base_path[endCut:]+'_z'
            # Set base path
            node_depth_output.base_path = node_depth_output.base_path[:endCut]
        nt.links.new(node_add_1000.outputs[0], node_depth_output.inputs[0])
        # View node
        node_view = nt.nodes.new(ViewerNode)
        node_view.location = grid[1, -1]
        nt.links.new(node_add_1000.outputs[0], node_view.inputs['Image'])
        
    def add_normals(self, scn=None, single_output=False):
        """Adds compositor nodes to render out surface normals
        
        Parameters
        ----------
        scn : blender scene instance
            scene to which to add normals. Defaults to current scene.
        single_output : bool
            Whether normals will be the only rendered output from the scene
        """
        if not scn:
            scn = bpy.context.scene
        scn.use_nodes = True
        scn.render.use_compositing = True
        grid = self._node_grid_locations[3:6]
        #####################################################################
        ### ---                Set up render layers:                  --- ###
        #####################################################################
        render_layer_names = scn.render.layers.keys()
        if not 'Normals' in render_layer_names:
            ob_layer = scn.render.layers.new('Normals')
            for k in self.DefaultLayerOpts.keys():
                ob_layer.__setattr__(k, self.DefaultLayerOpts[k])
            render_layer_names.append('Normals')
            # Necessary for Normals to work for transparent materials ?
            ob_layer.use_ztransp = True
            ob_layer.use_pass_normal = True  # Principal interest
            ob_layer.use_pass_object_index = True  # for masking out sky dome normals
        else:
            raise Exception('Normal layer already exists!')
        ########################################################################
        ### ---                 Set up compositor nodes:                 --- ###
        ########################################################################
        nt = scn.node_tree
        node_rl = nt.nodes.new(type=RLayerNode)
        node_rl.layer = 'Normals'
        node_rl.location = grid[0, 0]
        # Normal output nodes
        # (1) Split normal channels
        node_split_normals = nt.nodes.new(type=SepRGBANode)
        node_split_normals.location = grid[0, 2]
        nt.links.new(node_rl.outputs['Normal'], node_split_normals.inputs['Image'])
        # (2) Zero out all normals on the sky dome (the sky doesn't really curve!)
        node_sky_id = nt.nodes.new(IDmaskNode)
        node_sky_id.use_antialiasing = True
        node_sky_id.index = 100
        node_sky_id.location = grid[1, 1]
        nt.links.new(node_rl.outputs['IndexOB'], node_sky_id.inputs['ID value'])
        # Invert alpha layer, so sky values are zero
        node_invert_value = nt.nodes.new(MathNode)
        node_invert_value.operation = 'SUBTRACT'
        node_invert_value.inputs[0].default_value = 1.0
        node_invert_value.location = grid[1, 2]
        nt.links.new(node_sky_id.outputs[0], node_invert_value.inputs[1])
        # (3) re-combine to RGB image
        node_combine_normals = nt.nodes.new(type=CombRGBANode)
        node_combine_normals.location = grid[1, -3]
        # Normal values go from -1 to 1, but image formats won't support that, so we will add 1
        # and store a floating-point value from to 0-2 in an .hdr file
        for iMap in range(3):
            # For masking out sky:
            node_multiply = nt.nodes.new(MathNode)
            node_multiply.operation = 'MULTIPLY'
            node_multiply.location = grid[iMap, 3]
            # For adding 1 to normal values:
            node_add1 = nt.nodes.new(MathNode)
            node_add1.operation = 'ADD'
            node_add1.inputs[1].default_value = 1.0
            node_add1.location = grid[iMap, 4]
            # Link nodes for order of computation:
            # multiply by inverse of sky alpha:
            nt.links.new(node_split_normals.outputs['RGB'[iMap]], node_multiply.inputs[0])
            nt.links.new(node_invert_value.outputs['Value'], node_multiply.inputs[1])
            # Add 1:
            nt.links.new(node_multiply.outputs['Value'], node_add1.inputs[0])
            # Re-combine:
            nt.links.new(node_add1.outputs['Value'], node_combine_normals.inputs['RGB'[iMap]])
        # Normal output node
        node_normal_output = nt.nodes.new(OutputFileNode)
        node_normal_output.location = grid[0, -2]
        node_normal_output.format.file_format = 'OPEN_EXR'  # 'PNG'
        node_normal_output.name = 'fOutput Normals'
        nt.links.new(node_combine_normals.outputs['Image'], node_normal_output.inputs[0])
        # If any other node is the principal node, replace (output folder) with /Normals/:
        if '/Masks/' in scn.render.filepath:
            node_normal_output.base_path = scn.render.filepath[0:-4]  # get rid of "_m01"
            node_normal_output.base_path = node_normal_output.base_path.replace(
                '/Masks/', '/Normals/')+'_z'
        elif '/Motion/' in scn.render.filepath:
            node_normal_output.base_path = scn.render.filepath[0:-4]  # get rid of "_mot"
            node_normal_output.base_path = node_normal_output.base_path.replace(
                '/Motion/', '/Normals/')+'_mot'
        elif '/Zdepth/' in scn.render.filepath:
            node_normal_output.base_path = node_normal_output.base_path[0:-2]  # remove '_z'
            node_normal_output.base_path = scn.render.filepath.replace(
                '/Zdepth/', '/Scenes/')+'_nor'
        else:
            node_normal_output.base_path = scn.render.filepath.replace(
                '/Scenes/', '/Normals/')
            # Set unique name per frame
            print(node_normal_output.base_path)
            endCut = node_normal_output.base_path.index('Normals/')+len('Normals/')
            node_normal_output.file_slots[0].path = node_normal_output.base_path[endCut:]+'_nor'
            # Set base path
            node_normal_output.base_path = node_normal_output.base_path[:endCut]
        nt.links.new(node_combine_normals.outputs['Image'], node_normal_output.inputs[0])
        # View
        node_view = nt.nodes.new(ViewerNode)
        node_view.location = grid[2, -1]
        nt.links.new(
            node_combine_normals.outputs['Image'], node_view.inputs['Image'])
        

    def add_motion(self, scn=None, single_output=False):
        """Adds compositor nodes to render motion (optical flow, a.k.a. vector pass)

        Parameters
        ----------
        scn : bpy scene instance | None. default = None
            Leave as default (None) for now. For potential future code upgrades
        single_output : bool
            Whether optical flow will be the only rendered output from the scene
        """
        if not scn:
            scn = bpy.context.scene
        scn.use_nodes = True
        scn.render.use_compositing = True
        #####################################################################
        ### ---                Set up render layers:                  --- ###
        #####################################################################
        RL = scn.render.layers.keys()
        if not 'Motion' in RL:
            bpy.ops.scene.render_layer_add()
            # Seems like there should be a "name" input argument, but not yet so we have to be hacky about this:
            ob_layer = [x for x in scn.render.layers.keys() if not x in RL]
            ob_layer = scn.render.layers[ob_layer[0]]
            # /Hacky
            # Set default layer options
            for k in self.DefaultLayerOpts.keys():
                ob_layer.__setattr__(k, self.DefaultLayerOpts[k])
            # And set motion-specific layer options
            ob_layer.name = 'Motion'
            ob_layer.use_pass_vector = True  # Motion layer
            # Necessary (?) for motion to work for transparent materials
            ob_layer.use_ztransp = True
            ob_layer.use_pass_z = True  # Necessary (?)
            #ob_layer.use_pass_object_index = True # for masking out depth of sky dome
            RL.append('Motion')
        else:
            raise Exception('Motion layer already exists!')
        ########################################################################
        ### ---                Set up compositor nodes:                  --- ###
        ########################################################################
        nt = scn.node_tree
        # Get all node names (keys)
        node_rl = nt.nodes.new(type=RLayerNode)
        node_rl.layer = 'Motion'

        # QUESTION: Better to zero out motion in sky?? NO for now,
        # but leave here in case we want the option later...
        if False:
            # Zero out all depth info from the sky dome (the sky doesn't have any depth!)
            node_sky_id = nt.nodes.new(IDmaskNode)
            # No AA for z depth! doesn't work to combine non-AA node w/ AA node!
            node_sky_id.use_antialiasing = False
            node_sky_id.index = 100
            nt.links.new(node_rl.outputs['IndexOB'],
                         node_sky_id.inputs['ID value'])
            node_invert_value = nt.nodes.new(MathNode)
            node_invert_value.operation = 'SUBTRACT'
            # Invert (ID) alpha layer, so sky values are zero, objects/bg are 1
            node_invert_value.inputs[0].default_value = 1.0
            nt.links.new(node_sky_id.outputs[0], node_invert_value.inputs[1])
            # Mask out sky by multiplying with inverted sky mask
            node_multiply = nt.nodes.new(MathNode)
            node_multiply.operation = 'MULTIPLY'
            nt.links.new(node_rl.outputs['Speed'], node_multiply.inputs[0])
            nt.links.new(node_invert_value.outputs[0], node_multiply.inputs[1])
            # Add 1000 to the sky:
            node_multiply1000 = nt.nodes.new(MathNode)
            node_multiply1000.operation = 'MULTIPLY'
            node_multiply1000.inputs[0].default_value = 1000.0
            nt.links.new(node_multiply1000.inputs[1], node_sky_id.outputs[0])
            node_add_1000 = nt.nodes.new(MathNode)
            node_add_1000.operation = 'ADD'
            node_add_1000.inputs[0].default_value = 1000.0
            nt.links.new(node_multiply.outputs[0], node_add_1000.inputs[0])
            nt.links.new(node_multiply1000.outputs[0], node_add_1000.inputs[1])

        # Depth output node
        MotionOut = nt.nodes.new(OutputFileNode)
        MotionOut.location = bmu.Vector((0., 300.))
        MotionOut.format.file_format = 'OPEN_EXR'
        if '/Masks/' in scn.render.filepath:
            # get rid of "_m01"
            MotionOut.base_path = scn.render.filepath[0:-4]
            MotionOut.base_path = node_depth_output.base_path.replace(
                '/Masks/', '/Motion/')+'_mot'
        elif '/Normals/' in scn.render.filepath:
            # get rid of "_nor"
            MotionOut.base_path = scn.render.filepath[0:-4]
            MotionOut.base_path = node_depth_output.base_path.replace(
                '/Normals/', '/Motion/')+'_mot'
        elif '/Zdepth/' in scn.render.filepath:
            MotionOut.base_path = scn.render.filepath[0:-2]  # get rid of "_z"
            MotionOut.base_path = node_depth_output.base_path.replace(
                '/Zdepth/', '/Motion/')+'_mot'
        else:
            MotionOut.base_path = scn.render.filepath.replace(
                '/Scenes/', '/Motion/')
            # Set unique name per frame
            endCut = MotionOut.base_path.index('Motion/')+len('Motion/')
            MotionOut.file_slots[0].path = MotionOut.base_path[endCut:]+'_mot'
            # Set base path
            MotionOut.base_path = MotionOut.base_path[:endCut]

        nt.links.new(node_rl.outputs['Speed'], MotionOut.inputs[0])

    def SetUpVoxelization(self, scn=None):
        """
        Set up Blender for rendering images to create 3D voxelization of an object
        NOTE: This sets up camera, rendering engine, and materials - NOT camera trajectory!
        """
        #, xL=(-5, 5), yL=(-5, 5), zL=(0, 10), nGrid=10, fix=None
        import math
        if scn is None:
            scn = bpy.context.scene
        # Set renderer to cycles
        scn.render.engine = 'CYCLES'
        # Set camera to cycles, fisheye equisolid, 360 deg fov
        Cam = [o for o in bpy.context.scene.objects if o.type == 'CAMERA']
        if len(Cam) == 1:
            Cam = Cam[0]
        else:
            raise Exception('Zero or >1 camera in your scene! WTF!!')
        Cam.data.type = 'PANO'
        Cam.data.cycles.fisheye_fov = math.pi*2.
        Cam.data.cycles.panorama_type = 'FISHEYE_EQUISOLID'

        # Get all-white cycles emission material
        fpath = os.path.join(bvp_basedir, 'BlendFiles')
        fName = 'Cycles_Render.blend'
        MatNm = 'CycWhite'
        bpy.ops.wm.link_append(
            # i.e., directory WITHIN .blend file (Scenes / Objects / Materials)
            directory=os.path.join(fpath, fName)+"\\Material\\",
            # local filepath within .blend file to the material to be imported
            filepath="//"+fName+"\\Material\\"+'CycWhite',
            # "filename" being the name of the data block, i.e. the name of the material.
            filename='CycWhite',
            link=False,
            relative_path=False,
        )

        # For all dupli-objects in scene, create proxies
        for bOb in bpy.context.scene.objects:
            # Create proxies for all objects within object
            if bOb.dupli_group:
                for o in bOb.dupli_group.objects:
                    bvpu.blender.grab_only(bOb)
                    # , object=bOb.name, type=o.name)
                    bpy.ops.object.proxy_make(object=o.name)
                # Get rid of linked group now that dupli group objects are imported
                bpy.context.scene.objects.unlink(bOb)
        # Change all materials to white Cycles emission material ("CycWhite", imported above)
        for nOb in bpy.context.scene.objects:
            for m in nOb.material_slots:
                m.material = bpy.data.materials['CycWhite']

    @classmethod
    def from_blend(cls, scn=None, bvp_params=None, blender_params=None):
        """Initialize render options from a given blend file

        bvp_params : dict
            bvp_params to override defaults
        blender_params : dict
            dict to override any params found in file
        """
        pass
