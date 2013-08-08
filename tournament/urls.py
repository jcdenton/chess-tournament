# -*- encoding: utf-8 -*-
from django.conf.urls import patterns, url
from django.views import generic

from . import views

urlpatterns = patterns('',
                       url(r'^$', generic.RedirectView.as_view(url='tournaments/'), name='index'),
                       url(r'^tournaments/', views.TournamentsView.as_view(), name='tournaments'),
                       )
