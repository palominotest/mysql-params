from django.shortcuts import get_object_or_404
from django.views import generic

from rds.models import ParameterGroup, DBInstance

class ParameterGroupListView(generic.ListView):
    template_name = 'rds/param_group_list.html'
    context_object_name = 'param_groups'
    
    def get_queryset(self):
        pg_names = ParameterGroup.objects.values_list('name', flat=True).distinct()
        pgs = []
        for name in pg_names:
            pg = ParameterGroup.objects.find_last(name)
            if pg is not None:
                pgs.append(pg)
        return pgs
        
class DBInstanceListView(generic.ListView):
    template_name = 'rds/db_instance_list.html'
    context_object_name = 'db_instances'
    
    def get_queryset(self):
        dbi_names = DBInstance.objects.values_list('name', flat=True).distinct()
        dbis = []
        for name in dbi_names:
            dbi = DBInstance.objects.find_last(name)
            if dbi is not None:
                dbis.append(dbi)
        return dbis
        
class ParameterGroupDetailView(generic.DetailView):
    template_name = 'rds/param_group_detail.html'
    context_object_name = 'param_group'
    model = ParameterGroup
    
class DBInstanceDetailView(generic.DetailView):
    template_name = 'rds/db_instance_detail.html'
    context_object_name = 'db_instance'
    model = DBInstance
    
class ParameterGroupReportView(generic.ListView):
    template_name = 'rds/param_group_report.html'
    context_object_name = 'param_groups'
    
    def get_queryset(self):
        queryset = ParameterGroup.objects.all()
        return queryset
