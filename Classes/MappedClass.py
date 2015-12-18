# General database class for bvp mapped classes

import os

"""
### --- NOTE --- ###
The functions below seem too complex, but I haven't been able to come up with 
a better way of switching between docdb _ids (to store in the database) and the
objects that populate the same fields when the objects are in use.
"""

def _obj2id_strlist(value):
    out = value
    if isinstance(value,MappedClass):
        # _id should always be top-level
        out = value._id
    elif isinstance(value,(list,tuple)):
        if len(value)>0:
            if isinstance(value[0],MappedClass):
                out = [vv._id for vv in value]
            elif isinstance(value[0],dict):
                # BETTER BE A DAMN MAPPED CLASS AT THIS DEPTH
                kk = value[0].keys()
                vv = value[0][kk[0]]
                if isinstance(vv,MappedClass):
                    out = [_obj2id_doc(vv) for vv in value] 
                #else:
                #    raise Exception('You are too deep in this object to have anything but mapped classes!')
                #elif isinstance(vvv,list):
                #    1/0
                #    out = [_obj2id_strlist(vvvv) for vvvv in vvvv]
                ## OH MAN PLEASE NO DEEPER... ##
    return out

def _obj2id_doc(doc):
    """Map all database-mappable objects in a document (or dictionary) to database _ids

    searches through fields of a dict for strings, lists, or dictionaries in which 
    the values contain MappedClass objects
    """
    out = {}
    for k,v in doc.items():
        if k[0] == '_' and not k in ('_id','_rev'):
            continue
        else:
            out[k] = v        
        if isinstance(v,(MappedClass,list,tuple)):
            out[k] = _obj2id_strlist(v)
        elif isinstance(v,dict):
            for kk,vv in v.items():
                out[k][kk] = _obj2id_strlist(vv)
    return out

def _id2obj_strlist(value,dbi):
    vb = dbi.is_verbose
    dbi.is_verbose = False
    v = value
    if isinstance(value,(str,unicode)):
        if value in ('None','multi_component'): 
            v = value
        else:
            v = dbi.query(1,_id=value,return_objects=True) #[]
    elif isinstance(value,(list,tuple)):
        if len(value)>0:
            if isinstance(value[0],MappedClass): # already loaded
                pass
            elif isinstance(value[0],dict):
                v = [_id2obj_dict(vv,dbi) for vv in value]
            else:
                v = [dbi.query(1,_id=vv,return_objects=True) for vv in value]
    dbi.is_verbose = vb
    return v

def _id2obj_dict(dct,dbi):
    vb = dbi.is_verbose
    dbi.is_verbose = False
    for k,v in dct.items():
        if isinstance(v,(str,unicode,list,tuple)):
            dct[k] = _id2obj_strlist(v,dbi)
        elif isinstance(v,dict):
            for kk,vv in v.items():
                dct[k][kk] = _id2obj_strlist(vv,dbi)
    dbi.is_verbose = vb
    return dct


class MappedClass(object):
    ### --- Database functions --- ###
    def db_init(self,raise_error=False):
        """Function to initialize database interface attribute."""
        is_verbose = True
        if self.dbi is None:
            self.dbi = dict(dbname=config.get('db','dbname'),
                file_store=config.get('db_dirs','default'),
                is_verbose=is_verbose,
                return_objects=return_objects)

        if isinstance(self.dbi,dict):
            raise Exception("db_init was a poorly conceived function; it relies on circular imports that I currently dont' see a way around. Please pass a database interface object to your class as an input!")
            try:
                self.dbi = docdb.getclient(**self.dbi)
            except:
                if raise_error:
                    raise Exception('Database interface could not be initialized!')
                if is_verbose:
                    warnings.warn('Database interface could not be initialized! attribute "dbi" is set to None!')

    @property
    def docdict(self):
        return self.get_docdict()

    @property
    def fpath(self):
        if (self.path) is None or (self.file_name is None):
            return None
        else:
            return os.path.join(self.path,self.file_name)

    def get_docdict(self,to_remove=('is_verbose','fpath',)):
        """Get docdb (database header) dictionary representation of this object

        Used to insert this object into a docdb database or query a database for 
        the existence of this object. 
        """
        attrs = [k for k in dir(self) if (not k[:2]=='__') and (not k=='docdict')]
        attrs = [k for k in attrs if not callable(getattr(self,k))]
        # Further exclusion criteria for attributes in docdict:
        no_value = [k for k in attrs if getattr(self,k) is None]
        # Exclusion criteria from inputs
        to_remove = to_remove + no_value 
        # Get attribtues
        d = dict(((k,getattr(self,k)) for k in attrs if not k in to_remove))
        # add extras back in
        if 'extras' in d:
            ee = d.pop('extras')
            ee = dict((k,v) for k,v in ee.items() if not k in to_remove)
            d.update(ee)
        # Replace all classes in document with IDs
        d = _obj2id_doc(d)
        return d

    def db_load(self):
        """Load all attributes that are database-mapped objects objects from database.
        """
        # (All of these fields better be populated by string database IDs)
        for tl in self._db_fields: # tl = to_load
            v = getattr(self,tl)
            if isinstance(v,(str,unicode,list,tuple)):
                v = _id2obj_strlist(v,self.dbi)
            elif isinstance(v,dict):
                v = _id2obj_dict(v,self.dbi)
            elif v is None:
                pass
            elif isinstance(v,MappedClass):
                pass
            else:
                raise ValueError("You have a value in one of fields that is expected to be a db class that is NOT a dbclass or an ID or anything sensible. Noodle brain.")
            if tl=='mask':
                if isinstance(v,(list,tuple)):
                    # Combine multiple masks by and-ing together
                    v = reduce(lambda x,y:x*y,v)
            setattr(self,tl,v)
        self._dbobjects_loaded = True

    def db_check(self,is_overwrite=False,skip_fields=('last_updated')):
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
        self.db_init(raise_error=True)
        # Search for extant db object
        doc = self.docdict
        for sf in skip_fields:
            if sf in doc:
                doc.pop(sf)
        chk = self.dbi.query_documents(**doc)
        # 0 matches = OK
        if len(chk)==0:
            return True,doc
        elif len(chk)==1:
            if is_overwrite:
                doc.update(chk[0])
                return True,doc
            else:
                return False,chk[0]
        else:
            return False,chk

    def delete(self):
        self.db_init(raise_error=True)
        if hasattr(self,'path') and hasattr(self,'fname'):
            if isinstance(self.fpath,(list,tuple)):
                # Leave listed files intact
                pass
            else:
                if not os.path.exists(self.fpath):
                    raise Exception("Path to real file not found!")
                print('Deleting %s'%self.fpath)
                os.unlink(self.fpath)
        else:
            # Temporary? 
            raise Exception("Path to real file not found!")
        doc = self.dbi.db[self._id]
        self.dbi.db.delete(doc)

    @classmethod
    def from_docdict(cls, docdict, dbinterface):
        """Creates a new instance of this class from the given `docdict`.
        """
        ob = cls.__new__(cls)
        ob.__init__(dbi=dbinterface,**docdict)
        return ob

    ### --- Housekeeping --- ###
    def __getitem__(self,x):
        return getattr(self,x)

    def __setitem__(self,x,y):
        return setattr(self,x,y)
    