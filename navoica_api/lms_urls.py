from django.conf import settings
from django.conf.urls import include, url
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView
from lms.sitemaps import CourseOverviewSitemap

LMS_URLS = [
    url(
        r"^sitemap\.xml$",
        sitemap,
        {"sitemaps": {"courses": CourseOverviewSitemap()}},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    url(r"^api/navoica/", include("navoica_api.api.urls", namespace="navoica_api")),
    url(
        r"^robots\.txt$",
        TemplateView.as_view(
            template_name="robots-allow.txt"
            if settings.LMS_BASE == "navoica.pl"
            else "robots.txt",
            content_type="text/plain",
        ),
        name="robots",
    ),
]
