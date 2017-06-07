from django.conf.urls import url

from . import views

app_name = 'register'
urlpatterns = [
    url(r'^$', views.root, name='root'),
    url(r'^new/$', views.edit, name='new'),
    url(r'^edit/(?P<id>\d+)/$', views.edit, name='edit'),
    url(r'^delete/(?P<id>\d+)/$', views.delete, name='delete'),
    url(r'^archive/(?P<id>\d+)/$', views.archive, name='archive'),
    url(r'^teamremove/(?P<teamid>\d+)/(?P<blogid>\d+)/$', views.remove_from_team, name='remove_from_team'),

    url(r'^blogposts/(\d+)/hide/(\d+)/$', views.blogpost_hide, name='hide'),
    url(r'^blogposts/(\d+)/unhide/(\d+)/$', views.blogpost_unhide, name='unhide'),
]
