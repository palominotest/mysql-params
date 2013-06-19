import re
from datetime import datetime, timedelta

from hurry.filesize import size

class ParamComparer(object):
    
    def __init__(self, key=None, val=None, dbi_val=None):
        self.key = key
        self.val = val
        self.dbi_val = dbi_val
        
    def params_equal(self):
        equal = False
        key = self.key
        val = self.normalize_val(self.val)
        dbi_val = self.normalize_val(self.dbi_val)
        if val == dbi_val:
            equal = True
        return equal
        
    def get_comparison_type(self):
        comparison_type = 'string'
        boolean_vals = ('OFF', 'ON', 'TRUE', 'FALSE')
        val = str(self.val)
        dbi_val = str(self.dbi_val)
        is_numeric = False
        try:
            float(val)
            float(dbi_val)
            is_numeric = True
        except Exception:
            pass
        filesize_regex1 = re.match('(\d+)([BKMGTP])', val)
        filesize_regex2 = re.match('(\d+)([BKMGTP])', dbi_val)
        if dbi_val.upper() in boolean_vals:
            comparison_type = 'boolean'
        elif is_numeric:
            comparison_type = 'numeric'
        elif filesize_regex1 is not None or filesize_regex2 is not None:
            comparison_type = 'filesize_numeric'
        return comparison_type        
        
    def normalize_val(self, val):
        comparison_type = self.get_comparison_type()
        return_val = str(val)
        if comparison_type == 'boolean':
            if val == '0':
                return_val = 'OFF'
            elif val == '1':
                return_val = 'ON'
            elif val in ('OFF', 'ON', 'TRUE', 'FALSE'):
                return_val = str(val)
        elif comparison_type == 'numeric':
            return_val = float(val)
        elif comparison_type == 'filesize_numeric':
            filesize_regex = re.match('(\d+)([BKMGTP])', val)
            if filesize_regex is None:
                return_val = str(size(float(val)))
            else:
                return_val = str(val)
        else:
            if val.endswith('/') or val.endswith('\\'):
                return_val = val[:-1]
        return return_val

def get_all_dbinstances(conn):
    dbis = []
    marker = True
    while True:
        request_dbis = conn.get_all_dbinstances(marker=marker)
        dbis.extend(request_dbis)
        if hasattr(request_dbis, 'Marker'):
            marker = getattr(request_dbis, 'Marker')
        else:
            break
    return dbis

def get_all_dbparameter_groups(conn):
    pgs = []
    marker = ''
    while True:
        request_pgs = conn.get_all_dbparameter_groups(marker=marker)
        pgs.extend(request_pgs)
        if hasattr(request_pgs, 'Marker'):
            marker = getattr(request_pgs, 'Marker')
        else:
            break
    return pgs
    
def get_all_dbparameters(pg):
    conn = pg.connection
    marker = ''
    while True:
        pg1 = conn.get_all_dbparameters(pg.name, marker=marker)
        pg.update(pg1)
        if hasattr(pg1, 'Marker'):
            marker = getattr(pg1, 'Marker')
        else:
            break
    return pg
    
def get_sorted_dict(objs):
    objs_dict = {}
    new = []
    changed = []
    deleted = []
    for obj in objs:
        status = obj.status
        if status == 'new':
            new.append(obj)
        elif status == 'deleted':
            deleted.append(obj)
        elif status == 'changed':
            changed.append(obj)
    objs_dict.update({
        'new':new,
        'deleted':deleted,
        'changed':changed,
    })
    return objs_dict   
    
def get_needs_restart(dbis):
    needs_restart = []
    for dbi in dbis:
        diff = dbi.get_difference_with_pg_or_cf()
        if len(diff) != 0:
            needs_restart.append((dbi, diff))
    return needs_restart
    
def str_to_datetime(string):
    regex = re.search('(\d+(?:\.?\d+)?)([hdwmHDWM])?', string)
    if regex is not None:
        num, unit = regex.groups()
        unit = unit.lower()
        num = float(num)
        if unit == 'h':
            dtime = datetime.now() - timedelta(hours=num)
        elif unit == 'd':
            dtime = datetime.now() - timedelta(days=num)
        elif unit == 'w':
            dtime = datetime.now() - timedelta(weeks=num)
        elif unit == 'm':
            dtime = datetime.now() - timedelta(minutes=num)
        else:
            dtime = datetime.now() - timedelta(seconds=num)
        return dtime
    else:
        return None
