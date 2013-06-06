import sys
import logging
import traceback

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.mail import send_mail

from rds.models import CollectorRun, ParameterGroup, DBInstance
from rds.utils import get_sorted_dict, get_needs_restart

logger = logging.getLogger('mysqlparams')

class Command(BaseCommand):

    def handle(self, *args, **options):
        try:
            pg_collector = CollectorRun.objects.get(collector='parameter_group')
            dbi_collector = CollectorRun.objects.get(collector='db_instance')
            pgs = ParameterGroup.objects.filter(run_time=pg_collector.last_run)
            dbis = DBInstance.objects.filter(run_time=dbi_collector.last_run)
            dbi_query = DBInstance.objects.find_versions('db_instance', txn='latest')
            pgs_dict = get_sorted_dict(pgs)
            dbis_dict = get_sorted_dict(dbis)
            needs_restart = get_needs_restart(dbi_query)
            res = []
                    
            res.append('Parameter Groups:')
            res.append('')
            res.append('New:')
            new_pgs = pgs_dict.get('new', [])
            if len(new_pgs) == 0:
                res.append('No new parameter groups.')
            else:
                for i,pg in enumerate(new_pgs):
                    res.append('%d. Family: %s Name: %s' % ((i+1), pg.family, pg.name))
            res.append('')
            res.append('Deleted:')
            deleted_pgs = pgs_dict.get('deleted', [])
            if len(deleted_pgs) == 0:
                res.append('No deleted parameter groups.')
            else:
                for i,pg in enumerate(deleted_pgs):
                    res.append('%d. Family: %s Name: %s' % ((i+1), pg.family, pg.name))
            res.append('')
            res.append('Changed:')
            changed_pgs = pgs_dict.get('changed', [])
            if len(changed_pgs) == 0:
                res.append('No changed parameter groups.')
            else:
                for i,pg in enumerate(changed_pgs):
                    prev = ParameterGroup.objects.previous_version(pg)
                    res.append('%d. Family: %s Name: %s' % ((i+1), pg.family, pg.name))
                    res.append('\tOLD ID: %d, NEW ID: %d' % (prev.id, pg.id))
                    res.append('\tChanged Parameters:')
                    changed_params = ParameterGroup.objects.get_changed_parameters(prev, pg)
                    for param in changed_params:
                        res.append("\t- %s: %s -> %s" % (param.get('key'), param.get('old_val'), param.get('new_val')))
            res.append('')            
            
            res.append('DB Instances:')
            res.append('')
            res.append('New:')
            new_dbis = dbis_dict.get('new', [])
            if len(new_dbis) == 0:
                res.append('No new database instances.')
            else:
                for i,dbi in enumerate(new_dbis):
                    res.append('%d. Region: %s Name: %s Endpoint: %s Port: %s' % ((i+1), dbi.region, dbi.name, dbi.endpoint, dbi.port))
            res.append('')
            res.append('Deleted:')
            deleted_dbis = dbis_dict.get('deleted', [])
            if len(deleted_dbis) == 0:
                res.append('No deleted database instances.')
            else:
                for i,dbi in enumerate(deleted_dbis):
                    res.append('%d. Region: %s Name: %s Endpoint: %s Port: %s' % ((i+1), dbi.region, dbi.name, dbi.endpoint, dbi.port))
            res.append('')
            res.append('Changed:')
            changed_dbis = dbis_dict.get('changed', [])
            if len(changed_dbis) == 0:
                res.append('No changed database instances.')
            else:
                for i,dbi in enumerate(changed_dbis):
                    prev = DBInstance.objects.previous_version(dbi)
                    res.append('%d. Region: %s Name: %s Endpoint: %s Port: %s' % ((i+1), dbi.region, dbi.name, dbi.endpoint, dbi.port))
                    res.append('\tOLD ID: %d, NEW ID: %d' % (prev.id, dbi.id))
                    res.append('\tChanged Parameters:')
                    changed_params = DBInstance.objects.get_changed_parameters(prev, dbi)
                    for param in changed_params:
                        res.append("\t- %s: %s -> %s" % (param.get('key'), param.get('old_val'), param.get('new_val')))
            res.append('')
            
            res.append('The following instances may need to be restarted.')
            if len(needs_restart) > 0:
                for i,dbi_tuple in enumerate(needs_restart):
                    dbi = dbi_tuple[0]
                    diff = dbi_tuple[1]
                    res.append('%d. Region: %s Name: %s Endpoint: %s Port: %s Parameter Group: %s' % ((i+1), 
                                dbi.region, dbi.name, dbi.endpoint, dbi.port, dbi.parameter_group_name))
                    res.append('\tParameter Differences:')
                    for param in diff:
                        res.append("\t- %s: Parameter Group Value: %s, DB Instance Value: %s" % (param.get('key'), param.get('pg_val'), param.get('dbi_val')))
            else:
                res.append('No instance needs to be restarted.')
            
            subject = '%s Change Alert' % (settings.EMAIL_SUBJECT_PREFIX)
            body = '\n'.join(res)
            from_email = settings.DEFAULT_FROM_EMAIL
            to_emails = []
            for admin in settings.ADMINS:
                to_emails.append(admin[1])
            send_mail(subject, body, from_email, to_emails, fail_silently=False)
        except Exception, e:
            tb = traceback.format_exc()
            logger.error(tb)
