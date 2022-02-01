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
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from django.db.models import Q


class UnEnrollmentCourseListView(ListAPIView):
    """
    **Use Cases**

        Request all courses visible and unenrollment to the specified user ordered by start date of course.

    **Example Requests**

        GET /api/navoica/v1/courses_list/unenrollment_courses?size=1

    **Response Values**

        List of objects using CourseSerializer

    **Parameters**

        size (optional):
            Limit courses. Default: no limit - all courses

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
    pagination_class = None

    def get_queryset(self):
        """
        Return courses visible and unenrollment to the user.
        """
        now = datetime.now(UTC)
        courses = branding.get_visible_courses()
        # there is missing one situation when: now > start && enrollment_start is null & enrollment_end is null
        courses = courses.filter(Q(enrollment_start__lte=now) | Q(enrollment_start__isnull=True)).filter(
            Q(enrollment_end__gte=now) | Q(enrollment_end__isnull=True)).filter(
            Q(end__gte=now) | Q(end__isnull=True)).order_by("-start")

        user = self.request.user

        return_courses = []

        for course in courses:

            if not (
                    course.enrollment_start is None and course.enrollment_end is None and course.start > now) and _can_enroll_courselike(
                    user, course) == ACCESS_GRANTED and not CourseEnrollment.is_enrolled(user,
                                                                                         course.id):
                return_courses.append(course)
                if self.request.GET.get('size') and len(return_courses) >= int(self.request.GET.get('size')):
                    break

        return return_courses
