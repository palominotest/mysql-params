from django.conf.urls import patterns, include, url
from django.core.urlresolvers import reverse_lazy

from rds import views

urlpatterns = patterns('',
        #url(r'^$', RedirectView.as_view(url=reverse_lazy("server_list"),), name='index'),
        
        url(r'^param-group/$', views.ParameterGroupListView.as_view(), name='param_group_list'),
        url(r'^param-group/(?P<pk>\d+)/$', views.ParameterGroupDetailView.as_view(), name='param_group_detail'),
        
        url(r'^db-instance/$', views.DBInstanceListView.as_view(), name='db_instance_List'),
        url(r'^db-instance/(?P<pk>\d+)/$', views.DBInstanceDetailView.as_view(), name='db_instance_detail'),
        
)
