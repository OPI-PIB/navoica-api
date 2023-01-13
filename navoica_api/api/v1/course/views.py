from datetime import datetime

from rest_framework.generics import ListAPIView
from lms.djangoapps.course_api.serializers import CourseSerializer
from lms.djangoapps.course_api.views import CourseDetailView, CourseListUserThrottle
from lms.djangoapps import branding
from lms.djangoapps.courseware.access import _can_enroll_courselike
from lms.djangoapps.courseware.access_utils import (
    ACCESS_DENIED,
    ACCESS_GRANTED,
)
from common.djangoapps.student.models import CourseEnrollment
from pytz import UTC
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from edx_rest_framework_extensions.paginators import DefaultPagination


class UnEnrollmentCourseListView(ListAPIView):
    """
    **Use Cases**

        Request all courses visible (or not) and available for the specified user.

    **Example Requests**

        GET /api/navoica/v1/courses_list/unenrollment_courses?catalog_visibility=none&ordering=-start_date&search=edX

    **Response Values**

        List of objects using CourseSerializer

    **Parameters**

        Field filters
            catalog_visibility:  both, about, none
            start_date_gte: Start date is greater than or equal to
            start_date_lte: Start date is less than or equal to
            start_date: Start date
            start_date_gt: Start date is greater than
            start_date_lt: Start date is less than
            Invitation only: true, false, null

        Ordering
            start_date - ascending
            start_date - descending
            enrollment_start - ascending
            enrollment_start - descending
            enrollment_end - ascending
            enrollment_end - descending

        Search:
            org, display_name from CourseOverview

    **Returns**

        * 200 on success, with a list of course discovery objects as returned using CourseSerializer.

        Example response:

            [
                {
                    "blocks_url": "https://dev-04.kdm/api/courses/v2/blocks/?course_id=course-v1%3AedX%2BDemoX%2BDemo_Course",
                    "effort": null,
                    "end": null,
                    "enrollment_start": null,
                    "enrollment_end": null,
                    "id": "course-v1:edX+DemoX+Demo_Course",
                    "media": {
                        "course_image": {
                            "uri": "/asset-v1:edX+DemoX+Demo_Course+type@asset+block@images_course_image.jpg"
                        },
                        "course_video": {
                            "uri": null
                        },
                        "image": {
                            "raw": "https://dev-04.kdm/asset-v1:edX+DemoX+Demo_Course+type@asset+block@images_course_image.jpg",
                            "small": "https://dev-04.kdm/asset-v1:edX+DemoX+Demo_Course+type@asset+block@images_course_image.jpg",
                            "large": "https://dev-04.kdm/asset-v1:edX+DemoX+Demo_Course+type@asset+block@images_course_image.jpg"
                        }
                    },
                    "name": "Demonstration Course",
                    "number": "DemoX",
                    "org": "edX",
                    "short_description": null,
                    "start": "2013-02-05T05:00:00Z",
                    "start_display": "Feb. 5, 2013",
                    "start_type": "timestamp",
                    "pacing": "instructor",
                    "mobile_available": false,
                    "hidden": false,
                    "invitation_only": false,
                    "course_id": "course-v1:edX+DemoX+Demo_Course"
                }
            ]
        """
    serializer_class = CourseSerializer
    throttle_classes = (CourseListUserThrottle,)
    pagination_class = DefaultPagination
    filter_backends = (OrderingFilter, DjangoFilterBackend, SearchFilter)
    filterset_fields = {'catalog_visibility': ['exact'], 'start_date': ['gte', 'lte', 'exact', 'gt', 'lt'],
                        'invitation_only': ['exact']}
    search_fields = ('org', 'display_name')
    ordering_fields = ('start_date', 'enrollment_start', 'enrollment_end')

    def get_queryset(self):
        """
        Return courses available for the user.
        """
        now = datetime.now(UTC)
        courses = branding.get_visible_courses()

        courses = courses.filter(Q(enrollment_start__lte=now) | Q(enrollment_start__isnull=True)).filter(
            Q(enrollment_end__gte=now) | Q(enrollment_end__isnull=True)).filter(
            Q(end__gte=now) | Q(end__isnull=True)).exclude(enrollment_start__isnull=True, enrollment_end__isnull=True,
                                                           start__gte=now)

        user = self.request.user

        for course in courses:
            if _can_enroll_courselike(
                    user, course) == ACCESS_DENIED or CourseEnrollment.is_enrolled(user, course.id):
                courses = courses.exclude(pk=str(course.id))
        return courses

class HomeCourses(ListAPIView):
    """
    **Use Cases**

        Request 8 new courses for homepage

    **Example Requests**

        GET /api/navoica/v1/courses_list/home_courses

    **Response Values**

        List of objects using CourseSerializer

    **Returns**

        * 200 on success, with a list of course discovery objects as returned using CourseSerializer.
        """

    def get_queryset(self):
        """
        Return 8 new courses for homepage.
        """
        from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
        courses = CourseOverview.get_all_courses()
        return courses.order_by('id')[:8]