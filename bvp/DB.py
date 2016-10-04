"""

each class should have: from_docdict(doc), from_blender(blender_object), 
docdict [property], to_blender [sets blend props?] 


- Actions - 
    Action - must be linked to specific class of armatures (which will be a property of bvpObjects)
    - Armature_class
    - wordnet_label
    - semantic_category
    - 

-> Add armature field to objects
-> All animations must be based on armatures, and we should be able to flexibly define classes of armatures.
-> Positioning (for START of action) will still be handled by pos3D, rot3D, size3D. 
-> Actions will need bounding boxes, which will have to be multiplied by the bounding boxes for objects.

TODO: 
- 

"""

from __future__ import absolute_import

# Imports
import numpy as np
import subprocess
import sys
import os
import time
import json
from .options import config
from . import dbqueries

from .Classes.Action import Action
from .Classes.Background import Background
from .Classes.Camera import Camera
#from .Classes.Constraint import  ObConstraint, CamConstraint
from .Classes.Material import Material
from .Classes.Object import Object
#from .Classes.RenderOptions import RenderOptions
#from .Classes.Scene import Scene
#from .Classes.SceneList import SceneList
from .Classes.Shadow import Shadow
#from .Classes.Shape import Shape # Move to Object...?
from .Classes.Sky import Sky

try:
    import docdb_lite as docdb
    docdb.is_verbose = False
    docdb.orm.class_type.update(
        Action=Action,
        Background=Background,
        Camera=Camera,
        Material=Material,
        Object=Object,
        #RenderOptions=RenderOptions,
        #Scene=Scene,
        #SceneList=SceneList,
        Shadow=Shadow,
        #Shape=Shape, 
        Sky=Sky,
        )
    # add db queries for bvp stuff
    setattr(docdb.dbqueries, 'bvp', dbqueries)
except ImportError:
    print("No docdb_lite present! WTF!") # Make me a better error message

# Defaults
dbhost = config.get('db','dbhost')
dbname = config.get('db','dbname')
is_verbose = config.get('db','is_verbose').lower() in ('t','true','yes','1')
return_objects = config.get('db','return_objects').lower() in ('t','true','yes','1')

verbosity_level = 3

# Make sure that all files in these directories contain objects / backgrounds / skies that you want to use. Otherwise, modify the lists of objects / bgs / skies below.
class DBInterface(docdb.couchclient.CouchDocDBClient):
    """Class to interface with bvp elements stored in couch db
    
    Files in the library directory must be stored according to bvp directory structure: 
    
    BaseDirectory/ object/*.blend
                   background/*.blend
                   sky/*.blend
                   shadow/*.blend
    Parameters
    ----------
    dbhost : string
        Name for host server. Read from config file. Config default is intialized to be 'localhost'
    dbname : string
        Database name. Read from config file. Config default is intialized to be 'bvp_1.0'
    port : scalar
        Port number for database. 
    Notes
    -----
    """
    def __init__(self, dbhost=dbhost, dbname=dbname, queries=('basic', 'bvp'), 
        is_verbose=is_verbose, return_objects=return_objects):
        super(DBInterface, self).__init__(dbhost, dbname, queries=queries, 
            is_verbose=is_verbose, return_objects=return_objects)
        # Set database root dir
        try:
            self.db_dir = os.path.expanduser(self.db['config']['db_dir'])
        except:
            # TODO: Make this an error
            self.db_dir = None

    def _cleanup(self):
        """Remove all .blend1 and .blend2 backup files from database"""
        for root, _, files in os.walk(self.dbpath, topdown=True):
            ff = [f for f in files if 'blend1' in f or 'blend2' in f]
            for f in ff:
                os.unlink(os.path.join(root, f))

    def export_json(self, fname, qdict=None):
        """Exports some or all documents in this database """
        if qdict is None:
            ddict = [dict(doc) for doc in self.get_all_documents() if not '_design' in doc.id]
        elif isinstance(qdict, (list, tuple)):
            ddict = []
            for q in qdict:
                ddict += self.query_documents(**q) # no fancy queries...
        elif isinstance(qdict, dict):
            ddict = self.query_documents(**qdict)
        else:
            raise Exception("Bad type for qdict argument!")
        json.dump(ddict, open(fname, mode='w'))
        
    def import_json(self, fname):
        """Import all library header files from a json document.

        This function is for updating an extant database; see classmethod 

        """
        raise NotImplementedError("Not yet!") 

    def posed_object_list(self):
        """Get a list of posed objects as bvpObjects - duplicate each object for however many poses it has
        """
        raise NotImplementedError("Not yet!")
        ObList = []
        for o in self.objects:
            if o['nPoses']:
                for p in range(o['nPoses']):
                    ObList.append(Object(o['name'], self, size3D=None, pose=p))
            else:
                ObList.append(Object(o['name'], self, size3D=None, pose=None))
        return ObList

    def render_objects(self, query_dict, rtype=('Image', ), rot_list=(0, ), render_pose=True, render_group_size=1, is_overwrite=False, scale_obj=None):
        """
        Render (all) objects in bvpLibrary

        IS THIS NECESSARY? maybe. More flexible render class for simple renders: 
        define scene, diff camera angles, put objects into it? 
        or: rotate objects? (define armature?)
        or: render all actions? 

        ScaleObj = optional scale object to render along with this object (NOT FINISHED!)
        """
        raise NotImplementedError("Not yet!")
        RO = RenderOptions() # Should be an input, as should scene
        RO.BVPopts['BasePath'] = os.path.join(self.LibDir, 'Images', 'Objects', 'Scenes', '%s')
        RO.resolution_x = RO.resolution_y = 256 # smaller images
        
        if subCat:
            ToRender = self.getSCL(subCat, 'objects')
        else:
            ToRender = self.objects # all objects
        
        ObCt = 0
        ScnL = []
        for o in ToRender:
            # Get all object variations to add as separate scenes
            ObToAdd = []
            for rotZ in rotList:
                if o['nPoses'] and render_Pose:
                    for p in range(o['nPoses']):
                        O = Object(obID=o['name'], Lib=self, pos3D=(0, 0, 0), size3D=10, rot3D=(0, 0, rotZ), pose=p)
                        ObToAdd.append(O)
                        if scaleObj:
                            ScObSz = 10.*scaleObj.size3D/O.size3D
                            ScObToAdd.append
                else:
                    O = Object(obID=o['name'], Lib=self, pos3D=(0, 0, 0), size3D=10, rot3D=(0, 0, rotZ))
                    ObToAdd.append(O)
                    # Add scale object in here somehwhere... Scale for each object!
                    if scaleObj:
                        ScObSz = 10.*scaleObj.size3D/O.size3D
                        ScObToAdd.append
            # Camera, Lights (Sky), Background
            Cam = Camera()
            Sky = Sky()
            BG = Background()
            # Objects
            for Obj in ObToAdd:
                # Create Scene
                ObCt+=1
                if Obj.pose or Obj.pose==0:
                    pNum = Obj.pose+1
                else:
                    pNum = 1
                fpath = '%s_%s_p%d_r%d_fr##'%(Obj.semantic_category[0], Obj.name, pNum, Obj.rot3D[2])
                ScnL.append(Scene(Num=ObCt, Obj=(Obj, ), BG=BG, Sky=Sky, 
                                    Shadow=None, Cam=Cam, FrameRange=(1, 1), 
                                    fpath=fpath, FrameRate=15))
        # Convert list of scenes to SceneList   
        SL = SceneList(ScnList=ScnL, RenderOptions=RO)
        SL.RenderSlurm(RenderGroupSize=renderGroupSize, RenderType=Type)
        #SL.Render(RenderGroupSize=renderGroupSize, RenderType=Type)

    def RenderBGs(self, subCat=None, dummyObjects=(), nCamLoc=5, Is_Overwrite=False):
        """
        Render (all) backgrounds in bvpLibrary to folder <LibDir>/Images/Backgrounds/<category>_<name>.png

        subCat = None #lambda x: x['name']=='BG_201_mHouse_1fl_1' #None #'outdoor'      
        dummyObjects = ['*human', '*artifact', '*vehicle']
        """
        raise NotImplementedError("Not yet!")
        RO = RenderOptions()
        RO.BVPopts['BasePath'] = os.path.join(self.LibDir, 'Images', 'Backgrounds', '%s')
        RO.resolution_x = RO.resolution_y = 256 # smaller images
        if subCat:
            ToRender = self.getSCL(subCat, 'backgrounds')
        else:
            ToRender = self.backgrounds # all backgrounds
        # Frame count
        frames = (1, 1)
        # Get dummy objects to put in scenes:
        # Misc Setup
        BGCt = 0;
        ScnL = []
        for bg in ToRender:
            BGCt+=1
            # Create Scene
            BG = Background(bgID=bg['name'], Lib=self)
            ObL = []
            for o in dummyObjects:
                ObL.append(Object(obID=o, Lib=self, size3D=None))

            for p in range(nCamLoc):
                cNum = p+1
                fpath = '%s_%s_cp%02d_fr##'%(BG.semantic_category[0], BG.name, cNum)
                fChk = RO.BVPopts['BasePath']%fpath.replace('##', '01.'+RO.image_settings['file_format'].lower())
                print('Checking for file: %s'%(fChk))
                if os.path.exists(fChk) and not Is_Overwrite:
                    print('Found it!')
                    # Only append scenes to render that DO NOT have previews already rendered!
                    continue                
                Cam = Camera(location=BG.CamConstraint.sampleCamPos(frames), fixPos=BG.CamConstraint.sampleFixPos(frames), frames=frames)
                Sky = Sky('*'+BG.sky_semantic_category[0], Lib=self)
                if Sky.semantic_category:
                    if 'dome' in Sky.semantic_category:
                        if len(Sky.lightLoc)>1:
                            Shad=None
                        elif len(Sky.lightLoc)==1:
                            if 'sunset' in Sky.semantic_category:
                                Shad = Shadow('*west', self)
                            else:
                                fn = lambda x: 'clouds' in x['semantic_category'] and not 'west' in x['semantic_category']
                                Shad = Shadow(fn, self)
                        else:
                            Shad=None
                else:
                    Shad = None

                S = Scene(Num=BGCt, BG=BG, Sky=Sky, Obj=None, 
                                    Shadow=Shad, Cam=Cam, FrameRange=frames, 
                                    fpath=fpath, 
                                    FrameRate=15)
                try:
                    # Allow re-set of camera position with each attempt to populate scene
                    S.populate_scene(ObL, ResetCam=True)
                except:
                    print('Unable to populate scene %s!'%S.fpath)
                ScnL.append(S)
        # Convert list of scenes to SceneList   
        SL = SceneList(ScnList=ScnL, RenderOptions=RO)
        SL.RenderSlurm(RenderGroupSize=nCamLoc)

    def RenderSkies(self, subCat=None, Is_Overwrite=False):
        """
        Render (all) skies in bvpLibrary to folder <LibDir>/LibBackgrounds/<category>_<name>.png

        subCat = None # lambda x: 'dome' in x['semantic_category']
        """
        raise Exception('Not done yet!')
        RO = RenderOptions()
        RO.BVPopts['BasePath'] = os.path.join(self.LibDir, 'Images', 'Skies', '%s')
        RO.resolution_x = RO.resolution_y = 256 # smaller images
        if subCat:
            ToRender = self.getSCL(subCat, 'backgrounds')
        else:
            ToRender = self.backgrounds # all backgrounds
        # Frame count
        frames = (1, 1)
        # set standard lights (Sky)
        Sky = Sky()
        # Get dummy objects to put in scenes:
        ObL = []
        for o in dummyObjects:
            ObL.append(Object(obID=o, Lib=self, size3D=None))
        # Misc Setup
        BGCt = 0;
        ScnL = []
        for bg in ToRender:
            BGCt+=1
            # Create Scene
            BG = Background(bgID=bg['name'], Lib=self)
            for p in range(nCamLoc):
                cNum = p+1
                fpath = '%s_%s_cp%d_fr##'%(BG.semantic_category[0], BG.name, cNum)
                fChk = RO.BVPopts['BasePath']%fpath.replace('##', '01.'+RO.file_format.lower())
                print('Checking for file: %s'%(fChk))
                if os.path.exists(fChk) and not Is_Overwrite:
                    print('Found it!')
                    # Only append scenes to render that DO NOT have previews already rendered!
                    continue                
                Cam = Camera(location=BG.CamConstraint.sampleCamPos(frames), fixPos=BG.CamConstraint.sampleFixPos(frames), frames=frames)
                S = Scene(Num=BGCt, BG=BG, Sky=Sky, Obj=None, 
                                    Shadow=None, Cam=Cam, FrameRange=(1, 1), 
                                    fpath=fpath, 
                                    FrameRate=15)
                #try:
                    # Allow re-set of camera position with each attempt to populate scene
                S.populate_scene(ObL, ResetCam=True)
                #except:
                #   print('Unable to populate scene %s!'%S.fpath)
                ScnL.append(S)
        # Convert list of scenes to SceneList   
        SL = SceneList(ScnList=ScnL, RenderOptions=RO)
        SL.RenderSlurm(RenderGroupSize=nCamLoc)

    def CreateSolidVol(self, obj=None, vRes=96, buf=4):
        """
        Searches for extant .voxverts files in <LibDir>/Objects/VOL_Files/, and from them creates 
        3D, filled object mask matrices
        Saves this voxelized verison of an object as a .vol file in the <LibDir>/Objects/VOL_Files/ directory.

        Can not be called from inside Blender, since it relies on numpy

        Volume for voxelized object mask is vRes+4 (usually 96+4=100) to allow for a couple voxels' worth
        of "wiggle room" for imprecise scalings of objects (not all will be exactly 10 units - that part
        of object creation is manual and can be difficult to get exactly right)
        
        Voxelizations are used to create shape skeletons in subsequent processing. 

        Since the voxelized mesh surfaces of objects qualifies as meta-data about the objects, 
        this function might be expected to be a method of the RenderOptions class. However, this 
        isn't directly used by any models (yet); thus it has been saved in a separate place, as 
        the data about real-world size, number of mesh vertices, etc.

        """
        # Imports
        import re, os
        from scipy.ndimage.morphology import binary_fill_holes as imfill # Fills holes in multi-dim images
        
        if not obj:
            obj = self.objects
        for o in obj:
            # Check for existence of .verts file:
            ff = '%s_%s.%dx%dx%d.verts'%(o['semantic_category'][0].capitalize(), o['name'], vRes+buf, vRes+buf, vRes+buf*2)
            fNm = os.path.join(Settings['Paths']['LibDir'], 'Objects', 'VOL_Files', ff)
            if not os.path.exists(fNm):
                if verbosity_level>3:
                    print('Could not find .verts file for %s'%o['name'])
                    print('(Searched for %s'%fNm)
                continue
            # Get voxelized vert list
            with open(fNm, 'r') as fid:
                Pt = fid.readlines()
            vL = np.array([[float(x) for x in k.split(', ')] for k in Pt])
            # Get dimensions 
            dim = [len(np.unique(vL.T[i])) for i in range(3)]
            # Create blank matrix
            z = np.zeros((vRes+buf, vRes+buf, vRes+buf*2), dtype=bool)
            # Normalize matrix to indices for volume
            vLn = vL/(10./vRes) -.5 + buf/2. # .5 is a half-voxel shift down
            vLn.T[0:2]+= vRes/2. # Move X, Y to center
            vLn.T[2] += buf/2. # Move Z up (off floor) by "buf"/2 again
            # Check for closeness of values to rounded values
            S = np.sqrt(np.sum((np.round(vLn)-vLn)**2))/len(vLn.flatten())
            if S>.001:
                raise Exception('Your voxelized coordinates do not round to whole number indices!')
            # Index into volume
            idx = np.cast['int'](np.round(vLn))
            z[tuple(idx.T)] = True
            # Fill holes w/ python 
            # May need fancier strel (structure element - 2nd argumnet) for some objects 
            hh = imfill(z)
            # Trim?? for more efficient computation? 
            # ?
            # Save volume in binary format for pfSkel (or other) code:
            PF = o['fname']
            fDir = os.path.split(PF)[0]
            Cat = re.search('(?<=Category_)[^_^.]*', PF).group()
            Res = '%dx%dx%d'%(vRes+buf, vRes+buf, vRes+buf+buf)
            fName = os.path.join(fDir, 'VOL_Files', Cat+'_'+o['name']+'.'+Res+'.vol')
            # Write to binary file
            print('Saving %s'%fName)
            with open(fName, 'wb') as fid:
                hh.T.tofile(fid) # Transpose to put it in column-major form...
            # Done with this object!
    @classmethod
    def create_db_from_json(cls, fname, dbname, dbhost, db_dir):
        """Creates database from a json file

        If fname for json file is None, just creates an empty database"""
        import couchdb
        server = couchdb.Server(dbhost)
        print("Creating database {} on {}".format(dbname, dbhost))
        server.create(dbname)
        server[dbname].save(dict(_id='config', db_dir=db_dir))
        dbi = cls.__new__(cls)
        dbi.__init__(dbname=dbname, dbhost=dbhost)
        print("Setting up queries...")
        dbi.set_up_db()
        if fname is not None:
            docs = json.load(open(fname))
            print("Uploading documents...")
            dbi.put_documents(docs)
        print("Done!")


    @classmethod
    def start_db_server(cls, cmd=None): # set cmd from config file
        # Options for cmd from particular os
        raise NotImplementedError("Not yet!")
        subprocess.call(cmd) # Or whatever to run this in the backgroud.

    # @property
    # def n_object(self):
    #   return len(self.objects)
    # @property
    # def n_object_count_poses(self):
    #   nOb = 0
    #   for o in self.objects:
    #       if o['nPoses']:
    #           nOb+=o['nPoses']
    #       else:
    #           nOb+=1
    #   return nOb
    # @property
    # def n_background(self):
    #   return len(self.backgrounds)
    # @property
    # def n_sky(self):
    #   return len(self.skies)
    # @property
    # def n_shadow(self):
    #   return len(self.shadows)
