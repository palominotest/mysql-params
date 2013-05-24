# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ParameterGroup'
        db.create_table('param_groups', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('description', self.gf('django.db.models.fields.CharField')(default=None, max_length=250, null=True, blank=True)),
            ('parameters', self.gf('jsonfield.fields.JSONField')(default=None, null=True, blank=True)),
            ('run_time', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('created_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'rds', ['ParameterGroup'])

        # Adding model 'DBInstance'
        db.create_table('db_instances', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('endpoint', self.gf('django.db.models.fields.CharField')(default=None, max_length=250, null=True, blank=True)),
            ('port', self.gf('django.db.models.fields.PositiveIntegerField')(default=None, null=True, blank=True)),
            ('parameter_group_name', self.gf('django.db.models.fields.CharField')(default=None, max_length=100, null=True, blank=True)),
            ('parameters', self.gf('jsonfield.fields.JSONField')(default=None, null=True, blank=True)),
            ('run_time', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('created_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'rds', ['DBInstance'])

        # Adding model 'CollectorRun'
        db.create_table('collector_runs', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('collector', self.gf('django.db.models.fields.CharField')(default=None, max_length=25, null=True, blank=True)),
            ('last_run', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
        ))
        db.send_create_signal(u'rds', ['CollectorRun'])

        # Adding model 'Snapshot'
        db.create_table('snapshots', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('txn', self.gf('django.db.models.fields.IntegerField')(default=None, null=True, blank=True)),
            ('collector_run', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['rds.CollectorRun'], null=True, blank=True)),
            ('statistic_id', self.gf('django.db.models.fields.IntegerField')(default=None, null=True, blank=True)),
            ('parent_txn', self.gf('django.db.models.fields.IntegerField')(default=None, null=True, blank=True)),
            ('run_time', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('created_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'rds', ['Snapshot'])


    def backwards(self, orm):
        # Deleting model 'ParameterGroup'
        db.delete_table('param_groups')

        # Deleting model 'DBInstance'
        db.delete_table('db_instances')

        # Deleting model 'CollectorRun'
        db.delete_table('collector_runs')

        # Deleting model 'Snapshot'
        db.delete_table('snapshots')


    models = {
        u'rds.collectorrun': {
            'Meta': {'object_name': 'CollectorRun', 'db_table': "'collector_runs'"},
            'collector': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '25', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_run': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'})
        },
        u'rds.dbinstance': {
            'Meta': {'object_name': 'DBInstance', 'db_table': "'db_instances'"},
            'created_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'endpoint': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '250', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parameter_group_name': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'parameters': ('jsonfield.fields.JSONField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'port': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'run_time': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'updated_time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'rds.parametergroup': {
            'Meta': {'object_name': 'ParameterGroup', 'db_table': "'param_groups'"},
            'created_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '250', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parameters': ('jsonfield.fields.JSONField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'run_time': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'updated_time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'rds.snapshot': {
            'Meta': {'object_name': 'Snapshot', 'db_table': "'snapshots'"},
            'collector_run': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['rds.CollectorRun']", 'null': 'True', 'blank': 'True'}),
            'created_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent_txn': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'run_time': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'statistic_id': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'txn': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'updated_time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['rds']