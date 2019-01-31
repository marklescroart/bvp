# Parent class for ORM for all bvp classes

import os
import json
import copy
from ..options import config

"""
The functions below seem complex, but I haven't been able to come up with 
a better way of switching between docdb _ids (to store in the database) and the
objects that populate the same fields when the objects are in use.
"""

def _obj2id_strlist(value):
    if isinstance(value, MappedClass):
        # _id should always be top-level
        out = value._id
    elif isinstance(value, (list, tuple)):
        out = [_obj2id_strlist(v) for v in value]
    elif isinstance(value, dict):
        out = _obj2id_doc(value)
    else:
        out = value
    return out

def _obj2id_doc(doc):
    """Map all database-mappable objects in a document (or dictionary) to database _ids

    searches through fields of a dict for strings, lists, or dictionaries in which 
    the values contain MappedClass objects
    """
    out = {}
    for k, v in doc.items():
        if k[0] == '_' and not k in ('_id', '_rev'):
            # Avoid any keys in dict with "_" prefix
            continue
        else:
            if isinstance(v, (MappedClass, list, tuple)):
                # Separate function for lists / tuples
                out[k] = _obj2id_strlist(v)
            elif isinstance(v, dict):
                # Recursive call for dicts
                out[k] = _obj2id_doc(v)
            else:
                # For strings & anything but lists, tuples, and dicts, leave it alone
                out[k] = v 
    return out

def _id2obj_strlist(value, dbi):
    vb = dbi.is_verbose
    dbi.is_verbose = False
    v = value
    if isinstance(value, (str, unicode)):
        if value in ('None', 'multi_component'): 
            v = value
        else:
            v = dbi.query(1, _id=value, return_objects=True) #[]
    elif isinstance(value, (list, tuple)):
        if len(value)>0:
            if isinstance(value[0], MappedClass): # already loaded
                pass
            elif isinstance(value[0], dict):
                v = [_id2obj_dict(vv, dbi) for vv in value]
            else:
                v = [dbi.query(1, _id=vv, return_objects=True) for vv in value]
    dbi.is_verbose = vb
    return v

def _id2obj_dict(dct, dbi):
    vb = dbi.is_verbose
    dbi.is_verbose = False
    for k, v in dct.items():
        if isinstance(v, (str, unicode, list, tuple)):
            dct[k] = _id2obj_strlist(v, dbi)
        elif isinstance(v, dict):
            for kk, vv in v.items():
                dct[k][kk] = _id2obj_strlist(vv, dbi)
    dbi.is_verbose = vb
    return dct

def _data_to_obj(datadict, dbinterface, is_verbose=False):
    import inspect
    import importlib
    old_is_verbose = copy.copy(dbinterface.is_verbose)
    dbinterface.is_verbose = is_verbose
    # Allow feeding this function whatever
    if isinstance(datadict, dict) and 'bvp_object' in datadict:
        object_class_name = datadict.pop('bvp_object')
        module, clsname = object_class_name.split('.')
        print('Importing %s, %s'%(module, clsname))
        module = importlib.import_module('bvp.Classes.%s'%module)
        obcls = getattr(module, clsname)
    else:
        return datadict
    # Get database info for database mapped objects
    if '_id' in datadict:
        ID = datadict.pop('_id')
        docdict = dbinterface.query_documents(1, _id=ID)
    else:
        docdict = {}
    # Find fields containing data dicts, convert to bvp objects
    for key in datadict.keys():
        value = datadict[key]
        if isinstance(value, dict):
            datadict[key] = _data_to_obj(value, dbinterface, is_verbose=is_verbose)
        elif (isinstance(value, (list, tuple)) and 
              isinstance(value[0], dict)):
            for i in range(len(value)):
                datadict[key][i] = _data_to_obj(value[i], dbinterface, is_verbose=is_verbose)
    # Instantiate object
    ob = obcls.__new__(obcls)
    argspec = inspect.signature(ob.__init__)
    if 'dbi' in argspec.parameters:
        # For database classes
        ob.__init__(dbi=dbinterface, **docdict, **datadict)
    else:
        # For pure data classes
        ob.__init__(**datadict)
    # Reset verbosity
    dbinterface.is_verbose = old_is_verbose
    return ob    

class MappedClass(object):
    
    # Temporary, meant to be overwritten by child classes
    #dbi = None
    # NOTE: `dbi` field is no longer included here, because 
    # some child classes are not db-mapped... This is a bit 
    # sloppy, and probably a good case for multiple inheritance
    # (one class for db-mapping, one class for other common
    # functions such as from_datadict(), etc. )
    @property
    def path(self):
        if self.dbi is None:
            return None
        else:
            db_dir = os.path.expanduser(config.get('path','db_dir'))
            #db_dir = os.path.expanduser(self.dbi.db['config']['db_dir'])
            return os.path.join(db_dir, self.type)

    @property
    def docdict(self):
        return self.get_docdict()
    
    @property
    def data(self):
        return self.get_datadict()
    
    @property
    def fpath(self):
        if hasattr(self, 'path') and hasattr(self, 'fname'):
            if (self.path is None) or (self.fname is None) or (self.path=='None') or (self.fname=='None'):
                return None
            else:
                return os.path.join(self.path, self.fname)
        else:
            return None

    # move me to just a property
    def get_docdict(self, rm_fields=()): #('is_verbose', 'fpath', 'datadict')): # remove is_verbose?
        """Get docdb (database header) dictionary representation of this object

        Used to insert this object into a docdb database or query a database for 
        the existence of this object.
        Maintain the option to remove some fields - this will be handy for partial copies
        of database objects 
        """
        # Fields that are never supposed to be saved in docdb
        _to_remove = ('docdict', 'data', 'fpath', 'dbi', 'data', 'shape', 'path')
        attrs = [k for k in dir(self) if (not k[:2]=='__') and (not k in _to_remove)]
        attrs = [k for k in attrs if not callable(getattr(self, k))]
        # Exclusion criteria # NOTE got rid of no_value field (fields w/ value None), added 'path' above to _to_remove
        to_remove = list(rm_fields) + self._data_fields + self._temp_fields
        # Get attribtues
        d = dict(((k, getattr(self, k)) for k in attrs if not k in to_remove))
        if 'is_verbose' in d:
            raise Exception('Is verbose?? WTF??')
        # add extras back in
        if 'extras' in d:
            ee = d.pop('extras')
            ee = dict((k, v) for k, v in ee.items() if not k in to_remove)
            d.update(ee)
        # Replace all classes in document with IDs
        d = _obj2id_doc(d)
        for k in d.keys():
            if d[k] is None:
                d[k] = 'None'
        if d['_rev'] == 'None':
            # Can't have `_rev` be 'None'
            _ = d.pop('_rev')
        # Convert to json and back to avoid unpredictable behavior due to conversion, e.g. tuple!=list
        d = json.loads(json.dumps(d))
        return d

    def get_datadict(self, fields=None):
        if fields is None:
            fields = self._data_fields
        if hasattr(self, '_id') and (self._id is not None) and not ('_id' in fields):
            fields += ['_id']
        output = dict()
        for field in fields:
            tmp = getattr(self, field)
            if tmp is None:
                # Skip all None attrs; those should have defaults.
                continue
            # Tmp is a list of BVP objects
            if isinstance(tmp, (list, tuple)):
                if len(tmp) > 0 and isinstance(tmp[0], MappedClass): #hasattr(tmp[0], 'data'):
                    output[field] = [t.data for t in tmp]
                    continue
            # Tmp is a BVP object
            if isinstance(tmp, MappedClass): # hasattr(tmp, 'data'):
                output[field] = tmp.data
            else:
                output[field] = tmp
        module = self.__class__.__module__.split('.')[-1]
        output['bvp_object'] = '.'.join([module, self.__class__.__name__])
        return output

    def db_load(self):
        """Load all attributes that are database-mapped objects objects from database.
        """
        # (All of these fields better be populated by string database IDs)
        for dbf in self._db_fields: 
            v = getattr(self, dbf)
            if isinstance(v, (str, unicode, list, tuple)):
                v = _id2obj_strlist(v, self.dbi)
            elif isinstance(v, dict):
                v = _id2obj_dict(v, self.dbi)
            elif v is None or v=='None':
                pass
            elif isinstance(v, MappedClass):
                pass
            else:
                raise ValueError("You have a value in one of fields that is expected to be a db class that is NOT a dbclass or an ID or anything sensible. Noodle brain.")
            if dbf=='mask':
                if isinstance(v, (list, tuple)):
                    # Combine multiple masks by and-ing together
                    v = reduce(lambda x, y:x*y, v)
            setattr(self, dbf, v)
        self._dbobjects_loaded = True

    def db_check(self, is_overwrite=False, skip_fields=('date_run', 'last_updated')):
        """Check database for identical instance.

        Returns
        -------
        proceed : bool
            Whether or not to proceed, depending on is_overwrite input
            (if 1 document exists and is_overwrite is true, proceed is true;
            if 1 document exists and is_overwrite is false, proceed is false;
            if > 1 document exists, proceed is always false; if 0 documents
            exist, proceed is always true)
        docs : list of db dict(s)

        """
        assert self.dbi is not None, 'dbi field must be set to check on items in database!'
        # Search for extant db object
        doc = self.docdict
        if doc['_id'] is None or doc['_id']=='None':
            _ = doc.pop('_id')
        if ('_rev' in doc) and (doc['_rev'] is None or doc['_rev']=='None'):
            _ = doc.pop('_rev')
        dr = {}
        for sf in skip_fields:
            if sf in doc:
                if sf=='date_run':
                    dr[sf] = doc.pop(sf)
                else:
                    _ = doc.pop(sf)
        chk = self.dbi.query_documents(**doc)
        if len(chk)==0:
            # 0 matches = OK
            # Add date_run back in
            doc.update(dr)
            return True, doc
        elif len(chk)==1:
            if is_overwrite:
                # Fill doc with fields from chk
                doc.update(chk[0])
                # Add date_run back in, since we're now over-writing
                doc.update(dr)
                return True, doc
            else:
                return False, chk[0]
        else:
            return False, chk

    def cloud_download(self, local_dir='/tmp/'):
        """Retrieve file stored on cloud to local file.

        This specifically download files stored in google drive (looks for 'gdrive' in 
        `self.path`); other cloud storage types still WIP.

        Parameters
        ----------
        local_dir : str
            path where file will be stored locally (temporarily, maybe?)
        """
        if self.path is None:
            # Nothing to see here (possibly raise exception?)
            return
        if not os.path.exists(self.path):
            import cottoncandy as cc
            if 'gdrive/' in self.path:
                gcci = cc.get_interface(backend='gdrive')
                cloud_dir = self.path.split('gdrive/')[-1]
            elif 's3/' in self.path:
                cloud_dir = self.path.split('s3/')[-1]
                bucket_name = cloud_dir.split('/')[0]
                cci = cc.get_interface(bucket_name=bucket_name)
            else:
                raise ValueError("File not found!")
            print("file ({}) not found locally - attempting to download from s3/google drive".format(self.fpath))
            tmp_dir = os.path.join(local_dir, cloud_dir)
            if not os.path.exists(tmp_dir):
                os.makedirs(tmp_dir)
            cci.download_to_file(os.path.join(cloud_dir, self.fname), os.path.join(tmp_dir, self.fname))
            # Shouldn't overwrite permanent property permanently...
            #self.path = tmp_dir
            self._tmppath = tmp_dir
        else:
            #print("Doing nothing - file exists locally.")
            pass

    def save(self, is_overwrite=False):
        """Save the meta-data for this object to docdb database
        
        Does NOT do any checks on content (besides `_id` field). Needs update for saving fname, etc.
        """
        # Initial checks
        if (self.dbi is None) or (self.dbi=='None'):
            raise ValueError('Must define database interface for this to work!')
        if self.fname == '':
            raise ValueError('BVP objects cannot be saved unless they exist in a named file')

        # Search for extant db object
        proceed, doc = self.db_check(is_overwrite=is_overwrite)
        if not proceed:
            if isinstance(doc,(list,tuple)) and len(doc)>1:
                raise Exception("Multiple objects found in database that match this object!")
            else:
                raise Exception("Found extant doc in database, and is_overwrite is set to False!")

        if (not '_id' in doc) or (doc['_id'] is None) or (doc['_id']=='None'):
            doc['_id'] = self.dbi.get_uuid()
        # Save header info to database
        self.dbi.put_document(doc)
    # For bvp, for now, this seems like a bad idea. 
    # def delete(self):
    #     assert self.dbi is not None, 'dbi field must be set to delete a file!'
    #     if hasattr(self, 'path') and hasattr(self, 'fname'):
    #         if isinstance(self.fpath, (list, tuple)):
    #             # Leave listed files intact
    #             pass
    #         else:
    #             print('Deleting %s'%self.fpath)
    #             if not os.path.exists(self.fpath): #fio.fexists(self.path, self.fname):
    #                 raise Exception("Path to real file not found")
    #             os.unlink(self.fpath) #fio.delete(self.path, self.fname)
    #     else:
    #         raise Exception("Path to real file not found!")
    #     doc = self.dbi.db[self._id]
    #     self.dbi.db.delete(doc)
    
    @classmethod
    def from_docdict(cls, docdict, dbinterface):
        """Creates a new instance of this class from the given `docdict`.
        """
        ob = cls.__new__(cls)
        ob.__init__(dbi=dbinterface, **docdict)
        return ob

    @classmethod
    def from_datadict(cls, datadict, dbinterface, is_verbose=False):
        """Create an instance of the class from a data dictionary"""
        return _data_to_obj(datadict, dbinterface, is_verbose=is_verbose)

    ### --- Housekeeping --- ###
    def __getitem__(self, x):
        return getattr(self, x)

    def __setitem__(self, x, y):
        return setattr(self, x, y)
    
