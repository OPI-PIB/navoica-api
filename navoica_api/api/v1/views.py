"""
API v1 views.
"""

from __future__ import absolute_import, unicode_literals

import csv
import logging
from datetime import datetime

from completion.models import BlockCompletion
from django.contrib.auth.models import User
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from edx_rest_framework_extensions.authentication import JwtAuthentication
from edx_rest_framework_extensions.paginators import DefaultPagination
from navoica_api.api.permissions import (IsCourseStaffInstructorOrStaff,
                                         IsCourseStaffInstructorOrUserInUrlOrStaff)
from navoica_api.api.v1.serializers import GeneratedCertificateSerializer
from opaque_keys.edx.keys import CourseKey
from rest_framework import status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.response import Response

from lms.djangoapps.courseware import courses
from lms.djangoapps.certificates.models import GeneratedCertificate
from lms.djangoapps.course_api.blocks.api import get_blocks
from openedx.core.lib.api import authentication
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

log = logging.getLogger(__name__)


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
                        cumulative_sum += unit_progress[2]/unit_progress[1]
                return round(cumulative_sum/number_of_units, 3)

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


class CertificatesListView(ListAPIView):
    """
        **Use Case**

            * Get the list of a generated certificate for a specific course_id

        **Example Request**

            GET /api/certificates/v0/certificates/courses/{course_id}

        **GET Parameters**

            A GET request must include the following parameters.

            * course_id: A string representation of a Course ID.

        ** Query parameters**

            * attachment: return ['Content-Disposition'] = 'attachment; filename={} response

            * filters/search/ordering attributes: ('user__profile__name', 'user__username',
            'user__email', 'created_date',)

        **Response Values**

            If the request for information about the user is successful, an HTTP 200 "OK" response
            is returned.

            The HTTP 200 response has the following values:

            * count: The number of mappings for the backend.

            * next: The URI to the next page of the mappings.

            * previous: The URI to the previous page of the mappings.

            * num_pages: The number of pages listing the mappings.

            * results:  A list of mappings returned. Each collection in the list
            contains these fields.

                * profile_name: student lastname and surname

                * username: student username

                * email: student e-mail

                * created_date: date of created certificate

                * grade: grade of certificate
    """

    authentication_classes = (authentication.OAuth2AuthenticationAllowInactiveUser,
                              authentication.SessionAuthenticationAllowInactiveUser,
                              JwtAuthentication,)
    permission_classes = (IsAuthenticated, IsCourseStaffInstructorOrStaff)
    pagination_class = DefaultPagination
    serializer_class = GeneratedCertificateSerializer
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    filter_backends = (OrderingFilter, DjangoFilterBackend, SearchFilter)
    filterset_fields = search_fields = ordering_fields = ('user__profile__name', 'user__username',
        'user__email', 'created_date',)

    def __init__(self):
        super(CertificatesListView, self).__init__()
        self.course_id = None

    def get_queryset(self):
        try:
            certs = GeneratedCertificate.eligible_certificates.filter(
                course_id=self.course_id
            )
            return certs
        except GeneratedCertificate.DoesNotExist:
            return None

    def check_course_permissions_and_return_queryset(self):
        self.course_id = CourseKey.from_string(self.kwargs.get('course_id', None))
        self.check_object_permissions(self.request, courses.get_course_by_id(self.course_id))
        return self.filter_queryset(self.get_queryset())

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        queryset = self.check_course_permissions_and_return_queryset()

        if 'attachment' in self.request.query_params:
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename={}'.format("report_{}.csv"
            .format(datetime.now().strftime("%Y_%m_%d-%I_%M_%S")))
            writer = csv.writer(response)
            certs = self.get_serializer(queryset, many=True).data
            if certs:
                writer.writerow(certs[0].keys())
                for cert in certs:
                    writer.writerow(cert.values())
            else:
                writer.writerow(['Empty list', ])
            return response
        else:
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
