"""Views for the branding app. """

import logging

import lms.djangoapps.branding.api as branding_api
import six
from common.djangoapps.util.json_request import JsonResponse
from django.conf import settings
from django.core.cache import cache
from django.http import Http404, HttpResponse
from django.utils import translation
from django.utils.translation import ugettext as _
from django.utils.translation.trans_real import get_supported_language_variant
from django.views.decorators.cache import cache_control
from lms.djangoapps.branding.views import _render_footer_html
from openedx.core.djangoapps.lang_pref.api import released_languages
from openedx.core.djangoapps.site_configuration import \
    helpers as configuration_helpers

log = logging.getLogger(__name__)


def _footer_navigation_links():
    """Return the navigation links to display in the footer. """
    platform_name = configuration_helpers.get_value('platform_name', settings.PLATFORM_NAME)
    return [
        {
            "name": link_name,
            "title": link_title,
            "url": link_url,
        }
        for link_name, link_url, link_title in [
            ("faq", "/faq", _("FAQ")),
            ("accessibility", "/accessibility", _("Accessibility Statement")),
            ("legend", "/legend", _("Legend_title")),
            ("career", "/career", _("Career")),
        ]
        if link_url and link_url != "#"
    ]


def _footer_legal_links():

    links = [
        ('tos', '/tos', _('Terms of use')),
        ('honor', '/honor', _('Honor code')),
        ('privacy', '/privacy', _('Privacy Policy')),
        ('cookies', '/cookies', _('Cookies Policy')),
    ]

    return [
        {
            "name": link_name,
            "title": link_title,
            "url": link_url,
        }
        for link_name, link_url, link_title in links
        if link_url and link_url != "#"
    ]


def _footer_connect_links():
    """Return the connect links to display in the footer. """

    return [
        {
            "name": link_name,
            "title": link_title,
            "url": link_url,
        }
        for link_name, link_url, link_title in [
            ("contact", '/contact', _("Contact Us")),
        ]
        if link_url and link_url != "#"
    ]


def get_navoica_footer(is_secure=True):
    footer_dict = branding_api.get_footer(is_secure)
    footer_dict['navigation_links'] = _footer_navigation_links()
    footer_dict['legal_links'] = _footer_legal_links()
    footer_dict['connect_links'] = _footer_connect_links()
    return footer_dict


@cache_control(must_revalidate=True, max_age=settings.FOOTER_BROWSER_CACHE_MAX_AGE)
def navoica_footer(request):
    """Retrieve the branded footer.

    This end-point provides information about the site footer,
    allowing for consistent display of the footer across other sites
    (for example, on the marketing site and blog).

    It can be used in one of two ways:
    1) A client renders the footer from a JSON description.
    2) A browser loads an HTML representation of the footer
        and injects it into the DOM.  The HTML includes
        CSS and JavaScript links.

    In case (2), we assume that the following dependencies
    are included on the page:
    a) JQuery (same version as used in edx-platform)
    b) font-awesome (same version as used in edx-platform)
    c) Open Sans web fonts

    Example: Retrieving the footer as JSON

        GET /api/branding/v1/footer
        Accepts: application/json

        {
            "navigation_links": [
                {
                  "url": "http://example.com/about",
                  "name": "about",
                  "title": "About"
                },
                # ...
            ],
            "social_links": [
                {
                    "url": "http://example.com/social",
                    "name": "facebook",
                    "icon-class": "fa-facebook-square",
                    "title": "Facebook",
                    "action": "Sign up on Facebook!"
                },
                # ...
            ],
            "mobile_links": [
                {
                    "url": "http://example.com/android",
                    "name": "google",
                    "image": "http://example.com/google.png",
                    "title": "Google"
                },
                # ...
            ],
            "legal_links": [
                {
                    "url": "http://example.com/terms-of-service.html",
                    "name": "terms_of_service",
                    "title': "Terms of Service"
                },
                # ...
            ],
            "openedx_link": {
                "url": "https://open.edx.org",
                "title": "Powered by Open edX",
                "image": "http://example.com/openedx.png"
            },
            "logo_image": "http://example.com/static/images/logo.png",
            "copyright": "edX, Open edX and their respective logos are registered trademarks of edX Inc."
        }


    Example: Retrieving the footer as HTML

        GET /api/branding/v1/footer
        Accepts: text/html


    Example: Including the footer with the "Powered by Open edX" logo

        GET /api/branding/v1/footer?show-openedx-logo=1
        Accepts: text/html


    Example: Retrieving the footer in a particular language

        GET /api/branding/v1/footer?language=en
        Accepts: text/html


    Example: Retrieving the footer with a language selector

        GET /api/branding/v1/footer?include-language-selector=1
        Accepts: text/html


    Example: Retrieving the footer with all JS and CSS dependencies (for testing)

        GET /api/branding/v1/footer?include-dependencies=1
        Accepts: text/html

    """
    if not branding_api.is_enabled():
        raise Http404

    # Use the content type to decide what representation to serve
    accepts = request.META.get('HTTP_ACCEPT', '*/*')

    # Show the OpenEdX logo in the footer
    show_openedx_logo = bool(request.GET.get('show-openedx-logo', False))

    # Include JS and CSS dependencies
    # This is useful for testing the end-point directly.
    include_dependencies = bool(request.GET.get('include-dependencies', False))

    # Override the language if necessary
    language = request.GET.get('language', translation.get_language())
    try:
        language = get_supported_language_variant(language)
    except LookupError:
        language = settings.LANGUAGE_CODE

    # Include a language selector
    include_language_selector = request.GET.get('include-language-selector', '') == '1'

    # Render the footer information based on the extension
    if 'text/html' in accepts or '*/*' in accepts:
        cache_params = {
            'language': language,
            'show_openedx_logo': show_openedx_logo,
            'include_dependencies': include_dependencies
        }
        if include_language_selector:
            cache_params['language_selector_options'] = ','.join(sorted([lang.code for lang in released_languages()]))
        cache_key = u"branding.footer.{params}.html".format(params=six.moves.urllib.parse.urlencode(cache_params))

        content = cache.get(cache_key)
        if content is None:
            with translation.override(language):
                content = _render_footer_html(
                    request, show_openedx_logo, include_dependencies, include_language_selector, language
                )
                cache.set(cache_key, content, settings.FOOTER_CACHE_TIMEOUT)
        return HttpResponse(content, status=200, content_type="text/html; charset=utf-8")

    elif 'application/json' in accepts:
        cache_key = u"branding.footer.{params}.json".format(
            params=six.moves.urllib.parse.urlencode({
                'language': language,
                'is_secure': request.is_secure(),
            })
        )
        footer_dict = cache.get(cache_key)
        if footer_dict is None:
            with translation.override(language):
                footer_dict = get_navoica_footer(is_secure=request.is_secure())
                cache.set(cache_key, footer_dict, settings.FOOTER_CACHE_TIMEOUT)
        return JsonResponse(footer_dict, 200, content_type="application/json; charset=utf-8")

    else:
        return HttpResponse(status=406)
