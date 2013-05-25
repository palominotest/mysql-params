import re

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
