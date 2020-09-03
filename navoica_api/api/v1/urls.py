
from . import views

from django.conf.urls import url

urlpatterns = [

    url(r'^progress/{username}/courses/{course_id}'.format(
        username=r'(?P<username>[^/]*)',
        course_id=r'(?P<course_id>[^/+]+(/|\+)[^/+]+(/|\+)[^/?]+)',
        ),
        views.CourseProgressView.as_view(),
        name='progress')
]
