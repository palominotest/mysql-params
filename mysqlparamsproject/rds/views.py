import csv
from datetime import datetime
from itertools import groupby

from django import http
from django.shortcuts import get_object_or_404
from django.views import generic

from rds.models import CollectorRun, ParameterGroup, DBInstance
from rds.utils import str_to_datetime, get_sorted_dict, get_needs_restart

class ListMixin(generic.ListView):

    def get_queryset(self):
        names = super(ListMixin, self).get_queryset().values_list('name', flat=True).distinct()
        objs = []
        for name in names:
            obj = self.model.objects.find_last(name)
            if obj is not None:
                objs.append(obj)
        return objs
        
class ReportMixin(generic.ListView):
    
    def get_queryset(self):
        queryset = self.model.objects.all().order_by('-run_time')
        since = self.request.GET.get('since')
        if since is not None and len(since) != 0:
            dtime = str_to_datetime(since)
            if dtime is not None:
                queryset = queryset.filter(run_time__gte=dtime)
        return queryset
        
    def get_context_data(self, **kwargs):
        context = super(ReportMixin, self).get_context_data(**kwargs)
        context['since'] = self.request.GET.get('since')
        return context
        
class ReportDownloadMixin(ReportMixin):

    def get_rows(self):
        raise Exception, 'This is an abstract method.'
        
    def get_filename(self):
        raise Exception, 'This is an abstract method.'
    
    def get(self, request, *args, **kwargs):
        rows = self.get_rows()
        response = http.HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="%s"' % (self.get_filename()) 
        writer = csv.writer(response)
        for row in rows:
            writer.writerow(row)
        return response

class ParameterGroupListView(ListMixin):
    template_name = 'rds/param_group_list.html'
    context_object_name = 'param_groups'
    model = ParameterGroup
        
class DBInstanceListView(ListMixin):
    template_name = 'rds/db_instance_list.html'
    context_object_name = 'db_instances'
    model = DBInstance
        
class ParameterGroupDetailView(generic.DetailView):
    template_name = 'rds/param_group_detail.html'
    context_object_name = 'param_group'
    model = ParameterGroup
    
class DBInstanceDetailView(generic.DetailView):
    template_name = 'rds/db_instance_detail.html'
    context_object_name = 'db_instance'
    model = DBInstance
    
class ParameterGroupReportView(ReportMixin):
    template_name = 'rds/param_group_report.html'
    context_object_name = 'param_groups'
    model = ParameterGroup
    
class ParameterGroupReportDownloadView(ReportDownloadMixin):
    model = ParameterGroup
    
    def get_filename(self):
        return 'param_group_report(%s).csv' % (datetime.now())
    
    def get_rows(self):
        queryset = self.get_queryset()
        rows = []
        rows.append(['Reporting Parameter Groups:'])
        empty = True
        for run_time,group in groupby(queryset, key=lambda row: row.run_time):
            empty = False
            rows.append(['Status', 'Name', 'Family', 'Description', 'Created Time'])
            for element in group:
                rows.append([element.status, element.name, element.family, element.description, element.created_time])
        if empty:
            rows.append(['No changes.'])
        return rows
    
class DBInstanceReportView(ReportMixin):
    template_name = 'rds/db_instance_report.html'
    context_object_name = 'db_instances'
    model = DBInstance
    
class DBInstanceReportDownloadView(ReportDownloadMixin):
    model = DBInstance
    
    def get_filename(self):
        return 'db_instance_report(%s).csv' % (datetime.now())
    
    def get_rows(self):
        queryset = self.get_queryset()
        rows = []
        rows.append(['Reporting DB Instances:'])
        empty = True
        for run_time,group in groupby(queryset, key=lambda row: row.run_time):
            empty = False
            rows.append(['Status', 'Name', 'Region', 'Endpoint', 'Port', 'Parameter Group', 'Created Time'])
            for element in group:
                rows.append([element.status, element.name, element.region, element.endpoint, 
                            element.port, element.parameter_group_name, element.created_time])
        if empty:
            rows.append(['No changes.'])
        return rows
    
class RecentChangesView(generic.TemplateView):
    template_name = 'rds/recent_changes.html'
    
    def get_context_data(self, **kwargs):
        context = super(RecentChangesView, self).get_context_data(**kwargs)
        pg_collector = CollectorRun.objects.get(collector='parameter_group')
        dbi_collector = CollectorRun.objects.get(collector='db_instance')
        pgs = ParameterGroup.objects.filter(run_time=pg_collector.last_run)
        dbis = DBInstance.objects.filter(run_time=dbi_collector.last_run)
        pgs_dict = get_sorted_dict(pgs)
        dbis_dict = get_sorted_dict(dbis)
        needs_restart = get_needs_restart(dbis)
        context['pgs_dict'] = pgs_dict
        context['dbis_dict'] = dbis_dict
        context['needs_restart'] = get_needs_restart(dbis)
        return context
        
class ParameterGroupCompareView(generic.TemplateView):
    template_name = 'rds/param_group_compare.html'
    
    def get_context_data(self, **kwargs):
        context = super(ParameterGroupCompareView, self).get_context_data(**kwargs)
        request = self.request
        engine = request.REQUEST.get('engine', 'MySQL 5.5')
        object_ids = request.REQUEST.get('object-ids', '')
        object_ids = object_ids.split(',')
        if engine == 'MySQL 5.1':
            default = 'default.mysql5.1'
        else:
            default = 'default.mysql5.5'
        default_pg = ParameterGroup.objects.find_last(default)
        pgs = ParameterGroup.objects.filter(id__in=object_ids)
        if pgs.count() == 1:
            pg = pgs[0]
            prev = pg.previous_version
            pgs = list(pgs)
            pgs.append(prev)
        keys = sorted(default_pg.parameters.keys())
        context['keys'] = keys
        context['default'] = default_pg
        context['param_groups'] = pgs
        return context
    
    def post(self, request, *args, **kwargs):
        return super(ParameterGroupCompareView, self).get(request, *args, **kwargs)
        
    def get(self, request, *args, **kwargs):
        return http.HttpResponseNotAllowed('GET requests are not allowed for this operation.')
        
class DBInstanceCompareView(generic.TemplateView):
    template_name = 'rds/db_instance_compare.html'
    
    def get_context_data(self, **kwargs):
        context = super(DBInstanceCompareView, self).get_context_data(**kwargs)
        request = self.request
        object_ids = request.REQUEST.get('object-ids', '')
        object_ids = object_ids.split(',')
        dbis = DBInstance.objects.filter(id__in=object_ids)
        if dbis.count() == 1:
            dbi = dbis[0]
            prev = dbi.previous_version
            dbis = list(dbis)
            dbis.append(prev)
        keys = []
        for dbi in dbis:
            if dbi.parameters is not None:
                keys.extend(dbi.parameters.keys())
        keys = sorted(set(keys))
        context['keys'] = keys
        context['db_instances'] = dbis
        return context
    
    def post(self, request, *args, **kwargs):
        return super(DBInstanceCompareView, self).get(request, *args, **kwargs)
        
    def get(self, request, *args, **kwargs):
        return http.HttpResponseNotAllowed('GET requests are not allowed for this operation.')
