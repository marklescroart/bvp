"""
.B.lender .V.ision .P.roject utils for functions to be used within Blender
(at Blender command line or in scripts run through Blender)
"""

import os
import random
import subprocess
import warnings
import copy
import re
import math as bnp
from six import string_types
from .bvpMath import circ_dst # 

#from ..Classes.Constraint import CamConstraint
from ..options import config

try:
    import bpy
    import mathutils as bmu
    is_blender = True
except ImportError: 
    is_blender = False

verbosity_level = 3 # Get rid of me? Implement in a better way?

def xyz2constr(xyz, ConstrType, originXYZ=(0., 0., 0.)):
    """
    Convert a cartesian (xyz) location to a constraint on azimuth 
    angle (theta), elevation angle (phi) or radius (rho).
    
    originXYZ is the origin of the coordinate system (default=(0, 0, 0))

    Returns angles in degrees.
    """
    X, Y, Z = xyz
    oX, oY, oZ = originXYZ
    X = X-oX
    Y = Y-oY
    Z = Z-oZ
    if ConstrType.lower() == 'phi':
        Out = bnp.degrees(bnp.atan2(Z, bnp.sqrt(X**2+Y**2)))
    elif ConstrType.lower() == 'theta':
        Out = bnp.degrees(bnp.atan2(Y, X))
    elif ConstrType.lower() == 'r':
        Out = (X**2+Y**2+Z**2)**.5
    return Out

def make_location_animation(location_list, frames, action_name='ObjectMotion', handle_type='VECTOR'):
    """Create a location-changing action in Blender from a list of frames and XYZ coordinates.
    
    Parameters
    ----------
    location_list : list 
        List of [x, y, z] coordinates for each frames
    frames : list of ints
        Keyframes at which to fix locations
    action_name : string
        Name for action
    handle_type : string | list
        string name to specify the types of handles on the Bezier splines
        that govern how animation interpolation is accomplished. One of:
        'VECTOR', ... [[TODO LOOK THIS UP IN BLENDER]]. A list can be 
        provided if you want different handles for different frames (must
        be on handle type per frame)
    """
    # Make handle_type input into a list of lists for use below
    if isinstance(handle_type, string_types):
        handle_type = [handle_type]*len(frames)
    for ih, h in enumerate(handle_type):
        if isinstance(h, string_types): 
            handle_type[ih] = [h]*2
        elif isinstance(h, (list,tuple)):
            if len(h)==1:
                handle_type[ih] = h*2
    a = bpy.data.actions.new(action_name)
    for iXYZ in range(3):
        a.fcurves.new('location', index=iXYZ, action_group="LocRotScale")
        a.fcurves[iXYZ].extrapolation = 'LINEAR'
        for ifr, fr in enumerate(frames):
            a.fcurves[iXYZ].keyframe_points.insert(fr, location_list[ifr][iXYZ])
            a.fcurves[iXYZ].keyframe_points[ifr].handle_left_type = handle_type[ifr][0]
            a.fcurves[iXYZ].keyframe_points[ifr].handle_right_type = handle_type[ifr][1]
        a.fcurves[iXYZ].extrapolation = 'CONSTANT'
    return a

def AddSelectedToGroup(gNm):
    """
    Adds all selected objects to group named gNm
    """
    scn = bpy.context.scene
    G = bpy.data.groups[gNm]
    ob = [o for o in scn.objects if o.select]
    for o in ob:
        G.objects.link(o)

def GetScenesToRender(SL):
    """Check on which scenes within a scene list have already been rendered.

    DEPRECATED?? Overlapping in function with something else? 
    """
    # Get number of scenes to render in one job:
    RenderGrpSize = SL.RenderOptions.BVPopts['RenderGrpSize']
    # Check on which scenes have been rendered:
    fpath, PathEnd = os.path.split(SL.RenderOptions.filepath[:-1]) # Leave out ending "/"
    # Modify PathEnd to accomodate all render types
    
    for iChk in range(1, SL.nScenes, RenderGrpSize):
        # For now: Only check images. Need to check masks, zdepth, etc...
        if not os.path.exists(os.path.join(fpath, PathEnd, 'Sc%04d_01.png'%(iChk))):
            ScnToRender = range(iChk-1, iChk+RenderGrpSize-1)
            return ScnToRender

def SetNoMemoryMode(nThreads=None, nPartsXY=6, Revert=False):
    """
    Usage: SetNoMemoryMode(nThreads=None, nPartsXY=6, Revert=False)
    During rendering, sets mode to no undos, allows how many threads 
    to specify for rendering (default = auto detect, maybe not the 
    nicest thing to do if rendering is being done on a cluster)
    Setting Revert=True undoes the changes.
    """
    scn = bpy.context.scene
    if not Revert:
        bpy.context.user_preferences.edit.use_global_undo = False
        bpy.context.user_preferences.edit.undo_steps = 0
    else:
        bpy.context.user_preferences.edit.use_global_undo = True
        bpy.context.user_preferences.edit.undo_steps = 32

    # Set threading to 1 for running multiple threads on multiple machines:
    if not nThreads:
        scn.render.threads_mode = 'AUTO'
    else: 
        scn.render.threads_mode = 'FIXED'
        scn.render.threads = nThreads
    # More parts to break up rendering...
    scn.render.tile_x = nPartsXY
    scn.render.tile_y = nPartsXY

def RemoveMeshFromMemory(MeshName):
    """
    Removes meshes from memory. Be careful with the use of this function; it can crash Blender to have meshes removed with objects that still rely on them.
    """
    Mesh = bpy.data.meshes[MeshName]
    Mesh.user_clear()
    bpy.data.meshes.remove(Mesh)

def RemoveActionFromMemory(ActionName):
    """
    Removes actions from memory. Called to clear scenes between loading / rendering scenes. Be careful, this can crash Blender! 
    """
    Act = bpy.data.actions[ActionName]
    Act.user_clear()
    bpy.data.actions.remove(Act)

def set_layers(ob, LayerList):
    """ 
    Convenience function to set layers. Note that active layers affect what will be selected with bpy select_all commands. 
    ob = blender object data structure
    LayerList = list of numbers of layers you want the object to appear on, e.g. [0, 9] (ZERO-BASED)
    """
    if not bvp.Is_Blender:
        print("Sorry, won't run outside of Blender!")
        return
    LL = [False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]
    for L in LayerList:
        LL[L] = True
    LL = tuple(LL)
    grab_only(ob)
    bpy.ops.object.move_to_layer(layers=LL)

def get_cursor():
    """Convenience function to get 3D cursor position in Blender (3D cursor marker, not mouse)

    Returns
    -------
    location : blender Vector
        X, Y, Z location of 3D cursor
    """
    # Now this is some serious bullshit. Look where Blender hides the cursor information. Just look.
    V = [x for x in bpy.data.window_managers[0].windows[0].screen.areas if x.type=='VIEW_3D'][0]
    return V.spaces[0].cursor_location

def set_cursor(location):
    """Sets 3D cursor to specified location in VIEW_3D window

    Useful to have a function for this because there is an irritatingly
    complex data structure for the cursor position in Blender's API

    Inputs
    ------
    location : list or bpy Vector
        Desired position of the cursor
    """
    V = [x for x in bpy.data.window_managers[0].windows[0].screen.areas if x.type=='VIEW_3D'][0]
    V.spaces[0].cursor_location = location

def grab_only(ob):
    """Selects the input object `ob` and and deselects everything else

    Inputs
    ------
    ob : bpy class object
        Object to be selected
    """
    if bpy.context.active_object is not None:
        if bpy.context.active_object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    bpy.ops.object.select_all(action='DESELECT')
    if isinstance(ob, bpy.types.Group):
        ob = find_group_parent(ob)
    ob.select = True
    bpy.context.scene.objects.active = ob    

def find_group_parent(group):
    """Find parent object among group objects"""
    no_parent = [o for o in group.objects if o.parent is None]
    if len(no_parent)>1:
        # OK, try for an armature:
        armatures = [o for o in group.objects if o.type=='ARMATURE']
        if len(armatures) == 1:
            return armatures[0]
        else:
            raise Exception("Can't find parent, can't find single armature")
        #raise Exception("WTF! More than one no-parent object in group!")
    return no_parent[0]

def get_mesh_objects(scn=None, select=True):
    """Returns a list of - and optionally, selects - all mesh objects in a scene
    """
    if scn is None:
        scn = bpy.context.scene
    bpy.ops.object.select_all(action='DESELECT')
    MeOb = [ob for ob in scn.objects if ob.type=='MESH']
    if select:
        for ob in MeOb:
            ob.select = True
    return MeOb

def CommitModifiers(ObList, mTypes=['Mirror', 'EdgeSplit']):
    """
    Commits mirror / subsurf / other modifiers to meshes (use before joining meshes)
    
    Modifier types to commit are specified in "mTypes"

    NOTE: This is shitty and probably broken. Fix me.
    ALSO: deprecated. The point here should be to get a pointwise mesh, and
    there are better ways to do that than this. Leaving here temporarily, will
    delete or replace soon.
    """
    Flag = {'Verbose':False}
    print('Committing modifiers...')
    for o in ObList:
        if Flag['Verbose']:
            print("Checking %s"%(o.name))
        #[any (value in item for value in v) ]
        PossMods = ['Mirror', 'EdgeSplit']
        Mods = [x for x in mTypes if x in PossMods]
        for mf in Mods:
            if mf in o.modifiers.keys():
                grab_only(o)
                m = o.modifiers[mf]
                #m.show_viewport = True # Should not be necessary - we don't want to commit any un-shown modifiers
                print("Applying %s modifier to %s"%(mf, o.name))    
                bpy.ops.object.modifier_apply(modifier=m.name)
        if 'Subsurf' in o.modifiers.keys() and 'Subsurf' in mTypes:
            grab_only(o)
            m = o.modifiers['Subsurf']
            m.show_viewport = True 
            m.levels = m.render_levels
            if m.levels > 1:
                # no need for more than 2 subsurf levels...
                m.levels = 2 
            if Flag['Verbose']:
                print("Modifier is: %s"%(m.name))
                print("Applying Subsurf modifier to %s"%(o.name))
            bpy.ops.object.modifier_apply(modifier=m.name)

def getVoxelizedVertList(obj, size=10/96., smooth=1, fNm=None, showVox=False):
    """
    Returns a list of surface point locations for a given object (or group of objects) in a regular grid. 
    Grid size is specified by "size" input.

    Inputs: 
    obj : a blender object, a blender group, or a list of objects
    size : distance between surface points. default = .2 units
    smooth : whether to smooth or not (default = 1) ## suavizado: 0 no deforma al subdividir, 1 formas organicas
    """
    verbosity_level = 5
    #print('Verbosity Level: %d'%verbosity_level)
    import time
    t0 = time.time()
    ## Get current scene:
    scn = bpy.context.scene
    # Set up no memory mode: 
    if not showVox:
        if verbosity_level>5:
            print('Setting no memory mode!')
        SetNoMemoryMode()
    # Recursive call to deal with groups with multiple objects:
    if isinstance(obj, bpy.types.Group):
        Ct = 0
        verts = []
        norms = []
        for o in obj.objects:
            v, n = getVoxelizedVertList(o, size=size, smooth=smooth, showVox=showVox)
            verts += v
            norms += n
        if fNm:
            if Ct==0:
                todo = 'w' # create / overwrite
            else:
                todo = 'a' # append
            with open(fNm, todo) as fid:
                for v in verts:
                    fid.write('%.5f, %.5f, %.5f\n'%(v[0], v[1], v[2]))
            # Skip normal output! These are fucked anyway!
            #with open(fNm, todo) as fid:
            #   for n in norms:
            #       fid.write('%.5f, %.5f, %.5f\n'%(n[0], n[1], n[2]))
            Ct+=1
        return verts, norms
    ## fix all transforms & modifiers:
    if showVox:
        obj.hide = obj.hide_render = True
    if not obj.type in ('MESH', 'CURVE', 'SURFACE'):
        # Skip any non-mesh(able) objects
        return [], []

    me = obj.to_mesh(scn, True, 'RENDER')
    me.transform(obj.matrix_world)
    dup = bpy.data.objects.new('dup', me)
    scn.objects.link(dup)
    dup.dupli_type = 'VERTS'
    scn.objects.active = dup

    ## Cut long edges in successive passes 
    bpy.ops.object.mode_set()#
    ver = me.vertices
    nPasses = 50
    for ii in range(nPasses):
        fin = True
        dd = []
        for i in dup.data.edges:
            # Vector subtraction btw vertices to get vector from vertex 1 -> 2
            d = ver[i.vertices[0]].co - ver[i.vertices[1]].co
            dd.append(d.length)
            if d.length > size:
                ver[i.vertices[0]].select = True
                ver[i.vertices[1]].select = True
                fin = False
        print('max length of a side is: %.2f'%max(dd))
        print('%.2f pct of edges are longer than "size"'%(sum([q>size for q in dd])/float(len(dd))*100))
        print('%.2f pct of vertices are selected for deletion'%(sum([q.select for q in dup.data.vertices])/float(len(dup.data.vertices))))
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.subdivide(number_cuts=1, smoothness=smooth)
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.editmode_toggle()
        if fin: 
            if verbosity_level>3:
                print('took %d edge cut passes'%ii)
            break
    if not fin:
        print('took all %d edge cut passes!'%nPasses)
    ## Place all vertices on a grid 
    for i in ver:
        i.co[0] -= divmod(i.co[0]+.5*size, size)[1] # X coord
        i.co[1] -= divmod(i.co[1]+.5*size, size)[1] # Y
        i.co[2] -= divmod(i.co[2]+.5*size, size)[1] # Z

    ## Clean the vertex of all duplicated vertices, edges, & faces (limpiar la malla de verts duplicados caras y edges)
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    bpy.ops.mesh.select_all(action='SELECT')
    try:
        #@$!ing stupid: kwarg name changes from "limit" to "mergedist" in 2.63. STOOPID
        bpy.ops.mesh.remove_doubles(limit=0.0001) 
    except:
        bpy.ops.mesh.remove_doubles(mergedist=0.0001) 
    bpy.ops.mesh.normals_make_consistent()
    bpy.ops.mesh.delete(type='EDGE_FACE')
    bpy.ops.object.mode_set()
    verts = [list(x.co) for x in dup.data.vertices]
    norms = [list(x.normal) for x in dup.data.vertices]
    if fNm:
        with open(fNm, 'w') as fid:
            for v in verts:
                fid.write('%.5f, %.5f, %.5f\n'%(v[0], v[1], v[2]))
        # Skip normal write-out - these are fucked anyway!
        #with open(fNm+'_Normals.txt', 'w') as fid:
        #   for n in norms:
        #       fid.write('%.5f, %.5f, %.5f\n'%(n[0], n[1], n[2]))
    if not showVox:
        scn.objects.unlink(dup)
        RemoveMeshFromMemory(me.name)
        #SetNoMemoryMode(Revert=True)
    if verbosity_level>4:
        t1=time.time()
        print('getVoxelizedVertList took %d mins, %.2f secs'%divmod((t1-t0), 60))
    return verts, norms

def add_img_material(name, imfile, imtype):
    """Add a texture containing an image to Blender.

    Is this optimal? May require different materials/textures w/ different uv mappings 
    to fully paint all the shit in a scene. Better to just load an image?

    Parameters
    ----------
    name : string
        Name of texture to be added. Blender image object will be called <name>, 
        Blender texture will be called <name>_tex, and Blender material will be 
        <name>_mat
    imfile : string
        full path to movie or image to add
    imtype : string
        one of : 'sequence', 'file', 'generated', 'movie'
    """
    # Load image
    from bpy_extras.image_utils import load_image
    img = load_image(imfile)
    img.source = imtype.upper()
    # Link image to new texture 
    tex = bpy.data.textures.new(name=name+'_image', type='IMAGE')
    tex.image = img
    if imtype.upper()=='MOVIE':
        tex.image_user.use_cyclic = True
        bpy.ops.image.match_movie_length()
    # Link texture to new material
    mat = bpy.data.materials.new(name=name)
    mat.texture_slots.create(0)
    mat.texture_slots[0].texture = tex
    return mat

def set_material(proxy_ob, mat):
    """Creates proxy objects for all sub-objects in a group & assigns a specific material to each"""
    for g in proxy_ob.dupli_group.objects:
        grab_only(proxy_ob)
        if not g.type=='MESH':
            continue
        bpy.ops.object.proxy_make(object=g.name)
        o = bpy.context.object
        for ms in o.material_slots:
            ms.material = mat
        # Get rid of proxy now that material is set
        bpy.context.scene.objects.unlink(o)

def set_scene(scene_name=None):
    """Sets all blender screens in an open Blender session to scene_name
    """
    if scene_name is None:
        scn = bpy.context.scene
    else:
        if not scene_name in bpy.data.scenes:
            scn = bpy.data.scenes.new(scene_name)
        else:
            scn = bpy.data.scenes[scene_name]
        # Set all screens to this scene
        for scr in bpy.data.screens:
            scr.scene = scn
    return scn

def apply_action(target_object, action_file, action_name):
    """"""
    pass
    # (character must already have been imported)
    # import action & armature from action_file
    # get list of matching bones
    # for all matching bones, apply (matrix? position?) of first frame

def set_up_group(ObList=None, scn=None):
    """    
    Set a group of objects to canonical position (centered, facing forward, max dimension = 10)
    Position is defined relative to the BOTTOM, CENTER of the object (defined by the  bounding 
    box, irrespective of the object's origin) Origins are set to (0, 0, 0) as well.

    WARNING: NOT SUPER RELIABLE. There is a great deal of variability in the way in which 3D model 
    objects are stored in the myriad free 3D sites online; thus a GREAT MANY conditional statements
    would be necesary to have a reliably working function. If you want to write such a function, 
    be my guest. This works... OK. In many cases. Use with caution. ML
    """
    
    verbosity_level > 3
    if not scn:
        scn = bpy.context.scene # (NOTE: think about making this an input!)
    if not ObList:
        for o in scn.objects:
            # Clear out cameras and (ungrouped) 
            if o.type in ['CAMERA', 'LAMP'] and not o.users_group:
                scn.objects.unlink(o)
                scn.update()
        ObList = list(scn.objects)
    ToSet_Size = 10.0
    ToSet_Loc = (0.0, 0.0, 0.0)
    ToSet_Rot = 0.0
    # FIRST: Clear parent relationships
    p = [o for o in ObList if not o.parent and not 'ChildOf' in o.constraints.keys()]
    if len(p)>1:
        raise Exception('More than one parent in group! Now I commit Seppuku! Hi-YA!')
    else:
        p = p[0]
    np = [o for o in ObList if o.parent or 'ChildOf' in o.constraints.keys()]
    if p:
        for o in np:
            GrabOnly(o)
            bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
            if 'ChildOf' in o.constraints.keys():
                o.constraints.remove(o.constraints['ChildOf'])
    
    # SECOND: Reposition all object origins 
    (MinXYZ, MaxXYZ) = get_group_bounding_box(ObList)
    BotMid = [(MaxXYZ[0]+MinXYZ[0])/2, (MaxXYZ[1]+MinXYZ[1])/2, MinXYZ[2]]
    set_cursor(BotMid)
    
    SzXYZ = []
    for Dim in range(3):
        SzXYZ.append(MaxXYZ[Dim]-MinXYZ[Dim])
    
    if not ToSet_Size==max(SzXYZ):
        ScaleF = ToSet_Size/max(SzXYZ)
    if verbosity_level > 3: 
        print('resizing to %.2f; scale factor %.2f x orig. size %.2f'%(ToSet_Size, ScaleF, max(SzXYZ)))
    
    for o in ObList:
        GrabOnly(o)
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        o.scale = o.scale * ScaleF
        o.location = ToSet_Loc

    scn.update()
    # Re-parent everything
    for o in np:
        GrabOnly(p)
        o.select = True
        bpy.ops.object.parent_set()
    # Create group (if necessary) and name group
    if not ObList[0].users_group:
        for o in ObList:
            o.select=True
        bpy.ops.group.create(name=scn.name)

def get_group_bounding_box(ob_list=None):
    """Returns the maximum and minimum X, Y, and Z coordinates of a set of objects

    Parameters
    ----------
    ob_list : list or tuple 
        list of Blender objects for which to get bounding box

    Returns
    -------
    minxyz, maxxyz : lists
        min/max x, y, z coordinates for all objects. Think about re-structuring this to be a
        more standard format for a bounding box. 
    """
    bb_types = ['MESH', 'LATTICE', 'ARMATURE'] 
    if ob_list is None:
        ob_list = [o for o in bpy.context.scene.objects if o.select]
    BBx = list()
    BBy = list()
    BBz = list()
    for ob in ob_list: 
        bvp.utils.blender.grab_only(ob)
        if ob.type in bb_types:
            bpy.ops.object.transform_apply(rotation=True)
        for ii in range(8):
            BBx.append(ob.bound_box[ii][0] * ob.scale[0] + ob.location[0]) 
            BBy.append(ob.bound_box[ii][1] * ob.scale[1] + ob.location[1])
            BBz.append(ob.bound_box[ii][2] * ob.scale[2] + ob.location[2])
    MinXYZ = [min(BBx), min(BBy), min(BBz)]
    MaxXYZ = [max(BBx), max(BBy), max(BBz)]
    # Done
    return MinXYZ, MaxXYZ

def get_collada_action(collada_file, act_name=None, scale=1.0):
    """Imports an armature and its associated action from a collada (.dae) file.

    Imports armature and rescales it to be standard Blender size (when the armature 
    is in a basic T pose)


    Inputs
    ------
    collada_file : string filename
        file name from which to import action(s)(?). 
    act_name : string
        name for action to create. defaults to title of collada file, without .dae extension
    scale : float
        amount by which to scale 
    """
    if act_name is None:
        act_name = os.path.split(collada_file)[1].replace('.dae', '')
    # Work in a new scene
    scn = set_scene(act_name)
    # Get list of extant actions, objects
    ext_act = [a.name for a in bpy.data.actions]
    ext_obj = [o.name for o in bpy.data.objects]
    # Import new armature
    bpy.ops.wm.collada_import(filepath=collada_file)
    # Find new objects (armature & parented meshes)
    arm_ob = [o for o in bpy.data.objects if isinstance(o.data, bpy.types.Armature) and not o.name in ext_obj]
    mesh_ob = [o for o in bpy.data.objects if isinstance(o.data, bpy.types.Mesh) and not o.name in ext_obj]
    print(mesh_ob)
    if len(arm_ob)>1:
        # Perhaps more subtlety will be required
        from pprint import pprint
        print('=========================================')
        print('Multiple armatures found for %s:'%act_name)
        print('New armatures:')
        pprint(arm_ob)
        print('=========================================')
        #raise Exception("WTF! TOO MANY NEW ARMATURES!")
        # Skip error, just go with it:
        #arm_ob = arm_ob[0]
        # Rename armature object, armature, bones
    # else:
    #   arm_ob = arm_ob[0]
    #   # Used to be outside if/else    
    #   # Rename armature object, armature, bones
    #   arm_ob.name = act_name+'_armature_ob'
    #   arm_ob.data.name = act_name+'_armature'
    #   for b in arm_ob.data.bones:
    #       xx = re.search('_', b.name).start()
    #       b.name = act_name+b.name[xx:]
    for iao, ao in enumerate(arm_ob):
        ao.name = act_name+'_%d_armature_ob'%iao
        ao.data.name = act_name+'_%d_armature'%iao
        if not ao.data.bones is None:
            for b in ao.data.bones:
                #print(b.name)
                grp = re.search('_', b.name)
                if not grp is None:
                    xx = grp.start()+1
                else:
                    xx = 0
                b.name = b.name[xx:]
                #print(b.name)
    # Find new action
    arm_act = [a for a in bpy.data.actions if not a.name in ext_act]
    if len(arm_act)>1:
        # Perhaps more subtlety will be required
        #raise Exception("WTF! TOO MANY NEW ACTIONS!")
        print('Keeping first action only!')
    arm_act = arm_act[0]
    arm_ob = arm_ob[0]
    # Rename new action
    arm_act.name = act_name
    # Adjust size to standard 10 units (standing straight up in rest pose)
    arm_ob.data.pose_position = "REST"
    #try:
    # Create parent relationship btw. armature and object

    set_up_group()
    #except:
    #   print('Automatic bounding box scaling failed for action;%s\nMultiplying by scale %.2f'%(act_name, scale))
    #   arm_ob.scale*=scale
    arm_ob.data.pose_position = "POSE"

###########################################################
### ---       Adding BVP elements to a scene        --- ###
###########################################################

def AddCameraWithTarget(scn=None, CamName='CamXXX', CamPos=[25, -25, 5], FixName='CamTarXXX', FixPos=[0., 0., 0.], Lens=50., Clip=(.1, 300.)):
    """
    Usage: AddCameraWithTarget(scn, CamName='CamXXX', CamPos=[25, -25, 5], FixName='CamTarXXX', FixPos=[0., 0., 0.])
    Adds a camera to a scene with an empty named <FixName> 
    This is a bit quick & dirty - make sure it grabs the right "camera" data, that it's not duplicating names; also that the scene is handled well
    ML 2011.06.16
    """
    if not scn:
        scn = bpy.context.scene
    # Add camera    
    bpy.ops.object.camera_add(location=CamPos)
    Cam = [o for o in scn.objects if o.type=='CAMERA'][0] # better be only 1
    Cam.name = CamName
    # Add fixation target
    bpy.ops.object.add(type='EMPTY', location=FixPos)
    # Is this legit? Is there another way to do this??
    Fix = [o for o in scn.objects if o.type=='EMPTY'][0]
    Fix.empty_draw_type = 'SPHERE'
    Fix.empty_draw_size = .33
    Fix.name = FixName
    # Add camera constraint
    grab_only(Cam)
    bpy.ops.object.constraint_add(type='TRACK_TO')  
    bpy.ops.object.constraint_add(type='TRACK_TO')
    Cam.data.lens = Lens
    Cam.data.clip_start = Clip[0]
    Cam.data.clip_end = Clip[1]
    Cam.constraints[0].target = Fix
    Cam.constraints[0].track_axis = 'TRACK_NEGATIVE_Z'
    Cam.constraints[0].up_axis = 'UP_Z'
    Cam.constraints[1].target = Fix
    Cam.constraints[1].track_axis = 'TRACK_NEGATIVE_Z'
    Cam.constraints[1].up_axis = 'UP_Y' 

def add_lamp(fname, scname, fpath=os.path.join(config.get('path', 'db_dir'), 'sky')): 
    """Add all the lamps and world settings from a given file to the current .blend file.

    Parameters
    ----------
    fname : string
        .blend file name (including .blend extension)
    scname : string
        name of scene within file to import lamps/world from
    fpath : string
        path to directory with all .blend files in it

    NOTE:
    Unused. Unclear if necessary. 
    """ 
    # PERMISSIBLE TYPES OF OBJECTS TO ADD:
    AllowedTypes = ['LAMP'] # No curves for now...'CURVE', 
    # ESTABLISH SCENE TO WHICH STUFF MUST BE ADDED, STATE OF .blend FILE
    scn = bpy.context.scene # (NOTE: think about making this an input!)
    # This is dumb too... ???
    ScnNum = len(bpy.data.scenes)
    ScnListOld = [s.name for s in bpy.data.scenes]
    # APPEND SCENE CONTAINING LAMPS TO BE ADDED
    bpy.ops.wm.link_append(
        directory=fpath+fname+"\\Scene\\", # i.e., directory WITHIN .blend file (Scenes / Objects)
        filepath="//"+fname+"\\Scene\\"+scname, # local filepath within .blend file to the scene to be imported
        filename=scname, # "filename" being the name of the data block, i.e. the name of the scene.
        link=False, 
        relative_path=False, 
        autoselect=True)
    ScnListNew = [s.name for s in bpy.data.scenes]
    nScn = [s for s in ScnListNew if not s in ScnListOld]
    nScn = bpy.data.scenes[nScn[0]]

    LampOb = [L for L in nScn.objects if (L.type in AllowedTypes)]

    LampOut = list()
    # Make parent / master object the first object in the list: 
    LampCt = 1
    for L in LampOb:
        scn.objects.link(L)
        LampOut.append(L)
        LampCt += 1
    scn.world = nScn.world
    scn.update()
    bpy.data.scenes.remove(nScn)
    bpy.ops.object.select_all(action = 'DESELECT')
    for L in LampOut:
        L.select = True
    return LampOut

def add_action(action_name, fname, fpath=os.path.join(config.get('path','db_dir'), 'action')):
    """Import an action into the current .blend file

    """
    if action_name in bpy.data.actions:
        # Group already exists in file, for whatever reason
        print('Action already exists!')
    else:
        bpy.ops.wm.link_append(
            directory=os.path.join(fpath, fname)+"\\Action\\", # i.e., directory WITHIN .blend file (Scenes / Objects / Groups)
            filepath="//"+fname+"\\Action\\"+action_name, # local filepath within .blend file to the scene to be imported
            filename=action_name, # "filename" is not the name of the file but the name of the data block, i.e. the name of the group. This stupid naming convention is due to Blender's API.
            link=True, 
            relative_path=False, 
            autoselect=True)
    a = bpy.data.actions[action_name]
    return a

def add_group(name, fname, fpath=os.path.join(config.get('path','db_dir'), 'object'), proxy=True):
    """Add a proxy object for a Blender group to the current scene. 

    Add a group of Blender objects (all the parts of a single object, most likely) from another 
    file to the current scene. 

    Parameters
    ----------
    fname : string
        .blend file name (including .blend extension)
    name : string
        Name of group to import 
    fpath : string
        Path of directory in which .blend file resides
    
    Notes
    -----
    Counts objects currently in scene and increments count.
    """ 

    if name in bpy.data.groups:
        
        # TO DO: add:
        # if proxy:
        # else:

        # Group already exists in file, for whatever reason
        print('Found group! adding new object...')
        # Add empty
        bpy.ops.object.add() 
        # Fill empty with dupli-group object of desired group
        G = bpy.context.object
        G.dupli_type = "GROUP"
        G.dupli_group = bpy.data.groups[name]
        G.name = name
    else:
        print('Did not find group! adding...')
        bpy.ops.wm.append(
            directory=os.path.join(fpath, fname)+"\\Group\\", # i.e., directory WITHIN .blend file (Scenes / Objects / Groups)
            filepath="//"+fname+"\\Group\\"+name, # local filepath within .blend file to the scene to be imported
            filename=name, # "filename" is not the name of the file but the name of the data block, i.e. the name of the group. This stupid naming convention is due to Blender's API.
            link=proxy, 
            #relative_path=False, 
            autoselect=True, 
            instance_groups=proxy)
        G = bpy.context.object
    return G

# Belongs in Object or Shape
def meshify(ob):
    """
    Create a single (water-tight?) mesh from a multi-mesh group
    """
    raise NotImplementedError('Not yet!')
    # Select object
    grab_only(ob)
    # Prep list of new objects to be joined later
    new_obs = []
    for oo in list(ob.dupli_group.objects):
        try:
            grab_only(o)
            bpy.ops.object.proxy_make(object=oo.name)
            N = bpy.context.object
            # Apply all modifiers in stack? 

            # Re-mesh once to assure quality no shady bits in mesh
            bpy.ops.object.modifier_add(type='REMESH')
            # Must be precise or it looks awful
            N.modifiers['Remesh'].octree_depth = 8 #??
            N.modifiers['Remesh'].scale = .8 # ??
            N.modifiers['Remesh'].mode = "SHARP"
            bpy.ops.object.modifier_apply(as_type='DATA', modifier='REMESH')
            # T
            new_obs.append(N.name)
        except:
            print("Failed for %s"%oo.name)

def make_cube(name, mn, mx):
    xn, yn, zn = mn
    xx, yx, zx = mx
    
    #Define vertices, faces, edges
    verts = [(xn, yn, zn), (xn, yx, zn), (xx, yx, zn), (xx, yn, zn), (xn, yn, zx), (xn, yx, zx), (xx, yx, zx), (xx, yn, zx)]
    faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
     
    #Define mesh and object
    mesh = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, mesh)
     
    #Set location and scene of object
    #ob.location = bpy.context.scene.cursor_location
    bpy.context.scene.objects.link(ob)
     
    #Create mesh
    mesh.from_pydata(verts, [], faces)
    mesh.update(calc_edges=True)

