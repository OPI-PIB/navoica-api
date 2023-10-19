"""
URLS for LMS
"""

from django.conf.urls import url
from django.urls import include


urlpatterns = [
    url(r"^api/navoica/", include("navoica_api.api.urls")),
    url(r"", include("navoica_api.urls")),
    url(r"", include("lms.urls")),
]