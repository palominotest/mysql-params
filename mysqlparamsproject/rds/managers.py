import time
from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.query import QuerySet

# Snapshot Manager
class SnapshotMixin(object):

    def find_last_by_statistic_id(self, id_):
        snaps = self.filter(statistic_id=id_)
        if snaps.count() > 0:
            return snaps.order_by('-id')[0]
        else:
            return None

class SnapshotQuerySet(QuerySet, SnapshotMixin):
    pass
    
class SnapshotManager(models.Manager, SnapshotMixin):
    
    def get_query_set(self):
        return SnapshotQuerySet(self.model, using=self._db)
    
    def head(self, collector=None):
        head = self.all().aggregate(models.Max('txn'))
        head['txn__max'] = 0 if head['txn__max'] is None else head['txn__max']
        return head.get('txn__max')
    
    def get_next_txn(self):
        return self.head() + 1
        
    def stat_is_new(self, stat_obj):
        return self.filter(collector_run__id=stat_obj.collector_id, statistic_id=stat_obj.id).count() == 1
        
# Collector Mixin
class CollectorMixin(object):
    
    def find_versions(self, name, txn=None):
        res = self.all()
        CollectorRun = models.get_model('rds', 'CollectorRun')
        Snapshot = models.get_model('rds', 'Snapshot')
        collector_run = CollectorRun.objects.get_or_create(collector=name)[0]
        
        if collector_run.collector == 'parameter_group':
            db_table = 'param_groups'
        elif collector_run.collector == 'db_instance':
            db_table = 'db_instances'
        
        latest_txn = None
        try:
            latest_txn = Snapshot.objects.filter(collector_run__id=collector_run.id).order_by('-txn')[0].txn
        except Exception:
            latest_txn = Snapshot.objects.head()
        
        if isinstance(txn, int) and txn < 0:
            txn = latest_txn
            txn = 0 if txn < 0 else txn
        elif isinstance(txn, int) and txn > latest_txn:
            txn = latest_txn
        elif txn == 'latest':
            txn = latest_txn
        
        res = res.extra(
            tables = ['snapshots'],
            where = ['snapshots.collector_run_id=%s %s AND %s.id=snapshots.statistic_id' % (str(collector_run.id),
                                                                                            '' if txn is None else 'AND snapshots.txn=%s' % (str(txn)),
                                                                                            db_table)]
        )
        return res
        
    def get_changed_parameters(self, old_instance, new_instance):
        res = []
        if old_instance is None or new_instance is None:
            return res
        old_params = old_instance.parameters
        new_params = new_instance.parameters
        if old_params is None or new_params is None:
            return res
        keys = sorted(set(old_params.keys() + new_params.keys()))
        for k in keys:
            old_val = old_instance.parameters.get(k)
            new_val = new_instance.parameters.get(k)
            if old_val != new_val:
                res.append({
                    'key': k,
                    'old_val': old_val,
                    'new_val': new_val,
                })
        return res
        
    def find_last(self, name):
        res = self.filter(name=name).order_by('-id')
        if res.count() > 0:
            return res[0]
        else:
            return None
            
    def previous_version(self, instance):
        res = self.filter(id__lt=instance.id, name=instance.name)
        if res.count() > 0:
            return res.order_by('-id')[0]
        else:
            return None
        
    def get_or_none(self, *args, **kwargs):
        try:
            return self.get(*args, **kwargs)
        except ObjectDoesNotExist:
            return None
            
    def create_unreachable_entry(self, host, run_time):
        raise NotImplementedError, "This is an abstract method."
    
    def unreachable(self, instance):
        raise NotImplementedError, "This is an abstract method."
    
    def deleted(self, instance):
        raise NotImplementedError, "This is an abstract method."
    
    def changed(self, instance):
        raise NotImplementedError, "This is an abstract method."    
    
    def history(self, instance, since=datetime.fromtimestamp(time.mktime([0,0,0,0,0,0,0,0,0]))):
        return self.filter(id__lte=instance.id, run_time__gte=since, name=instance.name)
    
    def new(self, instance):
        last = self.previous_version(instance)
        return self.history(instance).count() == 1 or (last is not None and self.deleted(instance))
    
    def status(self, instance):
        if self.unreachable(instance):
            return 'unreachable'
        elif self.deleted(instance):
            return 'deleted'
        elif self.new(instance):
            return 'new'
        elif self.changed(instance):
            return 'changed'
        else:
            return 'unchanged'
        
class ParameterGroupMixin(CollectorMixin):
    pass
        
class ParameterGroupQuerySet(QuerySet, ParameterGroupMixin):
    pass
    
class ParameterGroupManager(models.Manager, ParameterGroupMixin):
    
    def get_query_set(self):
        return ParameterGroupQuerySet(self.model, using=self._db)
    
    def create_unreachable_entry(self, name, run_time):
        self.create(
            name=name,
            region=None,
            family=None,
            description=None,
            parameters=None,
            run_time=run_time,
        )
        
    def unreachable(self, instance):
        return instance.region is None and instance.family is None and \
                instance.description is None and instance.parameters is None
    
    def deleted(self, instance):
        return instance.parameters is None
        
    def changed(self, instance):
        last = self.previous_version(instance)
        return last is None or self.deleted(instance) or len(self.get_changed_parameters(last, instance)) > 0
        
class DBInstanceMixin(CollectorMixin):
    pass
        
class DBInstanceQuerySet(QuerySet, DBInstanceMixin):
    pass
    
class DBInstanceManager(models.Manager,DBInstanceMixin):
    
    def get_query_set(self):
        return DBInstanceQuerySet(self.model, using=self._db)
        
    def create_unreachable_entry(self, name, run_time):
        self.create(
            name=name,
            region = None,
            endpoint=None,
            port=None,
            parameter_group_name=None,
            parameters=None,
            run_time=run_time,
        )
        
    def unreachable(self, instance):
        return instance.region is None and instance.endpoint is None and instance.port is None and \
                instance.parameters is None and instance.parameter_group_name is None 
    
    def deleted(self, instance):
        return instance.parameters is None
        
    def changed(self, instance):
        last = self.previous_version(instance)
        return last is None or self.deleted(instance) or len(self.get_changed_parameters(last, instance)) > 0
