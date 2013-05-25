import collections

from django.db import models
from jsonfield import JSONField

import managers

class ParameterGroup(models.Model):
    name = models.CharField(max_length=100)
    region = models.CharField(max_length=100, blank=True, null=True, default=None)
    family = models.CharField(max_length=100, blank=True, null=True, default=None)
    description = models.CharField(max_length=250, blank=True, null=True, default=None)
    parameters = JSONField(blank=True, null=True, default=None,
                            load_kwargs={'object_pairs_hook': collections.OrderedDict})
    run_time = models.DateTimeField(blank=True, null=True, default=None)
    
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
    
    objects = managers.ParameterGroupManager()
    
    class Meta:
        db_table = 'param_groups'
    
    def __unicode__(self):
        pg_str = 'Parameter Group: %s\nParameters:' % (self.name)
        if not self.parameters is None:
            for k in sorted(self.parameters.keys()):
                pg_str += '\n%s: %s' % (k, self.parameters.get(k))
        else:
            pg_str += 'None'
        return pg_str
        
    @property
    def status(self):
        status = self.__class__.objects.status(self)
        return status
        
class DBInstance(models.Model):
    name = models.CharField(max_length=100)
    region = models.CharField(max_length=100, blank=True, null=True, default=None)
    endpoint = models.CharField(max_length=250, blank=True, null=True, default=None)
    port = models.PositiveIntegerField(blank=True, null=True, default=None)
    parameter_group_name = models.CharField(max_length=100, blank=True, null=True, default=None)
    parameters = JSONField(blank=True, null=True, default=None,
                            load_kwargs={'object_pairs_hook': collections.OrderedDict})
    run_time = models.DateTimeField(blank=True, null=True, default=None)
    
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
    
    objects = managers.DBInstanceManager()
    
    class Meta:
        db_table = 'db_instances'
    
    def __unicode__(self):
        instance_str = 'DB Instance: %s\nParameters:' % (self.name)
        if not self.parameters is None:
            for k in sorted(self.parameters.keys()):
                instance_str += '\n%s: %s' % (k, self.parameters.get(k))
        else:
            instance_str += 'None'
        return instance_str
        
    @property
    def status(self):
        status = self.__class__.objects.status(self)
        return status
        
class CollectorRun(models.Model):
    collector = models.CharField(max_length=25, null=True, blank=True, default=None)
    last_run = models.DateTimeField(null=True, blank=True, default=None)
    
    class Meta:
        db_table = 'collector_runs'
    
    def __unicode__(self):
        return 'CollectorRun: %s' % (self.collector)
    
class Snapshot(models.Model):
    txn = models.IntegerField(null=True, blank=True, default=None)
    collector_run = models.ForeignKey(CollectorRun, null=True, blank=True, default=None)
    statistic_id = models.IntegerField(null=True, blank=True, default=None)
    parent_txn = models.IntegerField(null=True, blank=True, default=None)
    run_time = models.DateTimeField(null=True, blank=True, default=None)
    
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
    
    objects = managers.SnapshotManager()
    
    class Meta:
        db_table = 'snapshots'
