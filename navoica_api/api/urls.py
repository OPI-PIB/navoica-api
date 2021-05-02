"""
Api URLs.
"""

from __future__ import absolute_import, unicode_literals

from django.conf.urls import include, url
from django.contrib.sitemaps.views import sitemap

from navoica_api.sitemaps import CourseOverviewSitemap

app_name = 'navoica_api'

urlpatterns = [
    url(r'^v1/', include('navoica_api.api.v1.urls')),
    url(r'^sitemap\.xml$', sitemap, {'sitemaps': {'courses': CourseOverviewSitemap()}},
        name='django.contrib.sitemaps.views.sitemap'),
]
