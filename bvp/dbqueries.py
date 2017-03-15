"""Database queries for blender vision project"""

"""
Custom queries for STRF db
"""
from docdb_lite.dbqueries import generic as _g

### --- Simple item queries --- ###
class name(_g.ItemQuery):
    """Item query for name of db object (mask, experiment, etc)"""
    def __init__(self, *args, **kwargs):
        super(name, self).__init__(*args, **kwargs)
        self.priority = 0.5

### --- List Member queries --- ###
class semantic_category(_g.ListMemberQuery):
    """Item query for subject initials / other identifier."""
    def __init__(self, *args, **kwargs):
        super(semantic_category, self).__init__(*args, **kwargs)
        self.priority = 2

class wordnet_label(_g.ListMemberQuery):
    """Item query for subject initials / other identifier."""
    def __init__(self, *args, **kwargs):
        super(wordnet_label, self).__init__(*args, **kwargs)
        self.priority = 2

