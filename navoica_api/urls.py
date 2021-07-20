from django.conf import settings
from django.conf.urls import url
from django.contrib.sitemaps.views import sitemap
from static_template_view import views

from navoica_api.certificates import api
from navoica_api.sitemaps import CourseOverviewSitemap

urlpatterns = [
    url(r'^legend', views.render, {'template': 'legend.html'}, name="legend"),
    url(r'^accessibility$', views.render, {'template': 'accessibility.html'}, name="accessibility"),
    url(r'^cookies$', views.render, {'template': 'cookies.html'}, name="cookies"),

    url(r'^sitemap\.xml$', sitemap, {'sitemaps': {'courses': CourseOverviewSitemap()}},
        name='django.contrib.sitemaps.views.sitemap'),

    url(r'^start_merge_certificates/{course_id}/'.format(course_id=settings.COURSE_ID_PATTERN, ),
        api.start_merge_certificates, name='start_merge_certificates'),
]
