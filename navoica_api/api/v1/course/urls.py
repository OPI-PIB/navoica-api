from navoica_api.api.v1.course.views import UnEnrollmentCourseListView
from django.conf.urls import url

COURSES_URLS = [
    url(r"^unenrollment_courses", UnEnrollmentCourseListView.as_view(), name="unenrollment_courses"),
]
