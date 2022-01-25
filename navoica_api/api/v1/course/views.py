from rest_framework.generics import ListAPIView
from openedx.core.djangoapps.enrollments.serializers import CourseSerializer
from lms.djangoapps.course_api.views import CourseDetailView, CourseListUserThrottle
from lms.djangoapps import branding
from lms.djangoapps.courseware.access import _can_enroll_courselike
from lms.djangoapps.courseware.access_utils import (
    ACCESS_DENIED,
    ACCESS_GRANTED,
)
from common.djangoapps.student.models import CourseEnrollment


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
                    "course_id": "course-v1:Test+Test+Test",
                    "course_name": "Test",
                    "enrollment_start": null,
                    "enrollment_end": null,
                    "course_start": "2030-01-01T00:00:00Z",
                    "course_end": null,
                    "invite_only": false,
                    "course_modes": [
                        {
                            "slug": "audit",
                            "name": "Audit",
                            "min_price": 0,
                            "suggested_prices": "",
                            "currency": "usd",
                            "expiration_datetime": null,
                            "description": null,
                            "sku": null,
                            "bulk_sku": null
                        }
                    ]
                },
                {
                    "course_id": "course-v1:edX+E2E-101+course",
                    "course_name": "E2E Test Course",
                    "enrollment_start": null,
                    "enrollment_end": null,
                    "course_start": "2016-01-01T00:00:00Z",
                    "course_end": "2028-12-31T00:00:00Z",
                    "invite_only": false,
                    "course_modes": [
                        {
                            "slug": "audit",
                            "name": "Audit",
                            "min_price": 0,
                            "suggested_prices": "",
                            "currency": "usd",
                            "expiration_datetime": null,
                            "description": null,
                            "sku": null,
                            "bulk_sku": null
                        }
                    ]
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
        courses = branding.get_visible_courses()
        courses = courses.order_by("-start")

        user = self.request.user

        return_courses = []

        for course in courses:
            if _can_enroll_courselike(user, course) == ACCESS_GRANTED and not CourseEnrollment.is_enrolled(user,
                                                                                                           course.id):
                return_courses.append(course)
                if self.request.GET.get('size') and len(return_courses) >= int(self.request.GET.get('size')):
                    break

        return return_courses
