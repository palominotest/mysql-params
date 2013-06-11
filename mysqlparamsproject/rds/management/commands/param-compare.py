import logging
import traceback
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand

from colorama import init, Fore
from texttable import Texttable

from rds.models import CollectorRun, ParameterGroup, DBInstance

logger = logging.getLogger('mysqlparams')

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            '--stat',
            dest='stat',
            default='parameter_group',
            help='Statistic to compare. See --list-stats for available statistics.(Default: parameter_group)',
        ),
        make_option(
            '--list-stats',
            action='store_true',
            dest='list_stats',
            default=False,
            help='List available statistics.'
        ),
        make_option(
            '-n',
            '--names',
            dest='names',
            default='',
            help='A comma-separated string containing parameter group/db instance names. If only one name is passed, previous version will be used for comparison.'
        ),
        make_option(
            '-e',
            '--engine',
            dest='engine',
            default='mysql5.5',
            help='MySQL Engine used for comparison for default values. One of: mysql5.1, mysql5.5'
        ),
    )
    
    def handle(self, *args, **options):
        if options.get('list_stats'):
            print 'Available Statistics:'
            collector_runs = CollectorRun.objects.all()
            for i,collector_run in enumerate(collector_runs):
               print '%d. %s' % (i+1, collector_run.collector)
            sys.exit(0)
        
        try:
            stat = options.get('stat')
            names = options.get('names')
            engine = options.get('engine')
            if len(names) == 0:
                raise Exception, '--names parameter is required.'
            if stat == 'parameter_group':
                self.do_compare_parameter_groups(names, engine)
            elif stat == 'db_instance':
                self.do_compare_db_instances(names)
        except Exception, e:
            tb = traceback.format_exc()
            logger.error(tb)
            
    def _print(self, lines, highlight_keys=[]):
        init(autoreset=True)
        print lines[0]                  # Print header
        lines = lines[1:]               # Remove header
        for line in lines:
            tokens = line.split()
            k = tokens[0]
            if k in highlight_keys:
                print Fore.RED + line
            else:
                print line
    
    def do_compare_parameter_groups(self, names, engine):
        names_list = names.split(',')
        if engine == 'mysql5.1':
            default = 'default.mysql5.1'
        else:
            default = 'default.mysql5.5'
        default_pg = ParameterGroup.objects.find_last(default)
        pgs = []
        for name in names_list:
            pg = ParameterGroup.objects.find_last(name.strip())
            if pg is not None and pg.status != 'deleted':
                pgs.append(pg)
        if len(names_list) == 1:
            pg = ParameterGroup.objects.find_last(names_list[0])
            prev = pg.previous_version
            if prev is not None and prev.status != 'deleted':
                pgs.append(prev)
                
        if len(pgs) <= 1:
            raise Exception, 'No comparisons can be made.'
        
        table = Texttable(max_width=200)
        table.set_deco(Texttable.HEADER)
        rows = []
        header = []
        header.append('Key')
        header.append('Default')
        for pg in pgs:
            header.append('ID: %d - %s' % (pg.id, pg.name))
        rows.append(header)
        
        highlight_keys = []
        for k in sorted(default_pg.parameters.keys()):
            row = []
            row.append(k)
            vals = [str(default_pg.parameters.get(k))]
            for pg in pgs:
                vals.append(str(pg.parameters.get(k)))
                
            if len(set(vals)) > 1:
                highlight_keys.append(k)
            
            row.append(str(default_pg.parameters.get(k)))
            for pg in pgs:
                row.append(str(pg.parameters.get(k)))
            rows.append(row)
        
        table.add_rows(rows)
        table_str = table.draw()
        lines = table_str.split('\n')
        self._print(lines, highlight_keys)
        
    def do_compare_db_instances(self, names):
        names_list = names.split(',')
        dbis = []
        for name in names_list:
            dbi = DBInstance.objects.find_last(name.strip())
            if dbi is not None and dbi.status != 'deleted':
                dbis.append(dbi)
        if len(names_list) == 1:
            dbi = DBInstance.objects.find_last(names_list[0])
            prev = dbi.previous_version
            if prev is not None and prev.status != 'deleted':
                dbis.append(prev)
        
        if len(dbis) <= 1:
            raise Exception, 'No comparisons can be made.'
        
        table = Texttable(max_width=200)
        table.set_deco(Texttable.HEADER)
        rows = []
        header = []
        header.append('Key')
        for dbi in dbis:
            header.append('ID: %d - %s' % (dbi.id, dbi.name))
        rows.append(header)
        
        keys = []
        highlight_keys = []
        for dbi in dbis:
            keys.extend(dbi.parameters.keys())
        keys = set(keys)
        for k in sorted(keys):
            row = []
            row.append(k)
            vals = []
            for dbi in dbis:
                row.append(str(dbi.parameters.get(k)))
                vals.append(str(dbi.parameters.get(k)))
                
            if len(set(vals)) > 1:
                highlight_keys.append(k)
                
            rows.append(row)
        
        table.add_rows(rows)
        table_str = table.draw()
        lines = table_str.split('\n')
        self._print(lines, highlight_keys)
