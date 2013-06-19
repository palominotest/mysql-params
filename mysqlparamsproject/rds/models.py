import collections
import ConfigParser
import os
import re

from django.conf import settings
from django.db import models

import boto.rds
import paramiko
from jsonfield import JSONField

import managers
from utils import get_all_dbparameters, ParamComparer

class StatisticMixin(object):
    
    @property
    def status(self):
        status = self.__class__.objects.status(self)
        return status
        
    @property
    def previous_version(self):
        prev = self.__class__.objects.previous_version(self)
        return prev
        
    @property
    def ordered_parameters(self):
        if self.parameters is not None:
            return collections.OrderedDict(sorted(self.parameters.items(), key=lambda t: t[0]))
        else:
            return {}
            
    @property
    def params_changed_from_prev(self):
        prev = self.previous_version
        changed_parameters = self.__class__.objects.get_changed_parameters(prev, self)
        return changed_parameters

class ParameterGroup(models.Model, StatisticMixin):
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

class DBInstance(models.Model, StatisticMixin):
    RDS = 'rds'
    HOST = 'host'
    DBINSTANCE_TYPE_CHOICES = (
        (RDS, RDS),
        (HOST, HOST),
    )

    name = models.CharField(max_length=100)
    region = models.CharField(max_length=100, blank=True, null=True, default=None)
    endpoint = models.CharField(max_length=250, blank=True, null=True, default=None)
    port = models.PositiveIntegerField(blank=True, null=True, default=None)
    parameter_group_name = models.CharField(max_length=100, blank=True, null=True, default=None)
    parameters = JSONField(blank=True, null=True, default=None,
                            load_kwargs={'object_pairs_hook': collections.OrderedDict})
    db_instance_type = models.CharField(max_length=25, blank=True, null=True, default=None,
                                        choices=DBINSTANCE_TYPE_CHOICES)
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
        
    def get_difference_with_pg_or_cf(self):
        res = []
        if self.parameters is None:
            pass
        elif self.db_instance_type == self.RDS:
            conn = boto.rds.connect_to_region(self.region, aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
            pg = conn.get_all_dbparameter_groups(self.parameter_group_name)[0]
            pg = get_all_dbparameters(pg)
            res = []
            for p in sorted(pg.modifiable()):
                key = p.name.replace('-', '_')
                pg_val = p._value
                if pg_val is not None and key in self.parameters:
                    if key in settings.FORWARD_KEY_LOOKUP.keys():
                        dbi_val = self.parameters.get(settings.FORWARD_KEY_LOOKUP.get(key))
                    else:
                        dbi_val = self.parameters.get(key)
                    comparer = ParamComparer(key=key, val=pg_val, dbi_val=dbi_val)
                    regex = re.search('{.*}', pg_val)
                    # Don't process pg values with pseudo variables
                    if regex is None:
                        equal = comparer.params_equal()
                        if not equal:
                            res.append({
                                'key': key,
                                'val': comparer.normalize_val(pg_val),
                                'dbi_val': comparer.normalize_val(dbi_val),
                            })
        elif self.db_instance_type == self.HOST:
            host = None
            for h in settings.NON_RDS_HOSTS:
                if self.name == h.get('hostname'):
                    host = h
            hostname = host.get('hostname')
            ssh_user = host.get('ssh_user')
            identity_file = host.get('identity_file')
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(hostname, username=ssh_user, key_filename=identity_file)
            sftp_client = ssh_client.open_sftp()
            temp_file = os.path.join(settings.PROJECT_ROOT, 'temp_my.cnf')
            if os.path.isfile(temp_file):
                os.remove(temp_file)
            sftp_client.get(settings.MYSQL_CNF_FILE_PATH, temp_file)
            config = ConfigParser.ConfigParser(allow_no_value=True)
            config.readfp(open(temp_file))
            if config.has_section('mysqld'):
                items = dict(config.items('mysqld'))
                params_dict = {}
                for k in items.keys():
                    if items.get(k) is None:
                        params_dict[k] = 'ON'
                    else:
                        params_dict[k] = items.get(k)
                for k,v in params_dict.items():
                    key = k.replace('-', '_')
                    if key in self.parameters:
                        if key in settings.FORWARD_KEY_LOOKUP.keys():
                            dbi_val = self.parameters.get(settings.FORWARD_KEY_LOOKUP.get(key))
                        else:
                            dbi_val = self.parameters.get(key)
                        comparer = ParamComparer(key=key, val=v, dbi_val=dbi_val)
                        equal = comparer.params_equal()
                        if not equal:
                            res.append({
                                'key': key,
                                'val': comparer.normalize_val(v),
                                'dbi_val': comparer.normalize_val(dbi_val),
                            })
            if os.path.isfile(temp_file):
                os.remove(temp_file)
        return res
        
class ConfigFile(models.Model, StatisticMixin):
    name = models.CharField(max_length=200)     # This is the hostname
    parameters = JSONField(blank=True, null=True, default=None,
                            load_kwargs={'object_pairs_hook': collections.OrderedDict})
    raw_content = models.TextField(blank=True, null=True, default='')
    run_time = models.DateTimeField(blank=True, null=True, default=None)
    
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
    
    objects = managers.ConfigFileManager()
    
    class Meta:
        db_table = 'config_files'
        
    def __unicode__(self):
        return self.name
        
    @property
    def to_string(self):
        cf_str = 'Config File: %s\nParameters:' % (self.name)
        if not self.parameters is None:
            for k in sorted(self.parameters.keys()):
                cf_str += '\n%s: %s' % (k, self.parameters.get(k))
        else:
            cf_str += 'None'
        return cf_str
        
class CollectorRun(models.Model):
    RDS_STAT = 'rds'
    NON_RDS_STAT = 'non-rds'
    MIXED_STAT = 'mixed'
    COLLECTOR_TYPE_CHOICES = (
        (RDS_STAT, RDS_STAT),
        (NON_RDS_STAT, NON_RDS_STAT),
        (MIXED_STAT, MIXED_STAT),
    )

    collector = models.CharField(max_length=25, blank=True, null=True, default=None)
    collector_type = models.CharField(max_length=25, blank=True, null=True,
                                        default=None, choices=COLLECTOR_TYPE_CHOICES)
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
