from django.conf import settings
from django.conf.urls import include, url
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from machina import urls as machina_urls
from openedx.core.djangoapps.site_configuration import \
    helpers as configuration_helpers

CMS_URLS = [
    url("forum/", include(machina_urls)),
]

CMS_URLS += [
    url(
        r"^robots\.txt$",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
        name="robots",
    )
]

# Favicon
favicon_path = configuration_helpers.get_value(
    "favicon_path", settings.FAVICON_PATH
)  # pylint: disable=invalid-name
CMS_URLS += [
    url(
        r"^favicon\.ico$",
        RedirectView.as_view(url=settings.STATIC_URL + favicon_path, permanent=True),
    ),
]
