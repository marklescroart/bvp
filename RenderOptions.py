"""
Class to control BVP Render options 
"""
# Imports
import bvp,os,sys
import math as bnp
from bvp.utils.blender import set_layers
from bvp.utils.basics import fixedKeyDict
if bvp.Is_Blender:
	import bpy
	import mathutils as bmu # "B lender M ath U tilities"
# The "type" input for compositor node creation has been arbitrarily changed 
# numerous times throughout Blender API development. This is EXTREMELY 
# IRRITATING. Nonetheless, the format may change again, so I've collected
# all the node type IDs here and use the variables below

#['R_LAYERS', 'COMPOSITE', 'R_LAYERS', 'VIEWER', 'ID_MASK', 'OUTPUT_FILE', 'R_LAYERS', 'VIEWER', 'ID_MASK', 'OUTPUT_FILE']
if sys.platform == 'darwin':
	print('Mac computer node names!')
	RLayerNodeX = 'R_LAYERS' 
	CompositorNodeX = 'COMPOSITE'
	OutputFileNodeX = 'OUTPUT_FILE'
	ViewerNodeX = 'VIEWER'
	SepRGBANodeX = 'CompositorNodeSepRGBA'
	CombRGBANodeX = 'CompositorNodeCombRGBA'
	IDmaskNodeX = 'ID_MASK'
	MathNodeX = 'CompositorNodeMath'
else:
	RLayerNodeX = 'CompositorNodeRLayers' 
	CompositorNodeX = 'CompositorNodeComposite'
	OutputFileNodeX = 'CompositorNodeOutputFile'
	ViewerNodeX = 'CompositorNodeViewer'
	SepRGBANodeX = 'CompositorNodeSepRGBA'
	CombRGBANodeX = 'CompositorNodeCombRGBA'
	IDmaskNodeX = 'CompositorNodeIDMask'
	MathNodeX = 'CompositorNodeMath'

# else:
RLayerNode = 'CompositorNodeRLayers' 
CompositorNode = 'CompositorNodeComposite'
OutputFileNode = 'CompositorNodeOutputFile'
ViewerNode = 'CompositorNodeViewer'
SepRGBANode = 'CompositorNodeSepRGBA'
CombRGBANode = 'CompositorNodeCombRGBA'
IDmaskNode = 'CompositorNodeIDMask'
MathNode = 'CompositorNodeMath'

class RenderOptions(object):
	'''
	Class for storing render options for a scene. 
		
	'''
	def __init__(self,rParams={}):
		'''
		Usage: RenderOptions(rParams={})
		Class for storing render options for a scene (or scenes).
		See code for default rendering options.
		Update any of these values with rParams dictionary input

		NOTE: RenderOptions no longer touches a scene's file path; it only provides the base file (parent directory) for all rendering.
		bvpScene's "apply_opts" function should be the only one to mess with bpy.context.scene.filepath (!!) (2012.03.12)
		'''
		
		self.use_freestyle = False # May need some clever if statement here - checking on version of blender
		if self.use_freestyle:
			pass
			# Freestyle settings. Not used yet; freestyle is still not ready for primetime (2013.03.05)
			#FSlineThickness = 3.0
			#FSlineCol = (0.0,0.0,0.0)			
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
		self.image_settings = {}
		self.image_settings['color_mode'] = 'RGBA'
		self.image_settings['file_format'] = 'PNG'

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
			"Voxels":False,
			"ObjectMasks":False,
			"Motion":False,
			"Zdepth":False,
			"Contours":False, #Freestyle, yet to be implemented
			"Axes":False, # based on N.Cornea code, for now - still unfinished
			"Normals":False, # Not yet implemented
			"Clay":False, # Not yet implemented - All shape, no material / texture (over-ride w/ plain [clay] material) lighting??
			"Type":'FirstFrame', # other options: "All","FirstAndLastFrame",'every4th'
			"RenderFile":os.path.join(bvp.__path__[0],'Scripts','BlenderRender.py'),
			"BasePath":'/auto/k1/mark/Desktop/BlenderTemp/', # Replace with settings!
			}
		# Disallow updates that add fields
		self.__dict__ = fixedKeyDict(self.__dict__)
		# Update defaults w/ inputs
		if 'BVPopts' in rParams.keys():
			BVPopts = rParams.pop('BVPopts')
			self.BVPopts.update(BVPopts)
		if 'DefaultLayerOpts' in rParams.keys():
			DefaultLayerOpts = rParams.pop('DefaultLayerOpts')
			self.DefaultLayerOpts.update(DefaultLayerOpts)
		self.__dict__.update(rParams)
	def __repr__(self):
		S = 'Class "RenderOptions":\n'+self.__dict__.__repr__()
		return S
	
	def apply_opts(self,Scn=None):
		if not Scn:
			# Get current scene if input not supplied
			Scn = bpy.context.scene
		# Backwards compatibility:
		if not 'Voxels' in self.BVPopts:
			self.BVPopts['Voxels'] = False
		if not 'Motion' in self.BVPopts:
			self.BVPopts['Motion'] = False
		Scn.use_nodes = True
		# Set only first layer to be active
		Scn.layers = [True]+[False]*19
		# Get all non-function attributes
		ToSet = [x for x in self.__dict__.keys() if not hasattr(self.__dict__[x],'__call__') and not x in ['BVPopts','DefaultLayerOpts','image_settings']]
		for s in ToSet:
			try:
				setattr(Scn.render,s,self.__dict__[s])
			except:
				print('Unable to set attribute %s!'%s)
		# Set image settings:
		Scn.render.image_settings.file_format = self.image_settings['file_format']
		Scn.render.image_settings.color_mode = self.image_settings['color_mode']

		# Re-set all nodes and render layers:
		for n in Scn.node_tree.nodes:
			Scn.node_tree.nodes.remove(n)
		RL = bpy.context.scene.render.layers.keys()
		bpy.ops.scene.render_layer_add()
		for ii,n in enumerate(RL):
			bpy.context.scene.render.layers.active_index=0
			bpy.ops.scene.render_layer_remove()
		# Rename newly-added layer (with default properties) to default name:
		bpy.context.scene.render.layers[0].name = 'RenderLayer'
		# Add basic node setup:
		RL = Scn.node_tree.nodes.new(type=RLayerNode)
		CompOut = Scn.node_tree.nodes.new(type=CompositorNode)
		Scn.node_tree.links.new(RL.outputs['Image'],CompOut.inputs['Image'])
		Scn.node_tree.links.new(RL.outputs['Alpha'],CompOut.inputs['Alpha'])
		# Decide whether we're only rendering one type of output:
		SingleOutput = sum([self.BVPopts['Image'],self.BVPopts['ObjectMasks'],self.BVPopts['Zdepth'],
						self.BVPopts['Contours'],self.BVPopts['Axes'],self.BVPopts['Normals']])==1
		# Add compositor nodes for optional outputs:
		if self.BVPopts['Voxels']:
			self.SetUpVoxelization()
			Scn.update()
			return # Special case! no other node-based options can be applied!
		if self.BVPopts['ObjectMasks']:
			self.AddObjectMaskLayerNodes(Is_RenderOnlyMasks=SingleOutput)
		if self.BVPopts['Motion']:
			self.AddMotionLayerNodes(Is_RenderOnlyMotion=SingleOutput)
		if self.BVPopts['Zdepth']:
			self.AddZdepthLayerNodes(Is_RenderOnlyZ=SingleOutput)
		if self.BVPopts['Contours']:
			raise Exception('Not ready yet!')
		if self.BVPopts['Axes']:
			raise Exception('Not ready yet!')
		if self.BVPopts['Normals']:
			self.AddNormalLayerNodes(Is_RenderOnlyNormal=SingleOutput)
		if self.BVPopts['Clay']:
			raise Exception('Not ready yet!')
			#self.AddClayLayerNodes(Is_RenderOnlyClay=SingleOutput)
		if not self.BVPopts['Image']:
			# Switch all properties from one of the file output nodes to the composite output
			# Grab a node
			aa = [N for N in Scn.node_tree.nodes if N.type==OutputFileNodeX]
			print([a.type for a in Scn.node_tree.nodes])
			fOut = aa[0]
			# Find input to this node
			Lnk = [L for L in Scn.node_tree.links if L.to_node == fOut][0]
			Input = Lnk.from_socket
			# Remove all input to composite node:
			NodeComposite = [N for N in Scn.node_tree.nodes if N.type==CompositorNodeX][0]
			L = [L for L in Scn.node_tree.links if L.to_node==NodeComposite]
			for ll in L:
				Scn.node_tree.links.remove(ll)
			# Make link from input to file output to composite output:
			Scn.node_tree.links.new(Input,NodeComposite.inputs['Image'])
			# Update Scene info to reflect node info:
			Scn.render.filepath = fOut.base_path+fOut.file_slots[0].path
			Scn.render.image_settings.file_format = fOut.format.file_format
			# Get rid of old file output
			Scn.node_tree.nodes.remove(fOut)
			# Get rid of render layer that renders image:
			RL = Scn.render.layers['RenderLayer']
			Scn.render.layers.remove(RL)
			# Turn off raytracing??

		Scn.update()
	'''
	Notes on nodes: The following functions add various types of compositor nodes to a scene in Blender.
	These allow output of other image files that represent other "meta-information" (e.g. Z depth, 
	normals, etc) that is separate from the pixel-by-pixel color / luminance information in standard images. 
	To add nodes: NewNode = NT.nodes.new(type=NodeType) 
	See top of code for list of node types used.
	'''
	def AddObjectMaskLayerNodes(self,Scn=None,Is_RenderOnlyMasks=False):
		'''Adds compositor nodes to render out object masks.

		Parameters
		----------
		Scn : bpy.data.scene | None (default=None)
			Leave as default (None) for now. Placeholder for future code updates.
		Is_RenderOnlyMasks : bool


		Notes
		-----
		The current implementation relies on objects being linked into Blender scene (without creating proxies), or being 
		mesh objects. Older versions of the code filtered objects by whether or not they had any parent object. The old 
		way may be useful, if object insertion methods change.
		IMPORTANT: 
		If scenes are created with many objects off-camera, this code will create a mask for EVERY off-scene object. 
		These masks will not be in the scene, but blender will render an image (an all-black image) for each and 
		every one of them.
		
		ML 2012.01
 		'''
		if not Scn:
			Scn = bpy.context.scene
		Scn.use_nodes = True
		Scn.render.use_compositing = True
		########################################################################
		### --- First: Allocate all objects' pass indices (and groups??) --- ### 
		########################################################################
		DisallowedNames = ['BG_','CamTar','Shadow_'] # Also constraint objects...
		Ob = [o for o in bpy.context.scene.objects if not any([x in o.name for x in DisallowedNames])]
		PassCt = 1
		for o in Ob:
			# Check for dupli groups:
			if o.type=='EMPTY':
				if o.dupli_group:
					o.pass_index = PassCt
					for po in o.dupli_group.objects:
						po.pass_index = PassCt
					set_layers(o,[0,PassCt])
					PassCt +=1
			# Check for mesh objects:
			elif o.type=='MESH':
				o.pass_index = PassCt
				set_layers(o,[0,PassCt])
				PassCt +=1
			# Other types of objects?? 
		
		## OLD WAY: For all objects with NO parents (top-level objects), set increasing pass indices
		#Par = [x.parent for x in Ob if x.parent!=None]
		#NoPar = [x for x in Ob if x.parent==None]
		# For all objects that ARE parents, assign the children the same pass index.
		#for p in Par:
		#    bpy.ops.object.select_all(action='DESELECT')
		#    bpy.ops.object.select_name(name=p.name,extend=False)
		#    bpy.ops.object.select_grouped(extend =True,type='CHILDREN_RECURSIVE')
		#    ChildGrp = bpy.context.selected_editable_objects
		#    for Child in ChildGrp:
		#        Child.pass_index = p.pass_index
		
		#####################################################################
		### ---            Second: Set up render layers:              --- ### 
		#####################################################################
		RL = Scn.render.layers.keys()
		if not 'ObjectMasks1' in RL:
			for iOb in range(PassCt-1):
				bpy.ops.scene.render_layer_add() # Seems like there should be a "name" input argument, but not yet so we have to be hacky about this:
				ObLayer = [x for x in Scn.render.layers.keys() if not x in RL]
				ObLayer = Scn.render.layers[ObLayer[0]]
				for k in self.DefaultLayerOpts.keys():
					ObLayer.__setattr__(k,self.DefaultLayerOpts[k])
				ObLayer.name = 'ObjectMasks%d'%(iOb+1)
				RL.append('ObjectMasks%d'%(iOb+1))
				Lay = [False for x in range(20)];
				Lay[iOb+1] = True 
				ObLayer.layers = tuple(Lay)
				ObLayer.use_ztransp = True # Necessary for object indices to work for transparent materials
				ObLayer.use_pass_object_index = True # This one only
		else:
			raise Exception('ObjectMasks layers already exist!')
		########################################################################
		### ---            Third: Set up compositor nodes:               --- ### 
		########################################################################
		NT = Scn.node_tree
		# Object index nodes:
		PassIdx = [o.pass_index for o in Scn.objects if o.pass_index < 100] # 100 is for skies!
		MaxPI = max(PassIdx)
		if bvp.Verbosity_Level > 3:
			print('I think there are %d pass indices'%(MaxPI))
		for iObIdx in range(MaxPI):
			NodeRL = NT.nodes.new(type=RLayerNode)
			NodeRL.layer = 'ObjectMasks%d'%(iObIdx+1)

			NewVwNode = NT.nodes.new(ViewerNode)
			NewIDNode = NT.nodes.new(IDmaskNode)
			NewIDOut = NT.nodes.new(OutputFileNode)
			
			VwNm = 'ID Mask %d View'%(iObIdx+1)
			NewVwNode.name = VwNm
			
			IDNm = 'ID Mask %d'%(iObIdx+1)
			NewIDNode.name = IDNm
			NewIDNode.index = iObIdx+1
			# Link nodes
			NT.links.new(NodeRL.outputs['IndexOB'],NewIDNode.inputs['ID value'])
			NT.links.new(NewIDNode.outputs['Alpha'],NewIDOut.inputs[0])
			NT.links.new(NewIDNode.outputs['Alpha'],NewVwNode.inputs['Image'])
			NewIDOut.format.file_format = 'PNG'
			NewIDOut.base_path = Scn.render.filepath.replace('/Scenes/','/Masks/')
			endCut = NewIDOut.base_path.index('Masks/')+len('Masks/')
			# Set unique name per frame
			NewIDOut.file_slots[0].path = NewIDOut.base_path[endCut:]+'_m%02d'%(iObIdx+1)
			NewIDOut.name = 'Object %d'%(iObIdx)
			# Set base path
			NewIDOut.base_path = NewIDOut.base_path[:endCut]
			# Set location with NewIdNode.location = ((x,y))
			nPerRow = 8.
			Loc = bvp.bmu.Vector((bnp.modf(iObIdx/nPerRow)[0]*nPerRow,-bnp.modf(iObIdx/nPerRow)[1]))
			Offset = 250.
			Loc = Loc*Offset - bvp.bmu.Vector((nPerRow/2. * Offset - 300.,100.))  # hard-coded to be below RL node
			NewIDNode.location = Loc
			NewVwNode.location = Loc - bvp.bmu.Vector((0.,100))
			NewIDOut.location = Loc - bvp.bmu.Vector((-150.,100))
	def AddZdepthLayerNodes(self,Scn=None,Is_RenderOnlyZ=False):
		'''
		Usage: AddZdepthLayerNodes(Scn=None,Is_RenderOnlyZ=False)

		Adds compositor nodes to render out Z buffer

		ML 2012.01
		'''
		if not Scn:
			Scn = bpy.context.scene
		Scn.use_nodes = True
		Scn.render.use_compositing = True
		#####################################################################
		### ---                Set up render layers:                  --- ### 
		#####################################################################
		RL = Scn.render.layers.keys()
		if not 'Zdepth' in RL:
			bpy.ops.scene.render_layer_add() # Seems like there should be a "name" input argument, but not yet so we have to be hacky about this:
			ObLayer = [x for x in Scn.render.layers.keys() if not x in RL]
			ObLayer = Scn.render.layers[ObLayer[0]]
			for k in self.DefaultLayerOpts.keys():
				ObLayer.__setattr__(k,self.DefaultLayerOpts[k])
			ObLayer.name = 'Zdepth'
			RL.append('Zdepth')
			ObLayer.use_ztransp = True # Necessary for z depth to work for transparent materials ?
			ObLayer.use_pass_z = True # Principal interest
			ObLayer.use_pass_object_index = True # for masking out depth of sky dome 
		else:
			raise Exception('Zdepth layer already exists!')
		########################################################################
		### ---                Set up compositor nodes:                  --- ### 
		########################################################################
		NT = Scn.node_tree
		# Get all node names (keys)
		NodeRL = NT.nodes.new(type=RLayerNode)
		NodeRL.layer = 'Zdepth'

		# Zero out all depth info from the sky dome (the sky doesn't have any depth!)
		NodeSky = NT.nodes.new(IDmaskNode)
		NodeSky.use_antialiasing = False  #No AA for z depth! doesn't work to combine non-AA node w/ AA node!
		NodeSky.index = 100
		NT.links.new(NodeRL.outputs['IndexOB'],NodeSky.inputs['ID value'])
		NodeInv = NT.nodes.new(MathNode)
		NodeInv.operation = 'SUBTRACT'
		# Invert (ID) alpha layer, so sky values are zero, objects/bg are 1
		NodeInv.inputs[0].default_value = 1.0
		NT.links.new(NodeSky.outputs[0],NodeInv.inputs[1])
		# Mask out sky by multiplying with inverted sky mask
		NodeMult = NT.nodes.new(MathNode)
		NodeMult.operation = 'MULTIPLY'
		NT.links.new(NodeRL.outputs['Z'],NodeMult.inputs[0])
		NT.links.new(NodeInv.outputs[0],NodeMult.inputs[1])
		# Add 1000 to the sky:
		NodeMult1000 = NT.nodes.new(MathNode)
		NodeMult1000.operation = 'MULTIPLY'
		NodeMult1000.inputs[0].default_value = 1000.0
		NT.links.new(NodeMult1000.inputs[1],NodeSky.outputs[0])
		NodeAdd1000 = NT.nodes.new(MathNode)
		NodeAdd1000.operation = 'ADD'
		NodeAdd1000.inputs[0].default_value = 1000.0
		NT.links.new(NodeMult.outputs[0],NodeAdd1000.inputs[0])
		NT.links.new(NodeMult1000.outputs[0],NodeAdd1000.inputs[1])

		# Depth output node
		DepthOut = NT.nodes.new(OutputFileNode)
		DepthOut.location =  bvp.bmu.Vector((900.,300.))
		DepthOut.format.file_format = 'OPEN_EXR' # Changed 2012.10.24
		if '/Masks/' in Scn.render.filepath: 
			DepthOut.base_path = Scn.render.filepath[0:-4] # get rid of "_m01"
			DepthOut.base_path = DepthOut.base_path.replace('/Masks/','/Zdepth/')+'_z'
		elif '/Motion/' in Scn.render.filepath:
			DepthOut.base_path = Scn.render.filepath[0:-4] # get rid of "_mot"
			DepthOut.base_path = DepthOut.base_path.replace('/Motion/','/Zdepth/')+'_z'
		elif '/Normals/' in Scn.render.filepath:
			DepthOut.base_path = Scn.render.filepath[0:-4] # get rid of "_nor"
			DepthOut.base_path = DepthOut.base_path.replace('/Normals/','/Zdepth/')+'_z'
		else:
			DepthOut.base_path = Scn.render.filepath.replace('/Scenes/','/Zdepth/')
			# Set unique name per frame
			endCut = DepthOut.base_path.index('Zdepth/')+len('Zdepth/')
			DepthOut.file_slots[0].path = DepthOut.base_path[endCut:]+'_z'
			# Set base path
			DepthOut.base_path = DepthOut.base_path[:endCut]

		NT.links.new(NodeAdd1000.outputs[0],DepthOut.inputs[0])
			
	def AddNormalLayerNodes(self,Scn=None,Is_RenderOnlyNormal=False):
		'''
		Usage: AddNormalLayerNodes(Scn=None,Is_RenderOnlyNormal=False)

		Adds compositor nodes to render out Normals

		ML 2012.01
		'''
		if not Scn:
			Scn = bpy.context.scene
		Scn.use_nodes = True
		Scn.render.use_compositing = True
		#####################################################################
		### ---                Set up render layers:                  --- ### 
		#####################################################################
		RL = Scn.render.layers.keys()
		if not 'Normals' in RL:
			bpy.ops.scene.render_layer_add() # Seems like there should be a "name" input argument, but not yet so we have to be hacky about this:
			ObLayer = [x for x in Scn.render.layers.keys() if not x in RL]
			ObLayer = Scn.render.layers[ObLayer[0]]
			for k in self.DefaultLayerOpts.keys():
				ObLayer.__setattr__(k,self.DefaultLayerOpts[k])
			ObLayer.name = 'Normals'
			RL.append('Normals')
			ObLayer.use_ztransp = True # Necessary for Normals to work for transparent materials ?
			ObLayer.use_pass_normal = True # Principal interest
			ObLayer.use_pass_object_index = True # for masking out sky dome normals
		else:
			raise Exception('Normal layer already exists!')
		########################################################################
		### ---                 Set up compositor nodes:                 --- ### 
		########################################################################
		# TO DO: Make a sensible layout for these, i.e. set .location field for all nodes (not urgent...)
		NT = Scn.node_tree
		NodeRL = NT.nodes.new(type=RLayerNode)
		NodeRL.layer = 'Normals'
		# Normal output nodes
		# (1) Split normal channels
		NorSpl = NT.nodes.new(type=SepRGBANode)
		NT.links.new(NodeRL.outputs['Normal'],NorSpl.inputs['Image'])
		NorSpl.location = NodeRL.location + bvp.bmu.Vector((600.,0))
		UpDown = [75.,0.,-75.]
		# (2) Zero out all normals on the sky dome (the sky doesn't really curve!)
		NodeSky = NT.nodes.new(IDmaskNode)
		NodeSky.use_antialiasing = True
		NodeSky.index = 100
		NT.links.new(NodeRL.outputs['IndexOB'],NodeSky.inputs['ID value'])
		NodeInv = NT.nodes.new(MathNode)
		NodeInv.operation = 'SUBTRACT'
		# Invert alpha layer, so sky values are zero
		NodeInv.inputs[0].default_value = 1.0
		NT.links.new(NodeSky.outputs[0],NodeInv.inputs[1])
		# (3) re-combine to RGB image
		NorCom = NT.nodes.new(type=CombRGBANode)
		NorCom.location = NodeRL.location + bvp.bmu.Vector((1050.,0.))
		# Normal values go from -1 to 1, but image formats won't support that, so we will add 1 
		# and store a floating-point value from to 0-2 in an .hdr file
		for iMap in range(3):
			# For masking out sky:
			NodeMult = NT.nodes.new(MathNode)
			NodeMult.operation = 'MULTIPLY'
			# For adding 1 to normal values:
			NodeAdd1 = NT.nodes.new(MathNode)
			NodeAdd1.operation = 'ADD'
			NodeAdd1.inputs[1].default_value = 1.0
			# Link nodes for order of computation:
			# multiply by inverse of sky alpha: 
			NT.links.new(NorSpl.outputs['RGB'[iMap]],NodeMult.inputs[0])
			NT.links.new(NodeInv.outputs['Value'],NodeMult.inputs[1])
			# Add 1:
			NT.links.new(NodeMult.outputs['Value'],NodeAdd1.inputs[0])
			# Re-combine:
			NT.links.new(NodeAdd1.outputs['Value'],NorCom.inputs['RGB'[iMap]])
		# Normal output node
		NorOut = NT.nodes.new(OutputFileNode)
		NorOut.location = NodeRL.location + bvp.bmu.Vector((1200.,0.))
		NorOut.format.file_format = 'OPEN_EXR' #'PNG'
		NorOut.name = 'fOutput Normals'
		NT.links.new(NorCom.outputs['Image'],NorOut.inputs[0])
		# If any other node is the principal node, replace (output folder) with /Normals/:
		if '/Masks/' in Scn.render.filepath:
			NorOut.base_path = Scn.render.filepath[0:-4] # get rid of "_m01"
			NorOut.base_path = NorOut.base_path.replace('/Masks/','/Normals/')+'_z'
		elif '/Motion/' in Scn.render.filepath:
			NorOut.base_path = Scn.render.filepath[0:-4] # get rid of "_mot"
			NorOut.base_path = NorOut.base_path.replace('/Motion/','/Normals/')+'_mot'
		elif '/Zdepth/' in Scn.render.filepath:
			NorOut.base_path = NorOut.base_path[0:-2] # remove '_z'	
			NorOut.base_path = Scn.render.filepath.replace('/Zdepth/','/Scenes/')+'_nor'
		else:
			NorOut.base_path = Scn.render.filepath.replace('/Scenes/','/Normals/')
			# Set unique name per frame
			print(NorOut.base_path)
			endCut = NorOut.base_path.index('Normals/')+len('Normals/')
			NorOut.file_slots[0].path = NorOut.base_path[endCut:]+'_nor'
			# Set base path
			NorOut.base_path = NorOut.base_path[:endCut]
		NT.links.new(NorCom.outputs['Image'],NorOut.inputs[0])
	def AddMotionLayerNodes(self,Scn=None,Is_RenderOnlyMotion=False):
		'''Adds compositor nodes to render motion (optical flow, a.k.a. vector pass)

		Parameters
		----------
		Scn : bpy scene instance | None. default = None
			Leave as default (None) for now. For potential future code upgrades
		Is_RenderOnlyMotion : bool
			Set True if optical flow is the only desired output of the render
		'''
		if not Scn:
			Scn = bpy.context.scene
		Scn.use_nodes = True
		Scn.render.use_compositing = True
		#####################################################################
		### ---                Set up render layers:                  --- ### 
		#####################################################################
		RL = Scn.render.layers.keys()
		if not 'Motion' in RL:
			bpy.ops.scene.render_layer_add() 
			# Seems like there should be a "name" input argument, but not yet so we have to be hacky about this:
			ObLayer = [x for x in Scn.render.layers.keys() if not x in RL]
			ObLayer = Scn.render.layers[ObLayer[0]]
			# /Hacky
			# Set default layer options
			for k in self.DefaultLayerOpts.keys():
				ObLayer.__setattr__(k,self.DefaultLayerOpts[k])
			# And set motion-specific layer options
			ObLayer.name = 'Motion'
			ObLayer.use_pass_vector = True # Motion layer
			ObLayer.use_ztransp = True # Necessary (?) for motion to work for transparent materials
			ObLayer.use_pass_z = True # Necessary (?)
			#ObLayer.use_pass_object_index = True # for masking out depth of sky dome 
			RL.append('Motion')
		else:
			raise Exception('Motion layer already exists!')
		########################################################################
		### ---                Set up compositor nodes:                  --- ### 
		########################################################################
		NT = Scn.node_tree
		# Get all node names (keys)
		NodeRL = NT.nodes.new(type=RLayerNode)
		NodeRL.layer = 'Motion'

		# QUESTION: Better to zero out motion in sky?? NO for now, 
		# but leave here in case we want the option later...
		if False:
			# Zero out all depth info from the sky dome (the sky doesn't have any depth!)
			NodeSky = NT.nodes.new(IDmaskNode)
			NodeSky.use_antialiasing = False  #No AA for z depth! doesn't work to combine non-AA node w/ AA node!
			NodeSky.index = 100
			NT.links.new(NodeRL.outputs['IndexOB'],NodeSky.inputs['ID value'])
			NodeInv = NT.nodes.new(MathNode)
			NodeInv.operation = 'SUBTRACT'
			# Invert (ID) alpha layer, so sky values are zero, objects/bg are 1
			NodeInv.inputs[0].default_value = 1.0
			NT.links.new(NodeSky.outputs[0],NodeInv.inputs[1])
			# Mask out sky by multiplying with inverted sky mask
			NodeMult = NT.nodes.new(MathNode)
			NodeMult.operation = 'MULTIPLY'
			NT.links.new(NodeRL.outputs['Speed'],NodeMult.inputs[0])
			NT.links.new(NodeInv.outputs[0],NodeMult.inputs[1])
			# Add 1000 to the sky:
			NodeMult1000 = NT.nodes.new(MathNode)
			NodeMult1000.operation = 'MULTIPLY'
			NodeMult1000.inputs[0].default_value = 1000.0
			NT.links.new(NodeMult1000.inputs[1],NodeSky.outputs[0])
			NodeAdd1000 = NT.nodes.new(MathNode)
			NodeAdd1000.operation = 'ADD'
			NodeAdd1000.inputs[0].default_value = 1000.0
			NT.links.new(NodeMult.outputs[0],NodeAdd1000.inputs[0])
			NT.links.new(NodeMult1000.outputs[0],NodeAdd1000.inputs[1])

		# Depth output node
		MotionOut = NT.nodes.new(OutputFileNode)
		MotionOut.location =  bvp.bmu.Vector((0.,300.))
		MotionOut.format.file_format = 'OPEN_EXR' # Changed 2012.10.24
		if '/Masks/' in Scn.render.filepath: 
			MotionOut.base_path = Scn.render.filepath[0:-4] # get rid of "_m01"
			MotionOut.base_path = DepthOut.base_path.replace('/Masks/','/Motion/')+'_mot'
		elif '/Normals/' in Scn.render.filepath:
			MotionOut.base_path = Scn.render.filepath[0:-4] # get rid of "_nor"
			MotionOut.base_path = DepthOut.base_path.replace('/Normals/','/Motion/')+'_mot'
		elif '/Zdepth/' in Scn.render.filepath:
			MotionOut.base_path = Scn.render.filepath[0:-2] # get rid of "_z"
			MotionOut.base_path = DepthOut.base_path.replace('/Zdepth/','/Motion/')+'_mot'
		else:
			MotionOut.base_path = Scn.render.filepath.replace('/Scenes/','/Motion/')
			# Set unique name per frame
			endCut = MotionOut.base_path.index('Motion/')+len('Motion/')
			MotionOut.file_slots[0].path = MotionOut.base_path[endCut:]+'_mot'
			# Set base path
			MotionOut.base_path = MotionOut.base_path[:endCut]

		NT.links.new(NodeRL.outputs['Speed'],MotionOut.inputs[0])

	def SetUpVoxelization(self,Scn=None):
		"""
		Set up Blender for rendering images to create 3D voxelization of an object
		NOTE: This sets up camera, rendering engine, and materials - NOT camera trajectory!
		"""
		#,xL=(-5,5),yL=(-5,5),zL=(0,10),nGrid=10,fix=None
		import math
		if Scn is None:
			Scn = bpy.context.scene
		# Set renderer to cycles
		Scn.render.engine = 'CYCLES'
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
		fPath,bvpfNm = os.path.split(bvp.__file__)
		fPath = os.path.join(fPath,'BlendFiles')
		fName = 'Cycles_Render.blend'
		MatNm = 'CycWhite'
		bpy.ops.wm.link_append(
			directory=os.path.join(fPath,fName)+"\\Material\\", # i.e., directory WITHIN .blend file (Scenes / Objects / Materials)
			filepath="//"+fName+"\\Material\\"+'CycWhite', # local filepath within .blend file to the material to be imported
			filename='CycWhite', # "filename" being the name of the data block, i.e. the name of the material.
			link=False,
			relative_path=False,
			)
		if bvp.Verbosity_Level >= 3:
			print('loaded "CycWhite" material!')
		
		# For all dupli-objects in scene, create proxies
		for bOb in bpy.context.scene.objects:
			# Create proxies for all objects within object
			if bOb.dupli_group:
				for o in bOb.dupli_group.objects:
					bvp.utils.blender.grab_only(bOb)
					bpy.ops.object.proxy_make(object=o.name) #,object=bOb.name,type=o.name)
				# Get rid of linked group now that dupli group objects are imported
				bpy.context.scene.objects.unlink(bOb)
		# Change all materials to white Cycles emission material ("CycWhite", imported above)
		for nOb in bpy.context.scene.objects:
			for m in nOb.material_slots:
				m.material = bpy.data.materials['CycWhite']

