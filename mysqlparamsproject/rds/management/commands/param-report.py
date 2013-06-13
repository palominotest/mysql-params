import logging
import re
import sys
import traceback
from datetime import datetime, timedelta
from itertools import groupby
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.mail import send_mail

from texttable import Texttable

from rds.models import CollectorRun, ParameterGroup, DBInstance, ConfigFile
from rds.utils import get_needs_restart

logger = logging.getLogger('mysqlparams')

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            '--stat',
            dest='stat',
            default=None,
            help='Report a single <statistic>. See --list-stats for available statistics.',
        ),
        make_option(
            '--list-stats',
            action='store_true',
            dest='list_stats',
            default=False,
            help='List available statistics.'
        ),
        make_option(
            '-o',
            '--output',
            dest='output',
            default='text',
            help='Specifies an output formatter. One of: email, text'
        ),
        make_option(
            '-s',
            '--since',
            dest='since',
            default='',
            help='Where <since> is something like: last(since the last collector run), 4h(4 hours), 1d(1 day), 1w(1 week)',
        ),
    )

    def handle(self, *args, **options):
        if options.get('list_stats'):
            print 'Available Statistics:'
            collector_runs = CollectorRun.objects.all()
            for i,collector_run in enumerate(collector_runs):
               print '%d. %s' % (i+1, collector_run.collector)
            sys.exit(0)
    
        find_type = 'normal'
        sql_conditions = {}
        try:
            stat = options.get('stat')
            stats = CollectorRun.objects.all().values_list('collector', flat=True)
            output = options.get('output')
            
            since_regex = re.search('(\d+(?:\.?\d+)?)([hdwm])?', options.get('since', ''))
            if options.get('since') == 'last':
                find_type = 'last'
            elif since_regex is not None:
                num, unit = since_regex.groups()
                num = float(num)
                if unit == 'h':
                    time = datetime.now() - timedelta(hours=num)
                elif unit == 'd':
                    time = datetime.now() - timedelta(days=num)
                elif unit == 'w':
                    time = datetime.now() - timedelta(weeks=num)
                elif unit == 'm':
                    time = datetime.now() - timedelta(minutes=num)
                else:
                    time = datetime.now() - timedelta(seconds=num)
                sql_conditions['since'] = time
                
            if find_type == 'normal':
                pg_query = ParameterGroup.objects.all()
                dbi_query = DBInstance.objects.all()
                cf_query = ConfigFile.objects.all()
            else:
                pg_query = ParameterGroup.objects.find_versions('parameter_group', txn='latest')
                dbi_query = DBInstance.objects.find_versions('db_instance', txn='latest')
                cf_query = ConfigFile.objects.find_versions('config_file', txn='latest')
                
            if sql_conditions.get('since') is not None:
                pg_query = pg_query.filter(run_time__gte=sql_conditions.get('since'))
                dbi_query = dbi_query.filter(run_time__gte=sql_conditions.get('since'))
                cf_query = cf_query.filter(run_time__gte=sql_conditions.get('since'))
            
            pg_query = pg_query.order_by('-run_time')
            dbi_query = dbi_query.order_by('-run_time')
            cf_query = cf_query.order_by('-run_time')
            
            if output in ('text', 'email',):
                lines = []    
                if stat is None:
                    lines = self.get_lines(pg_query=pg_query, dbi_query=dbi_query, cf_query=cf_query, output=output)
                elif stat == 'parameter_group':
                    lines = self.get_lines(pg_query=pg_query, output=output)
                elif stat == 'db_instance':
                    lines = self.get_lines(dbi_query=dbi_query, output=output)
                elif stat == 'config_file':
                    lines = self.get_lines(cf_query=cf_query, output=output)
                
                res = '\n'.join(lines)    
                if output == 'text':
                    print res
                elif output == 'email':
                    subject = '%s Report' % (settings.EMAIL_SUBJECT_PREFIX)
                    body = res
                    from_email = settings.DEFAULT_FROM_EMAIL
                    to_emails = []
                    for admin in settings.ADMINS:
                        to_emails.append(admin[1])
                    send_mail(subject, body, from_email, to_emails, fail_silently=False)
                sys.exit(0)
            if output == 'nagios':
                dbi_query = DBInstance.objects.find_versions('db_instance', txn='latest')
                needs_restart = get_needs_restart(dbi_query)
                res = []
                if len(needs_restart) > 0:
                    res.append('The following instances may need to be restarted.')
                    for i,dbi_tuple in enumerate(needs_restart):
                        dbi = dbi_tuple[0]
                        diff = dbi_tuple[1]
                        res.append('%d. Region: %s Name: %s Endpoint: %s Port: %s Parameter Group: %s' % ((i+1), 
                                    dbi.region, dbi.name, dbi.endpoint, dbi.port, dbi.parameter_group_name))
                        res.append('\tParameter Differences:')
                        for param in diff:
                            res.append("\t- %s: Parameter Group/Config File Value: %s, DB Instance Value: %s" % (param.get('key'), param.get('val'), param.get('dbi_val')))
                    print '\n'.join(res)
                    sys.exit(1)     #Nagios WARNING
                else:
                    res.append('OK')
                    print '\n'.join(res)
                    sys.exit(0)     #Nagios OK
        except Exception, e:
            tb = traceback.format_exc()
            logger.error(tb)
            
    def get_lines(self, pg_query=None, dbi_query=None, cf_query=None, output='text'):
        lines = []
        if pg_query is not None:
            lines.append('Reporting Parameter Groups:')
            empty = True
            for run_time,group in groupby(pg_query, key=lambda row: row.run_time):
                empty = False
                if output == 'text':
                    table = Texttable()
                    table.set_cols_width([10, 15, 10, 30, 20])
                    table.set_deco(Texttable.HEADER)
                    rows = [['Status', 'Name', 'Family', 'Description', 'Created Time']]
                    lines.append('-- %s %s' % (run_time, ('-'*74)))
                    for element in group:
                        rows.append([element.status, element.name, element.family, element.description, element.created_time])
                    table.add_rows(rows)
                    lines.append(table.draw())
                    lines.append('')
                elif output == 'email':
                    lines.append('-- %s' % (run_time))
                    for element in group:
                        lines.append('[%s] Family: %s Name: %s' % (element.status, element.family, element.name))
                    lines.append('')
            if empty:
                lines.append('No changes.')
        if dbi_query is not None:
            lines.append('Reporting DB Instances:')
            empty = True
            for run_time,group in groupby(dbi_query, key=lambda row: row.run_time):
                empty = False
                if output == 'text':
                    table = Texttable()
                    table.set_cols_width([10, 5, 15, 10, 30, 5, '15', 20])
                    table.set_deco(Texttable.HEADER)
                    rows = [['Status', 'Type', 'Name', 'Region', 'Endpoint', 'Port', 'Parameter Group', 'Created Time']]
                    lines.append('-- %s %s' % (run_time, ('-'*108)))
                    for element in group:
                        rows.append([element.status, element.db_instance_type, element.name, element.region, element.endpoint, 
                                    element.port, element.parameter_group_name, element.created_time])
                    table.add_rows(rows)
                    lines.append(table.draw())
                    lines.append('')
                elif output == 'email':
                    lines.append('-- %s' % (run_time))
                    for element in group:
                        lines.append('[%s] Region: %s Name: %s Endpoint: %s Port: %s' % (element.status, element.region, 
                                                                            element.name, element.endpoint, element.port))
                    lines.append('')
            if empty:
                lines.append('No changes.')
        if cf_query is not None:
            lines.append('Reporting Config Files:')
            empty = True
            for run_time, group in groupby(cf_query, key=lambda row: row.run_time):
                empty = False
                if output == 'text':
                    table = Texttable()
                    table.set_cols_width([10, 30, 20])
                    table.set_deco(Texttable.HEADER)
                    rows = [['Statuus', 'Name', 'Created Time']]
                    lines.append('-- %s %s' % (run_time, ('-'*43)))
                    for element in group:
                        rows.append([element.status, element.name, element.created_time])
                    table.add_rows(rows)
                    lines.append(table.draw())
                    lines.append('')
                elif output == 'email':
                    lines.append('-- %s' % (run_time))
                    for element in group:
                        lines.append('[%s] Name: %s' % (element.status, element.name))
                    lines.append('')
            if empty:
                lines.append('No changes.')
        return lines
