import re
from datetime import datetime, timedelta

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
    
def compare_pg_to_dbi(pg, dbi):
    res = []
    for k in pg.parameters.keys():
        pg_val = pg.parameters.get(k)
        dbi_val = dbi.parameters.get(k)
        regex = re.search('{.*}', pg_val)
        # Don't process pg values with pseudo variables
        if regex is None and pg_val != dbi_val:
            res.append({
                'key': k,
                'pg_val': pg_val,
                'dbi_val': dbi_val,
            })
    return res

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
        diff = dbi.get_difference_with_pg()
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
