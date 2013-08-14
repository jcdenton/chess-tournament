# -*- encoding: utf-8 -*-
from django.conf.urls import patterns, url
from django.views import generic

from . import views

urlpatterns = patterns('',
                       url(r'^$', generic.RedirectView.as_view(url='tournaments/'), name='index'),
                       url(r'^tournaments/$', views.TournamentListView.as_view(), name='tournament_list'),
                       url(r'^tournaments/(?P<pk>\d+)/$', views.TournamentDetailView.as_view(), name='tournament_detail'),
                       )
