import collections
import re

from django.conf import settings
from django.db import models

import boto.rds
from jsonfield import JSONField

import managers
from utils import get_all_dbparameters

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
        return self.name
        
    @property
    def to_string(self):
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
        
    @property
    def ordered_parameters(self):
        if self.parameters is not None:
            return collections.OrderedDict(sorted(self.parameters.items(), key=lambda t: t[0]))
        else:
            return {}
        
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
        return self.name
    
    @property
    def to_string(self):
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
        
    @property
    def ordered_parameters(self):
        if self.parameters is not None:
            return collections.OrderedDict(sorted(self.parameters.items(), key=lambda t: t[0]))
        else:
            return {}
        
    def get_difference_with_pg(self):
        conn = boto.rds.connect_to_region(self.region, aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
        res = []
        pg = conn.get_all_dbparameter_groups(self.parameter_group_name)[0]
        pg = get_all_dbparameters(pg)
        res = []
        for k in pg.keys():
            pg_val = pg.get(k)._value
            if pg_val == '0':
                pg_val = 'OFF'
            if pg_val == '1':
                pg_val = 'ON'
            if str(pg_val).endswith('/'):
                pg_val = pg_val[:-1]
            if pg_val != None:
                dbi_val = self.parameters.get(k)
                if str(dbi_val).endswith('/'):
                    dbi_val = dbi_val[:-1]
                regex = re.search('{.*}', pg_val)
                # Don't process pg values with pseudo variables
                if regex is None and pg_val != dbi_val:
                    res.append({
                        'key': k,
                        'pg_val': pg_val,
                        'dbi_val': dbi_val,
                    })
        return res
        
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
