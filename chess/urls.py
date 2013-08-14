# -*- encoding: utf-8 -*-
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import RedirectView

admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^$', RedirectView.as_view(url='tournament/')),
                       url(r'^tournament/', include('tournament.urls', namespace='tournament')),
                       url(r'^admin/', include(admin.site.urls)),
                       url(r'^djangojs/', include('djangojs.urls')),
                       )
