"""
Convenience methods for working with datetime objects
"""

from common.djangoapps.util.date_utils import strftime_localized
from django.conf import settings
from pytz import timezone


def get_default_time_display(dtime):
    """
    it is used to override function from common.djangoapps.util.date_utils edx module

    Converts a datetime to a string representation. This is the default
    representation used in Studio and LMS.

    It will use the "DATE_TIME" format in the current language, if provided,
    or defaults to "Apr 09, 2013 at 16:00" from TIME_ZONE setting.

    If None is passed in for dt, an empty string will be returned.

    """
    if dtime is None:
        return u""
    if dtime.tzinfo is not None:
        try:
            timezone_str = u" " + dtime.tzinfo.tzname(dtime)
        except NotImplementedError:
            timezone_str = dtime.strftime('%z')
    else:
        timezone_str = u" UTC"

    if settings.USE_TZ and settings.TIME_ZONE and dtime.tzinfo:
        return strftime_localized(dtime.astimezone(timezone(settings.TIME_ZONE)), "DATE_TIME")
    else:
        localized = strftime_localized(dtime, "DATE_TIME")
        return (localized + timezone_str).strip()
