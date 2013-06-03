import logging
import sys
import traceback
from datetime import datetime
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

import boto.rds
import MySQLdb
import MySQLdb.cursors
from MySQLdb import OperationalError

from rds.models import CollectorRun, Snapshot, ParameterGroup, DBInstance
from rds.utils import get_all_dbinstances, get_all_dbparameter_groups, get_all_dbparameters

logger = logging.getLogger('mysqlparams')

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            '--stat',
            dest='stat',
            default=None,
            help='Collect a single <statistic>. See --list-stats for available statistics.',
        ),
        make_option(
            '--list-stats',
            action='store_true',
            dest='list_stats',
            default=False,
            help='List available statistics.'
        ),
    )

    def handle(self, *args, **options):
        collect_parameter_group = self.collect_parameter_group
        collect_db_instance = self.collect_db_instance
    
        if options.get('list_stats'):
            print 'Available Statistics:'
            collector_runs = CollectorRun.objects.all()
            for i,collector_run in enumerate(collector_runs):
               print '%d. %s' % (i+1, collector_run.collector)
            sys.exit(0)
        
        try:
            with transaction.commit_on_success():
                stat = options.get('stat')
                stats = CollectorRun.objects.all().values_list('collector', flat=True)
                txn_id = Snapshot.objects.get_next_txn()
                run_time = datetime.now()
                collect_data = {}
                
                for region in settings.AWS_REGIONS:
                    conn = boto.rds.connect_to_region(region, aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                                        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
                    logger.info("[region start]: %s" % (region))
                    if stat is None:
                        for statistic in stats:
                            collector_run = CollectorRun.objects.get(collector=statistic)
                            collector_run.last_run = run_time
                            collector_run.save()
                            func = locals().get('collect_%s' % (statistic))
                            prev_snapshot, cur_snapshot = func(conn, run_time)
                            if collect_data.get(statistic) is None:
                                collect_data[statistic] = []
                                print "NEW TXN: %d" % (txn_id)
                                print "CHANGED: %s" % (True if prev_snapshot != cur_snapshot else False)
                                collect_data[statistic].append((statistic, prev_snapshot, cur_snapshot))
                    elif stat in stats:
                        collector_run = CollectorRun.objects.get(collector=stat)
                        collector_run.last_run = run_time
                        collector_run.save()
                        func = locals().get('collect_%s' % (stat))
                        prev_snapshot, cur_snapshot = func(conn, run_time)
                        if collect_data.get(stat) is None:
                                collect_data[stat] = []
                                print "NEW TXN: %d" % (txn_id)
                                print "CHANGED: %s" % (True if prev_snapshot != cur_snapshot else False)
                                collect_data[stat].append((stat, prev_snapshot, cur_snapshot))
                    logger.info("[region end]: %s" % (region))            
                
                for v in collect_data.values():
                    changed = False
                    for i in v:
                        if i[1] != i[2]:
                            changed = True
                            break
                    if changed:
                        for i in v:
                            self._save_txn(i, txn_id, run_time)
        except Exception, e:
            tb = traceback.format_exc()
            logger.error(tb)
            
    def _find_in_instances(self, name, instances):
        for instance in instances:
            if name == instance.id:
                return instance
        return None
        
    def _find_in_pgs(self, name, pgs):
        for pg in pgs:
            if name == pg.name:
                return pg
        return None
        
    def _snapshot_updated(self, snapshot, new_id, old_id):
        snapshot.add((new_id, old_id))
        try:
            snapshot.remove(old_id)
        except KeyError:
            pass
            
    def _save_txn(self, i, txn, run_time):
        collector_run = CollectorRun.objects.get_or_create(collector=i[0])[0]
        collector_run.save()
        cur_snapshot = i[2]
        for j in cur_snapshot:
            snap = Snapshot(txn=txn, collector_run=collector_run, run_time=run_time)
            if isinstance(j, list) or isinstance(j, tuple) or isinstance(j, set):
                snap.statistic_id = j[0]
                p_txn = Snapshot.objects.find_last_by_statistic_id(j[1])
                if p_txn is not None:
                    snap.parent_txn = p_txn.id
            else:
                snap.statistic_id = j
            snap.save()
        
    def _save_run_ids(self, i, txn):
        for i in self.cur_snapshot:
            snap = Snapshot(txn=txn, collector_run=self.runref,
                            run_time=self.runref.last_run)
            if isinstance(i, list) or isinstance(i, tuple) or isinstance(i, set):
                snap.statistic_id = i[0]
                p_txn = Snapshot.objects.find_last_by_statistic_id(i[1])
                if p_txn is not None:
                    snap.parent_txn = p_txn.id
            else:
                snap.statistic_id = i
            snap.save()
    
    def collect_parameter_group(self, conn, run_time):
        region = conn.region.name
        logger.info('[parameter groups start]')
        pgs = get_all_dbparameter_groups(conn)
        prev_snapshot = set(ParameterGroup.objects.find_versions('parameter_group', txn='latest').values_list('id', flat=True))
        cur_snapshot = prev_snapshot.copy()
        prev_version = ParameterGroup.objects.filter(id__in=prev_snapshot)
        for pg in pgs:
            if pg.DBParameterGroupFamily not in ('mysql5.5', 'mysql5.1'):
                continue
            pg = get_all_dbparameters(pg)
            new_pg = ParameterGroup(
                name=pg.name,
                region=region,
                family=pg.DBParameterGroupFamily,
                description=pg.description,
                run_time=run_time,
            )
            parameters = {}
            for k in pg.keys():
                parameters[k] = pg.get(k)._value
            new_pg.parameters = parameters
            old_pg = ParameterGroup.objects.find_last(new_pg.name)
            
            if old_pg is None or old_pg.parameters is None:
                new_pg.save()
                cur_snapshot.add(new_pg.id)
                logger.info('[new] %s' % (new_pg.name))
            elif len(ParameterGroup.objects.get_changed_parameters(old_pg, new_pg)) > 0:
                new_pg.save()
                self._snapshot_updated(cur_snapshot, new_pg.id, old_pg.id)
                logger.info('[changed] %s' % (new_pg.name))
            logger.debug("\n%s\n" % (new_pg))
        
        for pg in prev_version:
            logger.info('[delete-check] %s' % (pg.name))
            g = self._find_in_pgs(pg.name, pgs)
            if g is None and not ParameterGroup.objects.deleted(pg):
                del_pg = ParameterGroup(
                    name=pg.name,
                    region=pg.region,
                    family=pg.family,
                    description=pg.description,
                    parameters=None,
                    run_time=run_time,
                )
                del_pg.save()
                self._snapshot_updated(cur_snapshot, del_pg.id, pg.id)
                logger.info("[deleted] %s" % (del_pg.name))
        logger.info('[parameter groups end]')
        return prev_snapshot, cur_snapshot
    
    def collect_db_instance(self, conn, run_time):
        region = conn.region.name
        logger.info('[db instances start]')
        instances = get_all_dbinstances(conn)
        prev_snapshot = set(DBInstance.objects.find_versions('db_instance', txn='latest').values_list('id', flat=True))
        cur_snapshot = prev_snapshot.copy()
        prev_version = DBInstance.objects.filter(id__in=prev_snapshot)
        for instance in instances:
            endpoint = instance.endpoint
            parameter_group = instance.parameter_group
            new_dbi = DBInstance(
                name=instance.id,
                region=region,
                endpoint=endpoint[0],
                port=endpoint[1],
                parameter_group_name=parameter_group.name,
                run_time=run_time
            )
            try:
                mysql_conn = MySQLdb.connect(host=new_dbi.endpoint, port=new_dbi.port,
                                            user=settings.RDS_MYSQL_USER,
                                            passwd=settings.RDS_MYSQL_PASSWORD,
                                            cursorclass=MySQLdb.cursors.DictCursor)
            except OperationalError, e:
                logger.error('[error] Unable to connect to RDS Instance %s' % (instance.id))
                continue
            cursor = mysql_conn.cursor()
            cursor.execute('SHOW GLOBAL VARIABLES')
            rows = cursor.fetchall()
            parameters = {}
            for row in rows:
                parameters[row.get('Variable_name')] = row.get('Value')
            new_dbi.parameters = parameters
            old_dbi = DBInstance.objects.find_last(new_dbi.name)
            
            if old_dbi is None or old_dbi.parameters is None:
                new_dbi.save()
                cur_snapshot.add(new_dbi.id)
                logger.info('[new] %s' % (new_dbi.name))
            elif len(DBInstance.objects.get_changed_parameters(old_dbi, new_dbi)) > 0:
                new_dbi.save()
                self._snapshot_updated(cur_snapshot, new_dbi.id, old_dbi.id)
                logger.info('[changed] %s' % (new_dbi.name))
            logger.debug('\n%s\n' % (new_dbi))
            
        for dbi in prev_version:
            logger.info('[delete-check] %s' % (dbi.name))
            g  = self._find_in_instances(dbi.name, instances)
            if g is None and not DBInstance.objects.deleted(dbi):
                del_dbi = DBInstance(
                    name=dbi.name,
                    region=dbi.region,
                    endpoint=dbi.endpoint,
                    port=dbi.port,
                    parameter_group_name=dbi.parameter_group_name,
                    parameters=None,
                    run_time=run_time,
                )
                del_dbi.save()
                self._snapshot_updated(cur_snapshot, del_dbi.id, dbi.id)
                logger.info("[deleted] %s" % (del_dbi.name))
        logger.info("[db instances end]")
        return prev_snapshot, cur_snapshot
