"""
Navoica API URLs.
"""
from django.conf import settings
from django.conf.urls import include, url

from navoica_api.api.v1 import views
from navoica_api.api.v1.views import UserApiView

PROGRESS_URLS = [
    url(r'^{username}/courses/{course_id}/$'.format(
        username=settings.USERNAME_PATTERN,
        course_id=settings.COURSE_ID_PATTERN,
    ),
        views.CourseProgressApiView.as_view(),
        name='detail')
]

USER_URLS = [
    url(
        r'^me$',
        UserApiView.as_view(),
        name='user_me'
    ),
]

urlpatterns = [
    url(r'^progress/', include(PROGRESS_URLS, namespace='progress')),
    url(r'^user/', include(USER_URLS, namespace='user')),
]
