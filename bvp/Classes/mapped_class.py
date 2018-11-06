# Parent class for ORM for all bvp classes

import os
import json
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

class MappedClass(object):
    
    # Temporary, meant to be overwritten by child classes
    dbi = None
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
    def datadict(self):
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
        _to_remove = ('docdict', 'datadict', 'fpath', 'dbi', 'data', 'shape', 'path')
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
        for f in fields:
            if hasattr(self, 'extras') and f in self.extras:
                raise Exception("There should be no data fields in 'extras' attribute!")
        dd = dict((k, self[k]) for k in fields if hasattr(self, k) and self[k] is not None)
        return dd

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
            tmp_dir = os.path.join(local_dir, cloud_dir)
            if not os.path.exists(tmp_dir):
                os.makedirs(tmp_dir)
            cci.download_to_file(os.path.join(cloud_dir, self.fname), os.path.join(tmp_dir, self.fname))
            # Shouldn't overwrite permanent property permanently...
            #self.path = tmp_dir
            self._tmppath = tmp_dir
        else:
            print("Doing nothing - file exists locally.")

    def save(self, is_overwrite=False):
        """Save the meta-data for this object to docdb database
        
        Does NOT do any checks on content (besides `_id` field). Needs update for saving fname, etc.
        """
        # Initial checks
        if (self.dbi is None) or (self.dbi=='None'):
            raise Exception('Must define database interface for this to work!')
        # Search for extant db object
        proceed,doc = self.db_check(is_overwrite=is_overwrite)
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

    ### --- Housekeeping --- ###
    def __getitem__(self, x):
        return getattr(self, x)

    def __setitem__(self, x, y):
        return setattr(self, x, y)
    
