# """ Tests for API permissions classes. """

# import ddt
# from django.contrib.auth.models import AnonymousUser
# from django.http import Http404
# from django.test import TestCase, RequestFactory
# from nose.plugins.attrib import attr
# from rest_framework.generics import GenericAPIView

# from student.roles import CourseStaffRole, CourseInstructorRole
# from openedx.core.lib.api.permissions import (
#     IsStaffOrOwner,
#     IsCourseStaffInstructor,
#     IsMasterCourseStaffInstructor,
# )
# from navoica_api.api.permissions import IsCourseStaffInstructorOrUserInUrlOrStaff

# from student.tests.factories import UserFactory
# from opaque_keys.edx.keys import CourseKey

# class TestObject(object):
#     """ Fake class for object permission tests. """
#     def __init__(self, user=None, course_id=None):
#         self.user = user
#         self.course_id = course_id


# class TestCcxObject(TestObject):
#     """ Fake class for object permission for CCX Courses """
#     def __init__(self, user=None, course_id=None):
#         super(TestCcxObject, self).__init__(user, course_id)
#         self.coach = user

# @attr(shard=2)
# class IsCourseStaffInstructorOrUserInUrlOrStaffTests(TestCase):
#     """ Test for IsCourseStaffInstructor permission class. """

#     def setUp(self):
#         super(IsCourseStaffInstructorOrUserInUrlOrStaffTests, self).setUp()
#         self.permission = IsCourseStaffInstructorOrUserInUrlOrStaff()
#         self.coach = UserFactory()
#         self.user = UserFactory()
#         self.request = RequestFactory().get('/')
#         self.request.user = self.user
#         self.course_key = CourseKey.from_string('edx/test123/run')
#         self.obj = TestCcxObject(user=self.coach, course_id=self.course_key)

#     def test_course_staff_has_access(self):
#         CourseStaffRole(course_key=self.course_key).add_users(self.user)
#         self.assertTrue(self.permission.has_object_permission(self.request, None, self.obj))

#     def test_course_instructor_has_access(self):
#         CourseInstructorRole(course_key=self.course_key).add_users(self.user)
#         self.assertTrue(self.permission.has_object_permission(self.request, None, self.obj))

#     def test_course_coach_has_access(self):
#         self.request.user = self.coach
#         self.assertTrue(self.permission.has_object_permission(self.request, None, self.obj))

#     def test_any_user_has_no_access(self):
#         self.assertFalse(self.permission.has_object_permission(self.request, None, self.obj))

#     def test_anonymous_has_no_access(self):
#         self.request.user = AnonymousUser()
#         self.assertFalse(self.permission.has_object_permission(self.request, None, self.obj))
