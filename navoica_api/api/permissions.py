"""
Permissions classes for the API.
"""
from __future__ import absolute_import, unicode_literals

from rest_framework import permissions

from openedx.core.lib.api.permissions import IsUserInUrlOrStaff
from student.roles import CourseInstructorRole, CourseStaffRole # pylint: disable=import-error


class IsCourseStaffInstructorOrUserInUrlOrStaff(IsUserInUrlOrStaff):
    """
    Permission that checks to see if the request user matches the user in the URL.
    """
    def has_object_permission(self, request, view, obj):
        if (hasattr(request, 'user') and
                # either the user is a staff or instructor of the master course
                (hasattr(obj, 'id') and
                 (CourseInstructorRole(obj.id).has_user(request.user) or
                  CourseStaffRole(obj.id).has_user(request.user))) or
                # or it is a safe method and the user is a coach on the course object
                (request.method in permissions.SAFE_METHODS
                 and hasattr(obj, 'coach') and obj.coach == request.user)):
            return True

        return super(IsCourseStaffInstructorOrUserInUrlOrStaff, self).has_permission(request, view)

    def has_permission(self, request, view):
        return True
