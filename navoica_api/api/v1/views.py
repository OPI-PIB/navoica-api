"""
API v1 views.
"""

from __future__ import absolute_import, unicode_literals

from completion.models import BlockCompletion
from django.contrib.auth.models import User
from opaque_keys.edx.keys import CourseKey
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from courseware import courses
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from django.core.exceptions import ObjectDoesNotExist
from edx_rest_framework_extensions.authentication import JwtAuthentication
from lms.djangoapps.course_api.blocks.api import get_blocks
from openedx.core.lib.api import permissions, authentication
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError
from rest_framework.authentication import SessionAuthentication
from rest_framework_oauth.authentication import OAuth2Authentication
from navoica_api.api.permissions import IsCourseStaffInstructorOrUserInUrlOrStaff
from lms.djangoapps.ccx.api.v0.views import get_valid_course
class CourseProgressView(GenericAPIView):
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
    authentication_classes = (authentication.OAuth2AuthenticationAllowInactiveUser, authentication.SessionAuthenticationAllowInactiveUser, JwtAuthentication,)
    permission_classes = (IsAuthenticated, IsCourseStaffInstructorOrUserInUrlOrStaff)

    def get_object(self, course_id, is_ccx=False):  # pylint: disable=arguments-differ
        """
        Override the default get_object to allow a custom getter for the CCX
        """
        course_object = courses.get_course_by_id(course_id)
        self.check_object_permissions(self.request, course_object)
        return course_object

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
        ccx_course_object= self.get_object(course_id)
        self.completion = 0
        self.total_children = 0

        def get_completion(course_completions, all_blocks, block_id):
            """
            Recursively get the aggregate completion for a subsection,
            given the subsection block and a list of all blocks.
            Parameters:
                course_completions: a dictionary of completion values by block IDs
                all_blocks: a dictionary of the block structure for a subsection
                block_id: an ID of a block for which to get completion
            """
            block = all_blocks.get(block_id)
            child_ids = block.get('children', [])
            if not child_ids:
                self.total_children += 1
                self.completion += course_completions.get(block.serializer.instance, 0)

            for child_id in child_ids:
                get_completion(course_completions, all_blocks, child_id)

            return round(self.completion/self.total_children, 3)

        course_usage_key = modulestore().make_course_usage_key(CourseKey.from_string(course_id))

        try:
            user_id = User.objects.get(username=username).id
        except User.DoesNotExist:
            return Response(
                status=404,
                data={'error_code': u'Not found.'}
            )

        block_types_filter = [
            'course',
            'chapter',
            'sequential',
            'vertical',
            'html',
            'problem',
            'video',
            'drag-and-drop-v2',
            'poll',
            'videojs',
            'embedded_answers',
            'inline-dropdown',
        ]
        try:
            blocks = get_blocks(request,course_usage_key,nav_depth=3,requested_fields=[
                'children',
            ],
            block_types_filter=block_types_filter
            )
        except ItemNotFoundError:
            return Response(
                status=404,
                data={'error_code': u'Not found.'}
            )


        course_completions = BlockCompletion.get_course_completions(user_id, CourseKey.from_string(course_id))
        aggregated_completion = get_completion(course_completions, blocks['blocks'], blocks['root'])

        response_dict = {"username": username,
                         "course_id": course_id,
                         "completion_value": aggregated_completion}

        return Response(response_dict, status=status.HTTP_200_OK)
