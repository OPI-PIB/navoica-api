"""
Permissions classes for the API.
"""
from __future__ import absolute_import, unicode_literals

from common.djangoapps.student.roles import (  # pylint: disable=import-error
    CourseInstructorRole, CourseStaffRole)
from openedx.core.lib.api.permissions import IsUserInUrlOrStaff
from rest_framework import permissions


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

        # because IsUserinUrlorStaff return permission class ...
        return super(IsCourseStaffInstructorOrUserInUrlOrStaff, self).has_permission(request, view)

    def has_permission(self, request, view):
        return True


class IsCourseStaffInstructorOrStaff(permissions.BasePermission):
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
                 and hasattr(obj, 'coach') and obj.coach == request.user)) or request.user.is_staff:
            return True


class IsStaffOrOwner(permissions.BasePermission):
    """
    Permission that allows access to admin users or the owner of an object.
    The owner is considered the User object represented by obj.user.
    """

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.user == request.user
