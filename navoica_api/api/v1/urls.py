"""
Navoica API URLs.
"""
from django.conf import settings
from django.conf.urls import include, url
from navoica_api.api.v1.branding.urls import BRANDING_URLS
from rest_framework import routers
from navoica_api.api.v1 import views
from navoica_api.api.v1.course.urls import COURSES_URLS
from navoica_api.api.v1.views import UserApiView

app_name = 'v1'

PROGRESS_URLS = ([
    url(r'^{username}/courses/{course_id}/$'.format(
        username=settings.USERNAME_PATTERN,
        course_id=settings.COURSE_ID_PATTERN,
    ),
        views.CourseProgressApiView.as_view(),
        name='detail'),
],   'progress')

CERTIFICATES_URLS = ([
    url(
        r'^courses/{course_id}/$'.format(
            course_id=settings.COURSE_ID_PATTERN
        ),
        views.CertificatesListView.as_view(), name='list'
    ),
], 'certificates')

UPDATEMESSAGES_URLS = ([
    url(r'^{username}/courses/{course_id}/$'.format(
        username=settings.USERNAME_PATTERN,
        course_id=settings.COURSE_ID_PATTERN,
    ),
        views.CourseUpdatesMessagesApiView.as_view(),
        name='list'),
],   'updates')

USER_URLS = ([
    url(
        r'^me$',
        UserApiView.as_view(),
        name='user_me'
    ),
], 'user_api')

POWERFORM_URLS = ([
    url(
        r'^{course_id}/$'.format(course_id=settings.COURSE_ID_PATTERN),
        views.PowerFormApiView.as_view(),
        name='powerformcheck'
    ),
], 'powerformcheck_api')

GRADE_URLS = ([
    url(
        r'^courses/{course_id}/$'.format(course_id=settings.COURSE_ID_PATTERN),
        views.CourseGradesApiView.as_view(),
        name='detail'
    ),
], 'grades_api')

router = routers.SimpleRouter()
router.register(r'courseopinions', views.CourseRunOpinionViewSet, basename='courseopinion')
router.register(r'career',  views.CareerViewSet, basename='career')

urlpatterns = [
    url(r'^progress/', include(PROGRESS_URLS, namespace='progress')),
    url(r'^user/', include(USER_URLS, namespace='user')),
    url(r'^certificates/', include(CERTIFICATES_URLS)),
    url(r'^updates/', include(UPDATEMESSAGES_URLS)),
    url(r'^branding/', include(BRANDING_URLS)),
    url(r'^grades/', include(GRADE_URLS)),
    url(r'^courses_list/', include(COURSES_URLS)),
    url(r'^powerformcheck/', include(POWERFORM_URLS)),
    url(r'^', include(router.urls)),
]
