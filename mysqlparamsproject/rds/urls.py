from django.conf.urls import patterns, include, url
from django.core.urlresolvers import reverse_lazy
from django.views.generic import RedirectView

from rds import views

urlpatterns = patterns('',
        url(r'^$', RedirectView.as_view(url=reverse_lazy("param_group_list"),), name='index'),
        
        url(r'^param-group/$', views.ParameterGroupListView.as_view(), name='param_group_list'),
        url(r'^param-group/report/$', views.ParameterGroupReportView.as_view(), name='param_group_report'),
        url(r'^param-group/report/download/$', views.ParameterGroupReportDownloadView.as_view(), name='param_group_report_download'),
        url(r'^param-group/compare/$', views.ParameterGroupCompareView.as_view(), name='param_group_compare'),
        url(r'^param-group/(?P<pk>\d+)/$', views.ParameterGroupDetailView.as_view(), name='param_group_detail'),
        
        url(r'^db-instance/$', views.DBInstanceListView.as_view(), name='db_instance_list'),
        url(r'^db-instance/report/$', views.DBInstanceReportView.as_view(), name='db_instance_report'),
        url(r'^db-instance/report/download/$', views.DBInstanceReportDownloadView.as_view(), name='db_instance_report_download'),
        url(r'^db-instance/compare/$', views.DBInstanceCompareView.as_view(), name='db_instance_compare'),
        url(r'^db-instance/(?P<pk>\d+)/$', views.DBInstanceDetailView.as_view(), name='db_instance_detail'),
        
        url(r'^config-file/$', views.ConfigFileListView.as_view(), name='config_file_list'),
        url(r'^config-file/report/$', views.ConfigFileReportView.as_view(), name='config_file_report'),
        url(r'^config-file/report/download/$', views.ConfigFileReportDownloadView.as_view(), name='config_file_report_download'),
        url(r'^config-file/compare/$', views.ConfigFileCompareView.as_view(), name='config_file_compare'),
        url(r'^config-file/(?P<pk>\d+)/$', views.ConfigFileDetailView.as_view(), name='config_file_detail'),
        
        url(r'^recent-changes/$', views.RecentChangesView.as_view(), name='recent_changes'),
        
)
