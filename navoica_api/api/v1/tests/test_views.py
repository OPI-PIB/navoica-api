"""
Tests for the Certificate REST APIs.
"""
from collections import OrderedDict
from datetime import datetime, timedelta
from django.utils.http import urlencode
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from lms.djangoapps.certificates.models import CertificateStatuses
from lms.djangoapps.certificates.tests.factories import \
    GeneratedCertificateFactory
from lms.djangoapps.courseware.tests.factories import (InstructorFactory,
                                                       UserFactory)
from oauth2_provider import models as dot_models
from openedx.features.course_experience.views.course_updates import \
    STATUS_VISIBLE
from rest_framework import status
from rest_framework.test import APITestCase
from six import text_type
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
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(resp.data, {u'detail': u'You do not have permission to perform this action.'})
        self.client.logout()

        # authorized student for different non exist user - should be 404
        self.client.login(username=self.student.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url('non_exist_user', self.course.id))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(resp.data, {u'detail': u'You do not have permission to perform this action.'})
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
        # instructor user in another course, does not have access - should be 403
        self.client.login(username=self.instructor_user.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url(self.student.username, self.second_course.id))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(resp.data, {u'detail': 'You do not have permission to perform this action.'})
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
        self.assertEqual(resp.data, {u'detail': u'You do not have permission to perform this action.'})
        self.client.logout()

    def test_staff_permissions(self):
        """
        Test that the staff user has access to scertificates end point
        """
        # staff user for course - should be 200
        self.client.login(username=self.staff_user.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url(self.course.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['results'][0], OrderedDict([('profile_name', self.student.profile.name),
                                                               ('username', self.student.username),
                                                               ('email', self.student.email),
                                                               ('created_date', text_type(self.CREATED_DATE.strftime(
                                                                   '%Y-%m-%dT%H:%M:%S.%fZ'))),
                                                               ('grade', u'0.98')]))
        self.client.logout()

        # staff user for second_course - should be 200
        self.client.login(username=self.staff_user.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url(self.second_course.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['results'][0], OrderedDict([('profile_name', self.student.profile.name),
                                                               ('username', self.student.username),
                                                               ('email', self.student.email),
                                                               ('created_date', text_type(self.CREATED_DATE.strftime(
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
                                                               ('created_date', text_type(self.CREATED_DATE.strftime(
                                                                   '%Y-%m-%dT%H:%M:%S.%fZ'))),
                                                               ('grade', u'0.98')]))
        self.client.logout()

        # another instructor user (for different course) in another course - should be 403
        self.client.login(username=self.instructor.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url(self.second_course.id))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(resp.data, {u'detail': u'You do not have permission to perform this action.'})

        self.client.logout()
        # instructor user in his course - should be 403
        self.client.login(username=self.second_instructor.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url(self.second_course.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['results'][0], OrderedDict([('profile_name', self.student.profile.name),
                                                               ('username', self.student.username),
                                                               ('email', self.student.email),
                                                               ('created_date', text_type(self.CREATED_DATE.strftime(
                                                                   '%Y-%m-%dT%H:%M:%S.%fZ'))),
                                                               ('grade', u'0.95')]))
        self.client.logout()

        # another instructor user (for different course) in another course - should be 403
        self.client.login(username=self.second_instructor.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url(self.course.id))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(resp.data, {u'detail': u'You do not have permission to perform this action.'})
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


class UpdatesListViewTest(SharedModuleStoreTestCase, APITestCase):
    """
    Test for the Updates REST APIs
    """

    CREATED_DATE = now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    WELCOME_MESSAGE_DATE = now - timedelta(days=15)
    FIRST_UPDATE_MESSAGE_DATE = now - timedelta(days=15)
    SECOND_UPDATE_MESSAGE_DATE = now - timedelta(days=7)
    THIRD_UPDATE_MESSAGE_DATE = now

    WELCOME_MESSAGE = u"<ol><li><h2>Date</h2>Welcome message!</li></ol>"
    UPDATE_MESSAGE = u"<ol><li><h2>Date</h2>Hello World!</li></ol>"

    @classmethod
    def setUpClass(cls):
        super(UpdatesListViewTest, cls).setUpClass()

        cls.course = CourseFactory.create(display_name='test course', run="Testing_course")
        cls.course_without_updates = CourseFactory.create()
        cls.course_key = cls.course.id
        cls.course_without_updates_key = cls.course_without_updates.id

        cls.student = UserFactory(password=USER_PASSWORD)
        cls.not_enrolled_student = UserFactory(password=USER_PASSWORD)
        cls.staff_user = UserFactory(password=USER_PASSWORD, is_staff=True)

        cls.initialize_course(cls.course)

    @classmethod
    def initialize_course(cls, course):
        """
        Sets up test course structure.
        """
        course.start = datetime.now()
        course.self_paced = True
        cls.store.update_item(course, cls.staff_user.id)

        update_key = course.id.make_usage_key('course_info', 'updates')
        course_updates = cls.store.create_item(
            cls.staff_user.id,
            update_key.course_key,
            update_key.block_type,
            block_id=update_key.block_id,
            fields=dict(data=u"<ol><li><h2>Date</h2>Hello world!</li></ol>"),
        )

        course_updates.items.append({
            "id": 1,
            "date": cls.WELCOME_MESSAGE_DATE.strftime("%d/%m/%Y"),
            "content": cls.WELCOME_MESSAGE,
            "status": STATUS_VISIBLE
        })

        course_updates.items.append({
            "id": 2,
            "date": cls.FIRST_UPDATE_MESSAGE_DATE.strftime("%d/%m/%Y"),
            "content": cls.UPDATE_MESSAGE,
            "status": STATUS_VISIBLE
        })

        course_updates.items.append({
            "id": 3,
            "date": cls.SECOND_UPDATE_MESSAGE_DATE.strftime("%d/%m/%Y"),
            "content": cls.UPDATE_MESSAGE,
            "status": STATUS_VISIBLE
        })

        course_updates.items.append({
            "id": 4,
            "date": cls.THIRD_UPDATE_MESSAGE_DATE.strftime("%d/%m/%Y"),
            "content": cls.UPDATE_MESSAGE,
            "status": STATUS_VISIBLE
        })

        cls.store.update_item(course_updates, cls.staff_user.id)

        section = ItemFactory.create(
            parent_location=course.location,
            category="chapter",
        )
        ItemFactory.create(
            parent_location=section.location,
            category="sequential",
        )

    def setUp(self):
        freezer = freeze_time(self.now)
        freezer.start()
        self.addCleanup(freezer.stop)

        super(UpdatesListViewTest, self).setUp()

        self.enrollment = CourseEnrollmentFactory.create(
            user=self.student,
            course_id=self.course.id)

        self.second_enrollment = CourseEnrollmentFactory.create(
            user=self.student,
            course_id=self.course_without_updates.id)

        self.namespaced_url = 'navoica_api:v1:updates:list'

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
        Helper function to create the url for certificatess
        """
        return reverse(
            self.namespaced_url,
            kwargs={
                'course_id': course_id,
                'username': username
            }
        )

    def get_dismiss_url(self, course_id):
        return reverse(
            'openedx.course_experience.dismiss_welcome_message', kwargs={'course_id': text_type(course_id)}
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
        Test that the owner has not access to certificates end point
        """
        # unauthorized student - should be 401
        resp = self.client.get(self.get_url(self.student.username, self.course.id))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # not enrolled student - should be 404
        self.client.login(username=self.not_enrolled_student.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url(self.not_enrolled_student.username, self.course.id))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(resp.data, {u'detail': u'You do not have permission to perform this action.'})
        self.client.logout()

        # course without updates - should be 404
        self.client.login(username=self.student.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url(self.student.username, self.course_without_updates.id))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(resp.data, {u'detail': u'Not found.'})
        self.client.logout()

        # if student is enrolled to course - should be 200 and returned welcome_messages
        self.client.login(username=self.student.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url(self.student.username, self.course.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertDictEqual(resp.data, {u"username": self.student.username,
                                         u"course_id": self.course.id._to_deprecated_string(),  # pylint: disable=protected-access
                                         u"dismiss_url": self.get_dismiss_url(self.course.id),
                                         u"updates": {
                                             u"content": self.WELCOME_MESSAGE,
                                             u"date": self.WELCOME_MESSAGE_DATE.isoformat(),
                                             u"id": 1,
                                             u"status": STATUS_VISIBLE
                                         }
                                         })

        self.client.logout()

        # check dismiss_url - should be 200
        self.client.login(username=self.student.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_dismiss_url(self.course.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.client.logout()

        # after dismiss_url should return ordered by date updates messages from last 2 weeks - should be 200
        self.client.login(username=self.student.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url(self.student.username, self.course.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertDictEqual(resp.data, {u"username": self.student.username,
                                         u"course_id": self.course.id._to_deprecated_string(),  # pylint: disable=protected-access
                                         u"updates": [
                                             {
                                                 u"content": self.UPDATE_MESSAGE,
                                                 u"date": self.THIRD_UPDATE_MESSAGE_DATE.isoformat(),
                                                 u"id": 4,
                                                 u"status": STATUS_VISIBLE
                                             },
                                             {
                                                 u"content": self.UPDATE_MESSAGE,
                                                 u"date": self.SECOND_UPDATE_MESSAGE_DATE.isoformat(),
                                                 u"id": 3,
                                                 u"status": STATUS_VISIBLE
                                             }]
                                         })

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


class CourseOpinionsViewTest(SharedModuleStoreTestCase, APITestCase):
    """
    Test for the Updates REST APIs
    """

    CREATED_DATE = now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    @classmethod
    def setUpClass(cls):
        super(CourseOpinionsViewTest, cls).setUpClass()

        cls.course = CourseFactory.create(display_name='first test course', run="First_edition")
        cls.course_key = text_type(cls.course.id)
        cls.second_course = CourseFactory.create(display_name='second test course', run="Second_edition")
        cls.second_course_key = text_type(cls.second_course.id)

        cls.student = UserFactory(password=USER_PASSWORD)
        cls.second_student = UserFactory(password=USER_PASSWORD)
        cls.not_enrolled_student = UserFactory(password=USER_PASSWORD)
        cls.staff_user = UserFactory(password=USER_PASSWORD, is_staff=True)

    def setUp(self):
        freezer = freeze_time(self.now)
        freezer.start()
        self.addCleanup(freezer.stop)

        super(CourseOpinionsViewTest, self).setUp()
        self.enrollment = CourseEnrollmentFactory.create(
            user=self.student,
            course_id=self.course.id)

        self.second_enrollment = CourseEnrollmentFactory.create(
            user=self.second_student,
            course_id=self.course.id)

        self.enrollment_second_student_to_second_course = CourseEnrollmentFactory.create(
            user=self.second_student,
            course_id=self.second_course.id)

        self.namespaced_url = 'navoica_api:v1:courseopinion'

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

    def get_test_data(self, course_id):
        return OrderedDict([("course_id", course_id), ("grade", "5.0"), ("content", "Bardzo fajny kurs, polecam.")])

    def get_url(self, action, kwargs=None, query_kwargs=None):
        """
        Helper function to create the url for certificatess
        """
        if action in ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']:
            if action in ['list', 'create']:
                url_name = 'list'
            else:
                url_name = 'detail'
            url = reverse(self.namespaced_url + '-' + url_name, kwargs=kwargs)

            if query_kwargs:
                return f'{url}?{urlencode(query_kwargs)}'
            return url
        return None

    def assert_oauth_status(self, access_token, expected_status):
        """
        Helper method for requests with OAUTH token
        """
        self.client.logout()
        auth_header = "Bearer {0}".format(access_token)
        response = self.client.get(self.get_url(action='list'), HTTP_AUTHORIZATION=auth_header)
        self.assertEqual(response.status_code, expected_status)

    def test_permission_unauthorized_user_can_only_get_list(self):
        """
        Test that the owner has not access to certificates end point
        """
        # unauthorized student - should be 200
        resp = self.client.get(self.get_url(action='list'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # unauthorized student - should be 401
        resp = self.client.post(self.get_url(action='create'), data=self.get_test_data(self.course_key))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # unauthorized student - should be 401
        resp = self.client.get(self.get_url(action='retrieve', kwargs={'id': 'test_id'}))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    # def test_permission_unenrolled_user_cant_create_and_course_must_exist(self):

    #     # not enrolled student - should be 400
    #     self.client.login(username=self.not_enrolled_student.username, password=USER_PASSWORD)
    #     resp = self.client.post(self.get_url(action='create'), data=self.get_test_data(self.course_key))
    #     self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
    #     self.client.logout()

    #     # not enrolled student - should be 400
    #     self.client.login(username=self.not_enrolled_student.username, password=USER_PASSWORD)
    #     resp = self.client.post(self.get_url(action='create'), data=self.get_test_data('not_exist_course'))
    #     self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
    #     self.client.logout()

    def test_permission_only_one_opinion_for_each_course(self):
        # not enrolled student - should be 400
        self.client.login(username=self.student.username, password=USER_PASSWORD)
        resp = self.client.post(self.get_url(action='create'), data=self.get_test_data(self.course_key))
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.client.logout()

        self.client.login(username=self.student.username, password=USER_PASSWORD)
        resp = self.client.post(self.get_url(action='create'), data=self.get_test_data(self.course_key))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST) # TO DO: zmienić na 403 forbidden ?
        self.client.logout()

    def test_permission_can_modify_only_own_opinion(self):
        # not enrolled student - should be 400
        self.client.login(username=self.student.username, password=USER_PASSWORD)
        resp = self.client.post(self.get_url(action='create'), data=self.get_test_data(self.course_key))
        opinion_id = resp.data.get('id', None)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        resp = self.client.patch(self.get_url(action='partial_update', kwargs={'id': opinion_id}), data={'grade': 4})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.client.logout()

        self.client.login(username=self.second_student.username, password=USER_PASSWORD)
        resp = self.client.patch(self.get_url(action='partial_update', kwargs={'id': opinion_id}), data={'grade': 4})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.client.logout()

    def test_permission_student_cant_modify_reviewed_field_but_staff_can(self):

        self.client.login(username=self.student.username, password=USER_PASSWORD)
        resp = self.client.post(self.get_url(action='create'), data=self.get_test_data(self.course_key))
        opinion_id = resp.data.get('id', None)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        resp = self.client.patch(self.get_url(action='partial_update', kwargs={'id': opinion_id}), data={'reviewed': True})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data.get('reviewed'), False)
        self.client.logout()

        self.client.login(username=self.staff_user.username, password=USER_PASSWORD)
        resp = self.client.patch(self.get_url(action='partial_update', kwargs={'id': opinion_id}), data={'reviewed': True})
        self.assertEqual(resp.data.get('reviewed'), True)
        self.client.logout()

    def test_filtering_by_course_id_and_username(self):
        self.client.login(username=self.student.username, password=USER_PASSWORD)
        resp = self.client.post(self.get_url(action='create'), data=self.get_test_data(self.course_key))

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.client.logout()

        self.client.login(username=self.second_student.username, password=USER_PASSWORD)
        resp = self.client.post(self.get_url(action='create'), data=self.get_test_data(self.second_course_key))
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.client.logout()
        resp = self.client.get(self.get_url(action='list', query_kwargs={'course_id': self.course_key, 'username': self.student.username}))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(resp.data.get('results')[0].items(), self.get_test_data(self.course_key).items())


# to do | problem z tworzeniem kursu o innej edycji
    # def test_return_opinions_for_all_runs_for_specified_course(self):

    #     self.client.login(username=self.student.username, password=USER_PASSWORD)
    #     resp = self.client.post(self.get_url(action='create'), data=self.get_test_data(self.course_key))

    #     self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
    #     self.client.logout()

    #     self.client.login(username=self.second_student.username, password=USER_PASSWORD)
    #     resp = self.client.post(self.get_url(action='create'), data=self.get_test_data(self.second_course_key))
    #     self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
    #     self.client.logout()

    #     resp = self.client.get(self.get_url(action='list'))
    #     self.assertEqual(resp.status_code, status.HTTP_200_OK)
    #     self.assertEqual(len(resp.data.get('results')), 2)
        # sprawdź zawartość

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
