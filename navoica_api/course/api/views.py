from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions
from opaque_keys.edx.keys import CourseKey
from lms.djangoapps.courseware import courses

from navoica_api.course.api.serializers.course_serializers import *
from navoica_api.course.models import *
from xmodule.modulestore.django import modulestore
from django.conf import settings
from django_countries.fields import Country
from django_countries import countries


class GetCourseExtendedInfo(APIView):
    """
    * Allow any to access this view.

    **Example Request**
            GET /api/navoica/v1/course/info/{course_id}/

    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, course_id, format=None):
        """
        Return a list of all users.
        """

        course_key = CourseKey.from_string(course_id)
        course = courses.get_course_by_id(course_key)

        c_settings = course.other_course_settings
        course_run = modulestore().get_course(course_key)

        external_enroll_url_data = None
        if c_settings.get('external_enroll') and c_settings.get('external_enroll')['value'] == True:
            external_enroll_url = CourseDisplayValueSerializer(
                data=c_settings.get('external_enroll_url'))
            external_enroll_url.is_valid()
            external_enroll_url_data = external_enroll_url.data

        append_eu_logos_certificate = CourseDisplayValueSerializer(
            data=c_settings.get('append_eu_logos_certificate'))

        append_eu_logos_certificate.is_valid()

        language = next(
            e for e in settings.ALL_LANGUAGES if e[0] == course.language)
        if language:
            language_serializer = CourseLanguageSerializer(
                data={
                    'code': language[0],
                    'title': language[1]
                }
            )
            language_serializer.is_valid()
            language_serializer_data = language_serializer.data

        resp = CourseInfoSerializer(
            data={
                "organizer": CourseOrganizer.objects.get_serialized_or_none(pk=c_settings.get('organizer')),
                "difficulty": CourseDifficulty.objects.get_serialized_or_none(pk=c_settings.get('difficulty')),
                "category": CourseCategory.objects.get_serialized_or_none(pk=c_settings.get('course_category')),
                "external_enroll_url": external_enroll_url_data,
                "append_eu_logos_certificate": append_eu_logos_certificate.data,
                "availability": c_settings.get('availability'),
                "course_organization": course_run.id.org,
                "course_name": course_run.id.course,
                "course_run": course_run.id.run,
                "course_language": language_serializer_data,
            })
        resp.is_valid()

        return Response(
            resp.data

        )
