from django.conf.urls import url
from django.conf import settings
from navoica_api.course.api.views import GetCourseExtendedInfo

COURSE_INFO_URLS = [
    url(r'^info/{course_id}/$'.format(course_id=settings.COURSE_ID_PATTERN), GetCourseExtendedInfo.as_view(), name="extended_info_course"),
]
