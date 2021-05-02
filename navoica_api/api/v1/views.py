"""
API v1 views.
"""

from __future__ import absolute_import, unicode_literals

from completion.models import BlockCompletion
from courseware import courses  # pylint: disable=import-error
from django.contrib.auth.models import User
from edx_rest_framework_extensions.authentication import JwtAuthentication
from lms.djangoapps.course_api.blocks.api import get_blocks
from navoica_api.api.v1.serializers.user import UserSerializer
from opaque_keys.edx.keys import CourseKey
from openedx.core.lib.api import authentication
from openedx.core.lib.api.authentication import (
    SessionAuthenticationAllowInactiveUser,
    OAuth2AuthenticationAllowInactiveUser,
)
from rest_framework import permissions
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

from navoica_api.api.permissions import \
    IsCourseStaffInstructorOrUserInUrlOrStaff


class CourseProgressApiView(GenericAPIView):
    """
        **Use Case**

            * Get detail about course completion.

        **Example Request**

            GET /api/navoica/v1/progress/{username}/courses/{course_id}

        **GET Parameters**

            A GET request must include the following parameters.

            * username: A string representation of an user's username.
            * course_id: A string representation of a Course ID.

        **GET Response Values**

            If the request for information about the Progress is successful, an HTTP 200 "OK" response
            is returned.

            The HTTP 200 response has the following values.

            * username: A string representation of an user's username passed in the request.

            * course_id: A string representation of a Course ID.

            * completion_value: A float between 0 and 1, when 1 meaning 100% completion



        **Example GET Response**
            {
                "username": "bob",
                "course_id": "edX/DemoX/Demo_Course",
                "completion_value": 0.800
            }
    """

    def __init__(self):
        super(CourseProgressApiView, self).__init__()
        self.units_progress_list = []

    authentication_classes = (authentication.OAuth2AuthenticationAllowInactiveUser,
                              authentication.SessionAuthenticationAllowInactiveUser,
                              JwtAuthentication,)
    permission_classes = (IsAuthenticated, IsCourseStaffInstructorOrUserInUrlOrStaff)

    def get(self, request, username, course_id):
        """
        Gets a progress information.

        Args:
            request (Request): Django request object.
            username (string): URI element specifying the user's username.
            course_id (string): URI element specifying the course location.

        Return:
            A JSON serialized representation of the certificate.
        """

        def aggregate_progress(course_completions, all_blocks, block_id):
            """
            Recursively get the progress for a units (vertical),
            given list of all blocks.
            Parameters:
                course_completions: a dictionary of completion values by block IDs
                all_blocks: a dictionary of the block structure for a subsection
                block_id: an ID of a block for which to get completion
            """
            block = all_blocks.get(block_id)
            child_ids = block.get('children', [])
            if block.get('type', None) == 'vertical':
                self.units_progress_list.append([block_id, 0, 0])

            if not child_ids and (block.get('type', None) in block_xblocks_types_filter):
                self.units_progress_list[-1][1] += 1
                self.units_progress_list[-1][2] += course_completions.get(block.serializer.instance, 0)

            for child_id in child_ids:
                aggregate_progress(course_completions, all_blocks, child_id)

        def calculate_progress():
            """
            Calculate course progress from units progress
            """
            number_of_units = len(self.units_progress_list)
            if number_of_units == 0:
                return float(0.0)
            else:
                cumulative_sum = 0
                for unit_progress in self.units_progress_list:
                    if unit_progress[1] == 0:
                        number_of_units -= 1
                    else:
                        cumulative_sum += unit_progress[2] / unit_progress[1]
                return round(cumulative_sum / number_of_units, 3)

        course_object_id = CourseKey.from_string(course_id)
        self.check_object_permissions(self.request, courses.get_course_by_id(course_object_id))
        course_usage_key = modulestore().make_course_usage_key(course_object_id)

        try:
            user_id = User.objects.get(username=username).id
        except User.DoesNotExist:
            return Response(
                status=404,
                data={'error_code': u'Not found.'}
            )

        block_navigation_types_filter = [
            'course',
            'chapter',
            'sequential',
            'vertical',
        ]

        block_xblocks_types_filter = [
            'html',
            'problem',
            'video',
            'drag-and-drop-v2',
            'poll',
            'videojs',
            'embedded_answers',
            'inline-dropdown',
            'openassessment',
            'audioplayer',
        ]

        block_types_filter = block_navigation_types_filter + block_xblocks_types_filter

        try:
            blocks = get_blocks(request, course_usage_key, nav_depth=3, requested_fields=[
                'children', 'type',
            ],
                                block_types_filter=block_types_filter
                                )
        except ItemNotFoundError:
            return Response(
                status=404,
                data={'error_code': u'Not found.'}
            )

        course_completions = BlockCompletion.get_course_completions(user_id, course_object_id)
        aggregate_progress(course_completions, blocks['blocks'], blocks['root'])
        calculated_progress = calculate_progress()
        response_dict = {"username": username,
                         "course_id": course_id,
                         "completion_value": calculated_progress}

        return Response(response_dict, status=status.HTTP_200_OK)


class UserApiView(APIView):
    """
            **Use Cases**

                Get user's account information.

            **Example Requests**

                GET /api/user/v1/me

            **Response Values for GET requests to the /me endpoint**
                If the user is not logged in, an HTTP 401 "Not Authorized" response
                is returned.

                Otherwise, an HTTP 200 "OK" response is returned. The response
                contains the following value:

                "id"
                "username"
                "email"
                "date_joined"
                "is_active"
                "name"
                "gender"
                "year_of_birth"
                "level_of_education"

        """

    authentication_classes = (
        OAuth2AuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser, JwtAuthentication
    )
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        return Response(UserSerializer(request.user).data)
