"""
Branding API endpoint urls.
"""
from django.conf.urls import url
# from navoica_api.api.v1.branding.views import navoica_footer

BRANDING_URLS = [
    url(r"^footer$", "branding_footer"),
]
