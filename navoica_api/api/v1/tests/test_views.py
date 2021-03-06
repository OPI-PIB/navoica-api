"""
Tests for the Certificate REST APIs.
"""
from collections import OrderedDict
from datetime import datetime, timedelta

from django.core.urlresolvers import reverse
from django.utils import timezone
from freezegun import freeze_time
from oauth2_provider import models as dot_models
from rest_framework import status
from rest_framework.test import APITestCase

from lms.djangoapps.courseware.tests.factories import InstructorFactory, UserFactory
from lms.djangoapps.certificates.models import CertificateStatuses
from lms.djangoapps.certificates.tests.factories import \
    GeneratedCertificateFactory
from student.tests.factories import CourseEnrollmentFactory   # pylint: disable=import-error
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

USER_PASSWORD = 'test'


class CourseProgressApiViewTest(SharedModuleStoreTestCase, APITestCase):
    """
    Test for the Progress REST APIs
    """
    now = timezone.now()

    @classmethod
    def setUpClass(cls):
        super(CourseProgressApiViewTest, cls).setUpClass()
        cls.course = CourseFactory.create(
            org='edx',
            number='verified',
            display_name='Verified Course'
        )

        cls.chapter = ItemFactory.create(
            parent_location=cls.course.location,
            category='chapter',
            display_name="Week 1",
        )
        cls.sequential = ItemFactory.create(
            parent_location=cls.chapter.location,
            category='sequential',
            display_name="Lesson 1",
        )
        cls.vertical = ItemFactory.create(
            parent_location=cls.sequential.location,
            category='vertical',
            display_name='Subsection 1',
        )

        cls.problem = ItemFactory.create(
            parent=cls.vertical,
            category="problem",
            display_name="Test Problem",
        )

        cls.second_course = CourseFactory.create(
            org='edx2',
            number='verified2',
            display_name='Verified Course2'
        )
        cls.second_chapter = ItemFactory.create(
            parent_location=cls.second_course.location,
            category='chapter',
            display_name="Week 1",
        )
        cls.second_sequential = ItemFactory.create(
            parent_location=cls.second_chapter.location,
            category='sequential',
            display_name="Lesson 1",
        )
        cls.second_vertical = ItemFactory.create(
            parent_location=cls.second_sequential.location,
            category='vertical',
            display_name='Subsection 1',
        )

        cls.second_problem = ItemFactory.create(
            parent=cls.second_vertical,
            category="problem",
            display_name="Test Problem",
        )

    def setUp(self):
        freezer = freeze_time(self.now)
        freezer.start()
        self.addCleanup(freezer.stop)

        super(CourseProgressApiViewTest, self).setUp()

        self.student = UserFactory(password=USER_PASSWORD)
        self.instructor_user = InstructorFactory(course_key=self.course.id, password=USER_PASSWORD)
        self.staff_user = UserFactory(password=USER_PASSWORD, is_staff=True)

        self.enrollment = CourseEnrollmentFactory.create(
            user=self.student,
            course_id=self.course.id)

        self.namespaced_url = 'navoica_api:v1:progress:detail'

        # create a configuration for django-oauth-toolkit (DOT)
        dot_app_user = UserFactory.create(password=USER_PASSWORD)
        dot_app = dot_models.Application.objects.create(
            name='test app',
            user=dot_app_user,
            client_type='confidential',
            authorization_grant_type='authorization-code',
            redirect_uris='http://localhost:8079/complete/edxorg/'
        )
        self.dot_access_token = dot_models.AccessToken.objects.create(
            user=self.student,
            application=dot_app,
            expires=datetime.utcnow() + timedelta(weeks=1),
            scope='read write',
            token='16MGyP3OaQYHmpT1lK7Q6MMNAZsjwF'
        )

    def get_url(self, username, course_id):
        """
        Helper function to create the url for progress
        """
        return reverse(
            self.namespaced_url,
            kwargs={
                'course_id': course_id,
                'username': username
            }
        )

    def assert_oauth_status(self, access_token, expected_status):
        """
        Helper method for requests with OAUTH token
        """
        self.client.logout()
        auth_header = "Bearer {0}".format(access_token)
        response = self.client.get(self.get_url(self.student.username, self.course.id), HTTP_AUTHORIZATION=auth_header)
        self.assertEqual(response.status_code, expected_status)

    def test_student_permissions(self):
        """
        Test that the owner has access to own progress status
        """
        # unauthorized student - should be 401
        resp = self.client.get(self.get_url(self.student.username, self.course.id))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # authorized user, own value - should be 200
        self.client.login(username=self.student.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url(self.student.username, self.course.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, {u"username": self.student.username,
                                     u"course_id": self.course.id._to_deprecated_string(),  # pylint: disable=protected-access
                                     u"completion_value": 0.0})
        self.client.logout()

        # authorized student for different user - should be 404
        self.client.login(username=self.student.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url(self.instructor_user.username, self.course.id))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(resp.data, {u'detail': u'Not found.'})
        self.client.logout()

        # authorized student for different non exist user - should be 404
        self.client.login(username=self.student.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url('non_exist_user', self.course.id))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(resp.data, {u'detail': u'Not found.'})
        self.client.logout()

    def test_staff_permissions(self):
        """
        Test that the staff user has access to student progress status
        """
        # staff user for different exist user - should be 200
        self.client.login(username=self.staff_user.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url(self.student.username, self.course.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, {u"username": self.student.username,
                                     u"course_id": self.course.id._to_deprecated_string(),  # pylint: disable=protected-access
                                     u"completion_value": 0.0})
        self.client.logout()

    def test_instructor_permissions(self):
        """
        Test that the instructor of the course has access to student progress status
        """
        # instructor user for own value - should be 200
        self.client.login(username=self.instructor_user.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url(self.instructor_user.username, self.course.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, {u"username": self.instructor_user.username,
                                     u"course_id": self.course.id._to_deprecated_string(),  # pylint: disable=protected-access
                                     u"completion_value": 0.0})
        self.client.logout()

        # instructor user for different exist user - should be 200
        self.client.login(username=self.instructor_user.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url(self.student.username, self.course.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, {u"username": self.student.username,
                                     u"course_id": self.course.id._to_deprecated_string(),  # pylint: disable=protected-access
                                     u"completion_value": 0.0})
        self.client.logout()
        # instructor user in another course, does not have access - should be 404
        self.client.login(username=self.instructor_user.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url(self.student.username, self.second_course.id))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(resp.data, {u'detail': u'Not found.'})
        self.client.logout()

    def test_inactive_user_access(self):
        """
        Verify inactive users - those who have not verified their email addresses -
        are allowed to access the endpoint.
        """
        self.client.login(username=self.student.username, password=USER_PASSWORD)
        self.student.is_active = False
        self.student.save()
        resp = self.client.get(self.get_url(self.student.username, self.course.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_course_does_not_exist(self):
        """
        Verify that the course exists
        """
        self.client.login(username=self.student.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url(self.student.username, 'does/not/exist'))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(resp.data, {u'detail': u'Not found.'})
        self.client.logout()

    def test_dot_valid_accesstoken(self):
        """
        Verify access with a valid Django Oauth Toolkit access token.
        """
        self.assert_oauth_status(self.dot_access_token, status.HTTP_200_OK)

    def test_dot_invalid_accesstoken(self):
        """
        Verify the endpoint is inaccessible for authorization
        attempts made with an invalid OAuth access token.
        """
        self.assert_oauth_status("fooooooooooToken", status.HTTP_401_UNAUTHORIZED)

    def test_dot_expired_accesstoken(self):
        """
        Verify the endpoint is inaccessible for authorization
        attempts made with an expired OAuth access token.
        """
        # set the expiration date in the past
        self.dot_access_token.expires = datetime.utcnow() - timedelta(weeks=1)
        self.dot_access_token.save()
        self.assert_oauth_status(self.dot_access_token, status.HTTP_401_UNAUTHORIZED)


class CertificatesListViewTest(SharedModuleStoreTestCase, APITestCase):
    """
    Test for the Certificate REST APIs
    """
    CREATED_DATE = now = timezone.now()
    DOWNLOAD_URL = "http://www.example.com/certificate.pdf"

    @classmethod
    def setUpClass(cls):
        super(CertificatesListViewTest, cls).setUpClass()
        cls.course = CourseFactory.create(
            org='edx',
            number='verified',
            display_name='Verified Course'
        )

        cls.second_course = CourseFactory.create(
            org='edx2',
            number='verified2',
            display_name='Verified Course2'
        )


    def setUp(self):
        freezer = freeze_time(self.now)
        freezer.start()
        self.addCleanup(freezer.stop)

        super(CertificatesListViewTest, self).setUp()

        self.student = UserFactory(password=USER_PASSWORD)
        self.instructor = InstructorFactory(course_key=self.course.id, password=USER_PASSWORD)
        self.second_instructor = InstructorFactory(course_key=self.second_course.id, password=USER_PASSWORD)
        self.staff_user = UserFactory(password=USER_PASSWORD, is_staff=True)

        self.enrollment = CourseEnrollmentFactory.create(
            user=self.student,
            course_id=self.course.id)

        self.second_enrollment = CourseEnrollmentFactory.create(
            user=self.student,
            course_id=self.second_course.id)

        self.certificate = GeneratedCertificateFactory(
            user=self.student,
            course_id=self.course.id,
            download_url=self.DOWNLOAD_URL,
            status=CertificateStatuses.downloadable,
            created_date=self.CREATED_DATE,
            grade=0.98,
        )

        self.second_certificate = GeneratedCertificateFactory(
            user=self.student,
            course_id=self.second_course.id,
            download_url=self.DOWNLOAD_URL,
            status=CertificateStatuses.downloadable,
            created_date=self.CREATED_DATE,
            grade=0.95,
        )

        self.namespaced_url = 'navoica_api:v1:certificates:list'

        # create a configuration for django-oauth-toolkit (DOT)
        dot_app_user = UserFactory.create(password=USER_PASSWORD)
        dot_app = dot_models.Application.objects.create(
            name='test app',
            user=dot_app_user,
            client_type='confidential',
            authorization_grant_type='authorization-code',
            redirect_uris='http://localhost:8079/complete/edxorg/'
        )
        self.dot_access_token = dot_models.AccessToken.objects.create(
            user=self.staff_user,
            application=dot_app,
            expires=datetime.utcnow() + timedelta(weeks=1),
            scope='read write',
            token='16MGyP3OaQYHmpT1lK7Q6MMNAZsjwF'
        )

    def get_url(self, course_id):
        """
        Helper function to create the url for certificatess
        """
        return reverse(
            self.namespaced_url,
            kwargs={
                'course_id': course_id,
            }
        )

    def assert_oauth_status(self, access_token, expected_status):
        """
        Helper method for requests with OAUTH token
        """
        self.client.logout()
        auth_header = "Bearer {0}".format(access_token)
        response = self.client.get(self.get_url(self.course.id), HTTP_AUTHORIZATION=auth_header)
        self.assertEqual(response.status_code, expected_status)

    def test_student_permissions(self):
        """
        Test that the owner has not access to certificates end point
        """
        # unauthorized student - should be 401
        resp = self.client.get(self.get_url(self.course.id))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # authorized student user, don't have access to endpoint - should be 403
        self.client.login(username=self.student.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url(self.course.id))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.client.logout()



    def test_staff_permissions(self):
        """
        Test that the staff user has access to scertificates end point
        """
        # staff user for course - should be 200
        self.client.login(username=self.staff_user.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url(self.course.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK) # TODO: compare response
        self.assertEqual(resp.data['results'][0], OrderedDict([('profile_name', self.student.profile.name),
                                                            ('username', self.student.username),
                                                            ('email', self.student.email),
                                                            ('created_date', unicode(self.CREATED_DATE.strftime(
                                                            '%Y-%m-%dT%H:%M:%S.%fZ'))),
                                                            ('grade', u'0.98')]))
        self.client.logout()

        # staff user for second_course - should be 200
        self.client.login(username=self.staff_user.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url(self.second_course.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK) # TODO: compare response
        self.assertEqual(resp.data['results'][0], OrderedDict([('profile_name', self.student.profile.name),
                                                            ('username', self.student.username),
                                                            ('email', self.student.email),
                                                            ('created_date', unicode(self.CREATED_DATE.strftime(
                                                            '%Y-%m-%dT%H:%M:%S.%fZ'))),
                                                            ('grade', u'0.95')]))

        self.client.logout()

    def test_instructor_permissions(self):
        """
        Test that the instructor of the course has access to certificates end point
        """
        # instructor user for course - should be 200
        self.client.login(username=self.instructor.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url(self.course.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['results'][0], OrderedDict([('profile_name', self.student.profile.name),
                                                            ('username', self.student.username),
                                                            ('email', self.student.email),
                                                            ('created_date', unicode(self.CREATED_DATE.strftime(
                                                            '%Y-%m-%dT%H:%M:%S.%fZ'))),
                                                            ('grade', u'0.98')]))
        self.client.logout()

        # another instructor user (for different course) in another course - should be 403
        self.client.login(username=self.instructor.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url(self.second_course.id))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        self.client.logout()
        # instructor user in his course - should be 403
        self.client.login(username=self.second_instructor.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url(self.second_course.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['results'][0], OrderedDict([('profile_name', self.student.profile.name),
                                                            ('username', self.student.username),
                                                            ('email', self.student.email),
                                                            ('created_date', unicode(self.CREATED_DATE.strftime(
                                                            '%Y-%m-%dT%H:%M:%S.%fZ'))),
                                                            ('grade', u'0.95')]))
        self.client.logout()

        # another instructor user (for different course) in another course - should be 403
        self.client.login(username=self.second_instructor.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url(self.course.id))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.client.logout()

    def test_course_does_not_exist(self):
        """
        Verify that the course exists
        """
        self.client.login(username=self.instructor.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url('does/not/exist'))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(resp.data, {u'detail': u'Not found.'})
        self.client.logout()

    def test_dot_valid_accesstoken(self):
        """
        Verify access with a valid Django Oauth Toolkit access token.
        """
        self.assert_oauth_status(self.dot_access_token, status.HTTP_200_OK)

    def test_dot_invalid_accesstoken(self):
        """
        Verify the endpoint is inaccessible for authorization
        attempts made with an invalid OAuth access token.
        """
        self.assert_oauth_status("fooooooooooToken", status.HTTP_401_UNAUTHORIZED)

    def test_dot_expired_accesstoken(self):
        """
        Verify the endpoint is inaccessible for authorization
        attempts made with an expired OAuth access token.
        """
        # set the expiration date in the past
        self.dot_access_token.expires = datetime.utcnow() - timedelta(weeks=1)
        self.dot_access_token.save()
        self.assert_oauth_status(self.dot_access_token, status.HTTP_401_UNAUTHORIZED)
