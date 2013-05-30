from django.conf.urls import patterns, include, url
from django.core.urlresolvers import reverse_lazy
from django.views.generic import RedirectView

from rds import views

urlpatterns = patterns('',
        url(r'^$', RedirectView.as_view(url=reverse_lazy("param_group_list"),), name='index'),
        
        url(r'^param-group/$', views.ParameterGroupListView.as_view(), name='param_group_list'),
        url(r'^param-group/report/$', views.ParameterGroupReportView.as_view(), name='param_group_report'),
        url(r'^param-group/compare/$', views.ParameterGroupCompareView.as_view(), name='param_group_compare'),
        url(r'^param-group/(?P<pk>\d+)/$', views.ParameterGroupDetailView.as_view(), name='param_group_detail'),
        
        url(r'^db-instance/$', views.DBInstanceListView.as_view(), name='db_instance_list'),
        url(r'^db-instance/report/$', views.DBInstanceReportView.as_view(), name='db_instance_report'),
        url(r'^db-instance/compare/$', views.DBInstanceCompareView.as_view(), name='db_instance_compare'),
        url(r'^db-instance/(?P<pk>\d+)/$', views.DBInstanceDetailView.as_view(), name='db_instance_detail'),
        
        url(r'^recent-changes/$', views.RecentChangesView.as_view(), name='recent_changes'),
        
)
