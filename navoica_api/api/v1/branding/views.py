from branding.views import footer
from django.conf import settings
from django.core.cache import cache
from django.utils import translation
from django.utils.translation.trans_real import get_supported_language_variant
from lms.djangoapps.branding.api import _footer_copyright, _footer_logo_img, _footer_social_links, \
    _footer_business_links, _footer_mobile_links, _footer_more_info_links, _footer_connect_links, _footer_openedx_link, \
    _footer_navigation_links, _footer_legal_links
import six

def navoica_footer(request):
    accepts = request.META.get('HTTP_ACCEPT', '*/*')

    language = request.GET.get('language', translation.get_language())
    try:
        language = get_supported_language_variant(language)
    except LookupError:
        language = settings.LANGUAGE_CODE

    is_secure = request.is_secure()

    cache_key = u"branding.footer.{params}.json".format(
        params=six.moves.urllib.parse.urlencode({
            'language': language,
            'is_secure': request.is_secure(),
        })
    )

    footer_dict = {
        "copyright": _footer_copyright(),
        "logo_image": _footer_logo_img(is_secure),
        "social_links": _footer_social_links(),
        "business_links": _footer_business_links(language),
        "mobile_links": _footer_mobile_links(is_secure),
        "more_info_links": _footer_more_info_links(language),
        "connect_links": _footer_connect_links(language),
        "openedx_link": _footer_openedx_link(),
        "navigation_links": _footer_navigation_links(language),
        "legal_links": _footer_legal_links(language),
    }

    cache.set(cache_key, footer_dict, settings.FOOTER_CACHE_TIMEOUT)

    return footer(request)
