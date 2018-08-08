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
from .. import utils as bvpu
from ..options import config

try:
    import bpy
    import mathutils as bmu
    is_blender = True
except ImportError:
    is_blender = False

bvp_basedir = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                           '../', '../'))
render_dir = os.path.expanduser(config.get('path', 'render_dir'))
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
        
        self.use_freestyle = False # May need some clever if statement here - checking on version of blender
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
        self.resolution_x = 512
        self.resolution_y = 512
        self.resolution_percentage = 100
        self.tile_x = 64 # More?
        self.tile_y = 64 # More?
        # Fields not in bpy.data.scene.render class:
        # Image settings: File format and color mode
        self.image_settings = dict(color_mode='RGBA',
                                   file_format='PNG')
        
        self.DefaultLayerOpts = {
            'layers':tuple([True]*20), 
            'use_zmask':False, 
            'use_all_z':False, 
            'use_solid':True, # Necessary for almost everything
            'use_halo':False, 
            'use_ztransp':False, 
            'use_sky':False, 
            'use_edge_enhance':False, 
            'use_strand':False, 
            'use_freestyle':False, 
            'use_pass_combined':False, 
            'use_pass_z':False, 
            'use_pass_vector':False, 
            'use_pass_normal':False, 
            'use_pass_uv':False, 
            'use_pass_mist':False, 
            'use_pass_object_index':False, 
            'use_pass_color':False, 
            'use_pass_diffuse':False, 
            'use_pass_specular':False, 
            'use_pass_shadow':False, 
            'use_pass_emit':False, 
            'use_pass_ambient_occlusion':False, 
            'use_pass_environment':False, 
            'use_pass_indirect':False, 
            'use_pass_reflection':False, 
            'use_pass_refraction':False, 
            }
        self.BVPopts = {
            # BVP specific rendering options
            "Image":True, 
            "Voxels":False, # Not yet implemented reliably. 
            "ObjectMasks":False, 
            "Motion":False, # Not yet implemented reliably. Buggy AF
            "Zdepth":False, 
            "Contours":False, #Freestyle, yet to be implemented
            "Axes":False, # based on N.Cornea code, for now - still unfinished
            "Normals":False,
            "Clay":False, # Not yet implemented - All shape, no material / texture (over-ride w/ plain [clay] material) lighting??
            "Type":'FirstFrame', # other options: "All", "FirstAndLastFrame", 'every4th'
            "RenderFile":render_file, 
            "BasePath":render_dir, 
            }
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
    
    def apply_opts(self, scn=None):
        if scn is None:
            # Get current scene if input not supplied
            scn = bpy.context.scene
        # Backwards compatibility:
        if not 'Voxels' in self.BVPopts:
            self.BVPopts['Voxels'] = False
        if not 'Motion' in self.BVPopts:
            self.BVPopts['Motion'] = False
        scn.use_nodes = True
        # Set only first layer to be active
        scn.layers = [True]+[False]*19
        # Get all non-function attributes
        ToSet = [x for x in self.__dict__.keys() if not hasattr(self.__dict__[x], '__call__') and not x in ['BVPopts', 'DefaultLayerOpts', 'image_settings']]
        for s in ToSet:
            try:
                setattr(scn.render, s, self.__dict__[s]) # define __getattr__ or whatever so self[s] works
            except:
                print('Unable to set attribute %s!'%s)
        # Set image settings:
        scn.render.image_settings.file_format = self.image_settings['file_format']
        scn.render.image_settings.color_mode = self.image_settings['color_mode']

        # Re-set all nodes and render layers
        for n in scn.node_tree.nodes:
            scn.node_tree.nodes.remove(n)
        old_render_layers = bpy.context.scene.render.layers.keys()
        bpy.ops.scene.render_layer_add()
        for ii in range(len(old_render_layers)):
            bpy.context.scene.render.layers.active_index = 0
            bpy.ops.scene.render_layer_remove()
        # Rename newly-added layer (with default properties) to default name
        # (Doing it in this order assures Blender won't make it, e.g., RenderLayer.001
        # if a layer named RenderLayer already exists)
        bpy.context.scene.render.layers[0].name = 'RenderLayer'
        # Add basic node setup:
        RL = scn.node_tree.nodes.new(type=RLayerNode)
        compositor_output = scn.node_tree.nodes.new(type=CompositorNode)
        scn.node_tree.links.new(RL.outputs['Image'], compositor_output.inputs['Image'])
        scn.node_tree.links.new(RL.outputs['Alpha'], compositor_output.inputs['Alpha'])
        # Decide whether we're only rendering one type of output:
        single_output = sum([self.BVPopts['Image'], self.BVPopts['ObjectMasks'], self.BVPopts['Zdepth'], 
                        self.BVPopts['Contours'], self.BVPopts['Axes'], self.BVPopts['Normals']])==1
        # Add compositor nodes for optional outputs:
        if self.BVPopts['Voxels']:
            self.SetUpVoxelization()
            scn.update()
            return # Special case! no other node-based options can be applied!
        if self.BVPopts['ObjectMasks']:
            self.add_object_masks(single_output=single_output)
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
            # Grab a node
            aa = [N for N in scn.node_tree.nodes if N.type==OutputFileNodeX]
            print([a.type for a in scn.node_tree.nodes])
            output = aa[0]
            # Find input to this node
            Lnk = [L for L in scn.node_tree.links if L.to_node == output][0]
            Input = Lnk.from_socket
            # Remove all input to composite node:
            NodeComposite = [N for N in scn.node_tree.nodes if N.type==CompositorNodeX][0]
            L = [L for L in scn.node_tree.links if L.to_node==NodeComposite]
            for ll in L:
                scn.node_tree.links.remove(ll)
            # Make link from input to file output to composite output:
            scn.node_tree.links.new(Input, NodeComposite.inputs['Image'])
            # Update Scene info to reflect node info:
            scn.render.filepath = output.base_path+output.file_slots[0].path
            scn.render.image_settings.file_format = output.format.file_format
            # Get rid of old file output
            scn.node_tree.nodes.remove(output)
            # Get rid of render layer that renders image:
            RL = scn.render.layers['RenderLayer']
            scn.render.layers.remove(RL)
            # Turn off raytracing??

        scn.update()
    """
    Notes on nodes: The following functions add various types of compositor nodes to a scene in Blender.
    These allow output of other image files that represent other "meta-information" (e.g. Z depth, 
    normals, etc) that is separate from the pixel-by-pixel color / luminance information in standard images. 
    To add nodes: NewNode = nt.nodes.new(type=NodeType) 
    See top of code for list of node types used.
    """
    def add_object_masks(self, scn=None, single_output=False):
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
        ########################################################################
        ### --- First: Allocate all objects' pass indices (and groups??) --- ### 
        ########################################################################
        DisallowedNames = ['BG_', 'CamTar', 'Shadow_'] # Also constraint objects...
        Ob = [o for o in bpy.context.scene.objects if not any([x in o.name for x in DisallowedNames])]
        PassCt = 1
        for o in Ob:
            # Check for dupli groups:
            if o.type=='EMPTY':
                if o.dupli_group:
                    o.pass_index = PassCt
                    for po in o.dupli_group.objects:
                        po.pass_index = PassCt
                    bvpu.blender.set_layers(o, [0, PassCt])
                    PassCt +=1
            # Check for mesh objects:
            elif o.type=='MESH':
                o.pass_index = PassCt
                bvpu.blender.set_layers(o, [0, PassCt])
                PassCt +=1
            # Other types of objects?? 
        
        #####################################################################
        ### ---            Second: Set up render layers:              --- ### 
        #####################################################################
        RL = scn.render.layers.keys()
        if not 'ObjectMasks1' in RL:
            for iob in range(PassCt-1):
                ob_layer = scn.render.layers.new('ObjectMasks%d'%(iob + 1))
                for k, v in self.DefaultLayerOpts.items():
                    ob_layer.__setattr__(k, v)
                layers = [False for x in range(20)];
                layers[iob+1] = True 
                ob_layer.layers = tuple(layers)
                ob_layer.use_ztransp = True # Necessary for object indices to work for transparent materials
                ob_layer.use_pass_object_index = True # This one only
        else:
            raise Exception('ObjectMasks layers already exist!')
        ########################################################################
        ### ---            Third: Set up compositor nodes:               --- ### 
        ########################################################################
        nt = scn.node_tree
        # Object index nodes (pass_index=100 is for skies!)
        pass_idx = [o.pass_index for o in scn.objects if o.pass_index < 100]
        max_pi = max(pass_idx)
        print('Found %d pass indices'%(max_pi))
        for iob in range(max_pi):
            node_rl = nt.nodes.new(type=RLayerNode)
            node_rl.layer = 'ObjectMasks%d'%(iob + 1)

            NewVwNode = nt.nodes.new(ViewerNode)
            NewIDNode = nt.nodes.new(IDmaskNode)
            NewIDOut = nt.nodes.new(OutputFileNode)
            
            VwNm = 'ID Mask %d View'%(iob+1)
            NewVwNode.name = VwNm
            
            IDNm = 'ID Mask %d'%(iob+1)
            NewIDNode.name = IDNm
            NewIDNode.index = iob+1
            # Link nodes
            nt.links.new(node_rl.outputs['IndexOB'], NewIDNode.inputs['ID value'])
            nt.links.new(NewIDNode.outputs['Alpha'], NewIDOut.inputs[0])
            nt.links.new(NewIDNode.outputs['Alpha'], NewVwNode.inputs['Image'])
            NewIDOut.format.file_format = 'PNG'
            NewIDOut.base_path = scn.render.filepath.replace('/Scenes/', '/Masks/')
            endCut = NewIDOut.base_path.index('Masks/')+len('Masks/')
            # Set unique name per frame
            NewIDOut.file_slots[0].path = NewIDOut.base_path[endCut:]+'_m%02d'%(iob+1)
            NewIDOut.name = 'Object %d'%(iob)
            # Set base path
            NewIDOut.base_path = NewIDOut.base_path[:endCut]
            # Set location with NewIdNode.location = ((x, y))
            nPerRow = 8.
            Loc = bmu.Vector((bnp.modf(iob/nPerRow)[0]*nPerRow, -bnp.modf(iob/nPerRow)[1]))
            Offset = 250.
            Loc = Loc*Offset - bmu.Vector((nPerRow/2. * Offset - 300., 100.))  # hard-coded to be below RL node
            NewIDNode.location = Loc
            NewVwNode.location = Loc - bmu.Vector((0., 100))
            NewIDOut.location = Loc - bmu.Vector((-150., 100))

    def add_depth(self, scn=None, single_output=False):
        """Adds compositor nodes to render out Z buffer
        """
        if not scn:
            scn = bpy.context.scene
        scn.use_nodes = True
        scn.render.use_compositing = True
        #####################################################################
        ### ---                Set up render layers:                  --- ### 
        #####################################################################
        RL = scn.render.layers.keys()
        if not 'Zdepth' in RL:
            #bpy.ops.scene.render_layer_add() # Seems like there should be a "name" input argument, but not yet so we have to be hacky about this:
            #ob_layer = [x for x in scn.render.layers.keys() if not x in RL]
            #ob_layer = scn.render.layers[ob_layer[0]]
            ob_layer = scn.render.layers.new('Zdepth')
            for k in self.DefaultLayerOpts.keys():
                ob_layer.__setattr__(k, self.DefaultLayerOpts[k])
            #ob_layer.name = 'Zdepth'
            #RL.append('Zdepth')
            ob_layer.use_ztransp = True # Necessary for z depth to work for transparent materials ?
            ob_layer.use_pass_z = True # Principal interest
            ob_layer.use_pass_object_index = True # for masking out depth of sky dome 
        else:
            raise Exception('Zdepth layer already exists!')
        ########################################################################
        ### ---                Set up compositor nodes:                  --- ### 
        ########################################################################
        nt = scn.node_tree
        # Get all node names (keys)
        node_rl = nt.nodes.new(type=RLayerNode)
        node_rl.layer = 'Zdepth'

        # Zero out all depth info from the sky dome (the sky doesn't have any depth!)
        NodeSky = nt.nodes.new(IDmaskNode)
        NodeSky.use_antialiasing = False  #No AA for z depth! doesn't work to combine non-AA node w/ AA node!
        NodeSky.index = 100
        nt.links.new(node_rl.outputs['IndexOB'], NodeSky.inputs['ID value'])
        NodeInv = nt.nodes.new(MathNode)
        NodeInv.operation = 'SUBTRACT'
        # Invert (ID) alpha layer, so sky values are zero, objects/bg are 1
        NodeInv.inputs[0].default_value = 1.0
        nt.links.new(NodeSky.outputs[0], NodeInv.inputs[1])
        # Mask out sky by multiplying with inverted sky mask
        NodeMult = nt.nodes.new(MathNode)
        NodeMult.operation = 'MULTIPLY'
        nt.links.new(node_rl.outputs['Depth'], NodeMult.inputs[0])
        nt.links.new(NodeInv.outputs[0], NodeMult.inputs[1])
        # Add 1000 to the sky:
        NodeMult1000 = nt.nodes.new(MathNode)
        NodeMult1000.operation = 'MULTIPLY'
        NodeMult1000.inputs[0].default_value = 1000.0
        nt.links.new(NodeMult1000.inputs[1], NodeSky.outputs[0])
        NodeAdd1000 = nt.nodes.new(MathNode)
        NodeAdd1000.operation = 'ADD'
        NodeAdd1000.inputs[0].default_value = 1000.0
        nt.links.new(NodeMult.outputs[0], NodeAdd1000.inputs[0])
        nt.links.new(NodeMult1000.outputs[0], NodeAdd1000.inputs[1])

        # Depth output node
        DepthOut = nt.nodes.new(OutputFileNode)
        DepthOut.location =  bmu.Vector((900., 300.))
        DepthOut.format.file_format = 'OPEN_EXR' # Changed 2012.10.24
        if '/Masks/' in scn.render.filepath: 
            DepthOut.base_path = scn.render.filepath[0:-4] # get rid of "_m01"
            DepthOut.base_path = DepthOut.base_path.replace('/Masks/', '/Zdepth/')+'_z'
        elif '/Motion/' in scn.render.filepath:
            DepthOut.base_path = scn.render.filepath[0:-4] # get rid of "_mot"
            DepthOut.base_path = DepthOut.base_path.replace('/Motion/', '/Zdepth/')+'_z'
        elif '/Normals/' in scn.render.filepath:
            DepthOut.base_path = scn.render.filepath[0:-4] # get rid of "_nor"
            DepthOut.base_path = DepthOut.base_path.replace('/Normals/', '/Zdepth/')+'_z'
        else:
            DepthOut.base_path = scn.render.filepath.replace('/Scenes/', '/Zdepth/')
            # Set unique name per frame
            endCut = DepthOut.base_path.index('Zdepth/')+len('Zdepth/')
            DepthOut.file_slots[0].path = DepthOut.base_path[endCut:]+'_z'
            # Set base path
            DepthOut.base_path = DepthOut.base_path[:endCut]

        nt.links.new(NodeAdd1000.outputs[0], DepthOut.inputs[0])
            
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
        #####################################################################
        ### ---                Set up render layers:                  --- ### 
        #####################################################################
        RL = scn.render.layers.keys()
        if not 'Normals' in RL:
            bpy.ops.scene.render_layer_add() # Seems like there should be a "name" input argument, but not yet so we have to be hacky about this:
            ob_layer = [x for x in scn.render.layers.keys() if not x in RL]
            ob_layer = scn.render.layers[ob_layer[0]]
            for k in self.DefaultLayerOpts.keys():
                ob_layer.__setattr__(k, self.DefaultLayerOpts[k])
            ob_layer.name = 'Normals'
            RL.append('Normals')
            ob_layer.use_ztransp = True # Necessary for Normals to work for transparent materials ?
            ob_layer.use_pass_normal = True # Principal interest
            ob_layer.use_pass_object_index = True # for masking out sky dome normals
        else:
            raise Exception('Normal layer already exists!')
        ########################################################################
        ### ---                 Set up compositor nodes:                 --- ### 
        ########################################################################
        # TO DO: Make a sensible layout for these, i.e. set .location field for all nodes (not urgent...)
        nt = scn.node_tree
        node_rl = nt.nodes.new(type=RLayerNode)
        node_rl.layer = 'Normals'
        # Normal output nodes
        # (1) Split normal channels
        NorSpl = nt.nodes.new(type=SepRGBANode)
        nt.links.new(node_rl.outputs['Normal'], NorSpl.inputs['Image'])
        NorSpl.location = node_rl.location + bmu.Vector((600., 0))
        UpDown = [75., 0., -75.]
        # (2) Zero out all normals on the sky dome (the sky doesn't really curve!)
        NodeSky = nt.nodes.new(IDmaskNode)
        NodeSky.use_antialiasing = True
        NodeSky.index = 100
        nt.links.new(node_rl.outputs['IndexOB'], NodeSky.inputs['ID value'])
        NodeInv = nt.nodes.new(MathNode)
        NodeInv.operation = 'SUBTRACT'
        # Invert alpha layer, so sky values are zero
        NodeInv.inputs[0].default_value = 1.0
        nt.links.new(NodeSky.outputs[0], NodeInv.inputs[1])
        # (3) re-combine to RGB image
        NorCom = nt.nodes.new(type=CombRGBANode)
        NorCom.location = node_rl.location + bmu.Vector((1050., 0.))
        # Normal values go from -1 to 1, but image formats won't support that, so we will add 1 
        # and store a floating-point value from to 0-2 in an .hdr file
        for iMap in range(3):
            # For masking out sky:
            NodeMult = nt.nodes.new(MathNode)
            NodeMult.operation = 'MULTIPLY'
            # For adding 1 to normal values:
            NodeAdd1 = nt.nodes.new(MathNode)
            NodeAdd1.operation = 'ADD'
            NodeAdd1.inputs[1].default_value = 1.0
            # Link nodes for order of computation:
            # multiply by inverse of sky alpha: 
            nt.links.new(NorSpl.outputs['RGB'[iMap]], NodeMult.inputs[0])
            nt.links.new(NodeInv.outputs['Value'], NodeMult.inputs[1])
            # Add 1:
            nt.links.new(NodeMult.outputs['Value'], NodeAdd1.inputs[0])
            # Re-combine:
            nt.links.new(NodeAdd1.outputs['Value'], NorCom.inputs['RGB'[iMap]])
        # Normal output node
        NorOut = nt.nodes.new(OutputFileNode)
        NorOut.location = node_rl.location + bmu.Vector((1200., 0.))
        NorOut.format.file_format = 'OPEN_EXR' #'PNG'
        NorOut.name = 'fOutput Normals'
        nt.links.new(NorCom.outputs['Image'], NorOut.inputs[0])
        # If any other node is the principal node, replace (output folder) with /Normals/:
        if '/Masks/' in scn.render.filepath:
            NorOut.base_path = scn.render.filepath[0:-4] # get rid of "_m01"
            NorOut.base_path = NorOut.base_path.replace('/Masks/', '/Normals/')+'_z'
        elif '/Motion/' in scn.render.filepath:
            NorOut.base_path = scn.render.filepath[0:-4] # get rid of "_mot"
            NorOut.base_path = NorOut.base_path.replace('/Motion/', '/Normals/')+'_mot'
        elif '/Zdepth/' in scn.render.filepath:
            NorOut.base_path = NorOut.base_path[0:-2] # remove '_z' 
            NorOut.base_path = scn.render.filepath.replace('/Zdepth/', '/Scenes/')+'_nor'
        else:
            NorOut.base_path = scn.render.filepath.replace('/Scenes/', '/Normals/')
            # Set unique name per frame
            print(NorOut.base_path)
            endCut = NorOut.base_path.index('Normals/')+len('Normals/')
            NorOut.file_slots[0].path = NorOut.base_path[endCut:]+'_nor'
            # Set base path
            NorOut.base_path = NorOut.base_path[:endCut]
        nt.links.new(NorCom.outputs['Image'], NorOut.inputs[0])
        
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
            ob_layer.use_pass_vector = True # Motion layer
            ob_layer.use_ztransp = True # Necessary (?) for motion to work for transparent materials
            ob_layer.use_pass_z = True # Necessary (?)
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
            NodeSky = nt.nodes.new(IDmaskNode)
            NodeSky.use_antialiasing = False  #No AA for z depth! doesn't work to combine non-AA node w/ AA node!
            NodeSky.index = 100
            nt.links.new(node_rl.outputs['IndexOB'], NodeSky.inputs['ID value'])
            NodeInv = nt.nodes.new(MathNode)
            NodeInv.operation = 'SUBTRACT'
            # Invert (ID) alpha layer, so sky values are zero, objects/bg are 1
            NodeInv.inputs[0].default_value = 1.0
            nt.links.new(NodeSky.outputs[0], NodeInv.inputs[1])
            # Mask out sky by multiplying with inverted sky mask
            NodeMult = nt.nodes.new(MathNode)
            NodeMult.operation = 'MULTIPLY'
            nt.links.new(node_rl.outputs['Speed'], NodeMult.inputs[0])
            nt.links.new(NodeInv.outputs[0], NodeMult.inputs[1])
            # Add 1000 to the sky:
            NodeMult1000 = nt.nodes.new(MathNode)
            NodeMult1000.operation = 'MULTIPLY'
            NodeMult1000.inputs[0].default_value = 1000.0
            nt.links.new(NodeMult1000.inputs[1], NodeSky.outputs[0])
            NodeAdd1000 = nt.nodes.new(MathNode)
            NodeAdd1000.operation = 'ADD'
            NodeAdd1000.inputs[0].default_value = 1000.0
            nt.links.new(NodeMult.outputs[0], NodeAdd1000.inputs[0])
            nt.links.new(NodeMult1000.outputs[0], NodeAdd1000.inputs[1])

        # Depth output node
        MotionOut = nt.nodes.new(OutputFileNode)
        MotionOut.location =  bmu.Vector((0., 300.))
        MotionOut.format.file_format = 'OPEN_EXR'
        if '/Masks/' in scn.render.filepath: 
            MotionOut.base_path = scn.render.filepath[0:-4] # get rid of "_m01"
            MotionOut.base_path = DepthOut.base_path.replace('/Masks/', '/Motion/')+'_mot'
        elif '/Normals/' in scn.render.filepath:
            MotionOut.base_path = scn.render.filepath[0:-4] # get rid of "_nor"
            MotionOut.base_path = DepthOut.base_path.replace('/Normals/', '/Motion/')+'_mot'
        elif '/Zdepth/' in scn.render.filepath:
            MotionOut.base_path = scn.render.filepath[0:-2] # get rid of "_z"
            MotionOut.base_path = DepthOut.base_path.replace('/Zdepth/', '/Motion/')+'_mot'
        else:
            MotionOut.base_path = scn.render.filepath.replace('/Scenes/', '/Motion/')
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
        Cam = [o for o in bpy.context.scene.objects if o.type=='CAMERA']
        if len(Cam)==1:
            Cam = Cam[0]
        else:
            raise Exception('Zero or >1 camera in your scene! WTF!!')
        Cam.data.type='PANO'
        Cam.data.cycles.fisheye_fov = math.pi*2.
        Cam.data.cycles.panorama_type='FISHEYE_EQUISOLID'

        # Get all-white cycles emission material 
        fpath = os.path.join(bvp_basedir, 'BlendFiles')
        fName = 'Cycles_Render.blend'
        MatNm = 'CycWhite'
        bpy.ops.wm.link_append(
            directory=os.path.join(fpath, fName)+"\\Material\\", # i.e., directory WITHIN .blend file (Scenes / Objects / Materials)
            filepath="//"+fName+"\\Material\\"+'CycWhite', # local filepath within .blend file to the material to be imported
            filename='CycWhite', # "filename" being the name of the data block, i.e. the name of the material.
            link=False, 
            relative_path=False, 
            )
        
        # For all dupli-objects in scene, create proxies
        for bOb in bpy.context.scene.objects:
            # Create proxies for all objects within object
            if bOb.dupli_group:
                for o in bOb.dupli_group.objects:
                    bvpu.blender.grab_only(bOb)
                    bpy.ops.object.proxy_make(object=o.name) #, object=bOb.name, type=o.name)
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