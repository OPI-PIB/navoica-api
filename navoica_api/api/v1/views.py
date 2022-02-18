"""
API v1 views.
"""

from __future__ import absolute_import, unicode_literals

import csv
import logging
from datetime import datetime, timedelta

from completion.models import BlockCompletion
from dateutil.parser import parse
from django.conf import settings
from django.contrib.auth.models import User
from django.db import IntegrityError  # Import IntegrityError
from django.http import HttpResponse
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from edx_rest_framework_extensions.auth.jwt.authentication import \
    JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import \
    SessionAuthenticationAllowInactiveUser
from edx_rest_framework_extensions.paginators import DefaultPagination
from edx_rest_framework_extensions.permissions import IsUserInUrl
from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.certificates.models import GeneratedCertificate
from lms.djangoapps.course_api.blocks.api import get_blocks
from lms.djangoapps.courseware import courses  # pylint: disable=import-error
from lms.djangoapps.courseware.courses import get_courses
from navoica_api.api.permissions import (
    IsCourseStaffInstructorOrStaff, IsCourseStaffInstructorOrUserInUrlOrStaff,
    IsStaffOrOwner)
from navoica_api.api.v1.serializers.certificate import \
    GeneratedCertificateSerializer
from navoica_api.api.v1.serializers.career import \
    CareerSerializer
from navoica_api.api.v1.serializers.opinion import (
    AdminCourseOpinionSerializer, CourseOpinionSerializer,
    CreateCourseOpinionSerializer)
from navoica_api.api.v1.serializers.user import UserSerializer
from navoica_api.models import CareerModel, CourseRunOpinionModel
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.user_api.course_tag.api import get_course_tag
from openedx.core.lib.api.authentication import \
    OAuth2AuthenticationAllowInactiveUser
from openedx.features.course_experience.views.course_updates import \
    get_ordered_updates
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from six import text_type
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError
from openedx.core.lib.api.view_utils import PaginatedAPIView, get_course_key, verify_course_exists
from lms.djangoapps.grades.rest_api.v1.utils import GradeViewMixin
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

    authentication_classes = (OAuth2AuthenticationAllowInactiveUser,
                              SessionAuthenticationAllowInactiveUser,
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
                data={'detail': u'Not found.'}
            )

        block_navigation_types_filter = settings.BLOCK_NAVIGATION_TYPES_FILTER

        block_xblocks_types_filter = settings.BLOCK_XBLOCKS_TYPES_FILTER

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
                data={'detail': u'Not found.'}
            )

        course_completions = BlockCompletion.get_learning_context_completions(user_id, course_object_id)
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

    authentication_classes = (OAuth2AuthenticationAllowInactiveUser,
                              SessionAuthenticationAllowInactiveUser,
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


PREFERENCE_KEY = 'view-welcome-message'


class CourseUpdatesMessagesApiView(GenericAPIView):
    """
        **Use Case**

            # * Get information about course updates

        **Example Request**

            GET /api/navoica/v1/updates/{username}/courses/{course_id}

        **GET Parameters**

            # A GET request must include the following parameters.

            # * username: A string representation of an user's username.
            # * course_id: A string representation of a Course ID.

        **GET Response Values**

            # If the request for information about the Updates is successful, an HTTP 200 "OK" response
            # is returned.

            # The HTTP 200 response has the following values.

            # * username: A string representation of an user's username passed in the request.

            # * course_id: A string representation of a Course ID.

            # * updates: List of messsage updates in format:

                # * id: String representation of id of update message

                # * date: String representation of publish date of update message

                # * content: String representation of update message

            # * if welcome-message was not dismissed than return one more field

            # *  'dismiss_url': A string represantation of dismiss url - optional



        **Example GET Response**
            {
                # "username": "bob",
                # "course_id": "edX/DemoX/Demo_Course",
                # "updates": [
                        {
                            # "id": "1",
                            # "date": "2021/01/01",
                            # "content": "My first update message"
                        },
                        # ],
                # "dismiss_url": "/courses/edX/DemoX/Demo_Course/course/dismiss_welcome_message"
            }
    """

    authentication_classes = (OAuth2AuthenticationAllowInactiveUser,
                              SessionAuthenticationAllowInactiveUser,
                              JwtAuthentication,)
    permission_classes = (IsAuthenticated, IsUserInUrl)

    def get(self, request, username, course_id):
        """
        Gets a updates messages.

        Args:
            request (Request): Django request object.
            username (string): URI element specifying the user's username.
            course_id (string): URI element specifying the course location.

        Return:
            A JSON serialized representation of the certificate.
        """
        def date_filter(update):
            update_date = update.get('date')
            update_id = update.get('id')
            if update_date and update_id:
                update_date = parse(update_date)
                if update_date <= datetime.today() and update_date >= datetime.today() - timedelta(days=14):
                    return True
                else:
                    return False
            else:
                return False

        def change_date_to_iso_format(update):
            update_date = update.get('date')
            if update_date:
                update_date = parse(update_date, dayfirst=True)
                update_date = update_date.isoformat()
                update['date'] = update_date
                return update

        course_key = CourseKey.from_string(course_id)
        course = courses.get_course_by_id(course_key)
        if not courses.check_course_access(course=course, user=request.user, action='load', check_if_enrolled=True):
            return Response(
                status=403,
                data={'detail': u'You do not have permission to perform this action.'}
            )

        ordered_updates = get_ordered_updates(request, course)
        ordered_updates = list(map(change_date_to_iso_format, ordered_updates))

        if not ordered_updates:
            return Response(
                status=404,
                data={'detail': u'Not found.'}
            )

        if not get_course_tag(request.user, course_key, PREFERENCE_KEY) == 'False':

            dismiss_url = reverse(
                'openedx.course_experience.dismiss_welcome_message', kwargs={'course_id': text_type(course_key)}
            )

            response_dict = {
                "username": username,
                "course_id": course_id,
                'dismiss_url': dismiss_url,
                'updates': ordered_updates[-1],
            }

        else:
            filtered_updates = list(filter(date_filter, ordered_updates[:-1]))
            response_dict = {"username": username,
                             "course_id": course_id,
                             "updates": filtered_updates}

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


class CourseRunOpinionViewSet(viewsets.ModelViewSet):
    """
    **Use Cases**
        Restful CRUD operations on course opinions.

    **Example Requests**

        GET /api/navoica/v1/courseopinion/
            returns all opinions
        GET /api/navoica/v1/courseopinion?course_id=xx&username=yyy
            returns opinions filtered by course_id and username
        GET /api/navoica/v1/courseopinion/{id}
            returns specified opinion

        POST /api/navoica/v1/courseopinion
            with payload
            {
                course_id = course-v1:course/course/run1,
                grade = "5.0",
                content = "very nice course"
            }
            adding new opinion
        PUT /api/navoica/v1/courseopinion/{id}
            modify opinion
        DELETE /api/navoica/v1/courseopinion/{id}
            delete specified opinion

    **Response Values

        GET: If the request is successful, an HTTP 200 "OK" response is returned
        along with a list of opinions dictionaries filtered by course_id in query_parameter.
        The details are contained in a JSON dictionary as follows:

        Otherwise, an HTTP 200 "OK" response is returned. The response
        contains the following value:

        * id: The opinion identifier.
        * course_id: The course identifier.
        * grade: Opinion grade.
        * content: Opinion content.
        * user: The author of opinion.
        * reviewed: reviwed status (default False).
        * created: Date of the creation.
        * last_udpated: Date of last modification.

    """
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser,
                              JwtAuthentication,)
    permission_classes = (IsAuthenticatedOrReadOnly, IsStaffOrOwner,)
    serializer_class = CourseOpinionSerializer
    lookup_field = 'id'
    filter_backends = (OrderingFilter, DjangoFilterBackend, SearchFilter)
    filterset_fields = ordering_fields = ('created',)

    def get_queryset(self):
        try:
            filter_dict = {}
            if course_key := (course_id := self.request.query_params.get('course_id')) and CourseKey.from_string(course_id):
                filtered_courses_id = (course.id for course in get_courses(
                    self.request.user, org=course_key.org) if course.number == course_key.course)
                if filtered_courses_id:
                    filter_dict['course_id__in'] = filtered_courses_id

                if (username := self.request.query_params.get('username')):
                    filter_dict['user__username'] = username
            return CourseRunOpinionModel.objects.filter(**filter_dict)
        except InvalidKeyError:
            return CourseRunOpinionModel.objects.none()

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            raise ValidationError(detail='You can not add additional opinion for this course.')

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return AdminCourseOpinionSerializer
        if self.action == 'create':
            return CreateCourseOpinionSerializer
        return CourseOpinionSerializer


class CourseGradesApiView(GradeViewMixin, APIView):
    """
    **Use Case**
        * Get course grades of user if they are allowed.
    **Example Request**
        GET /api/grades/v1/courses/{course_id}/                              - Get grades for request user
    **GET Parameters**
        A GET request may include the following parameters.
        * course_id: (required) A string representation of a Course ID.
    **GET Response Values**
        If the request for information about the course grade
        is successful, an HTTP 200 "OK" response is returned.
        The HTTP 200 response has the following values.
        * username: A string representation of a user's username passed in the request.
        * email: A string representation of a user's email.
        * course_id: A string representation of a Course ID.
        * passed: Boolean representing whether the course has been
                  passed according to the course's grading policy.
        * percent: A float representing the overall grade for the course
        * letter_grade: A letter grade as defined in grading policy (e.g. 'A' 'B' 'C' for 6.002x) or None
    **Example GET Response**
        {
            "username": "bob",
            "email": "bob@example.com",
            "course_id": "course-v1:edX+DemoX+Demo_Course",
            "passed": false,
            "percent": 0.03,
            "letter_grade": null,
        }
    """
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser,
                              SessionAuthenticationAllowInactiveUser,
                              JwtAuthentication,)
    permission_classes = (IsAuthenticated, )


    @verify_course_exists
    def get(self, request, course_id=None):
        # Gets a course progress status.
        # Args:
        #     request (Request): Django request object.
        #     course_id (string): URI element specifying the course location.
        #                         Can also be passed as a GET parameter instead.
        # Return:
        #     A JSON serialized representation of the requesting user's current grade status.

        course_key = get_course_key(request, course_id)
        try:
            CourseEnrollment.objects.get(user=request.user, course_id=course_key)
        except CourseEnrollment.DoesNotExist:
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message='The user matching the requested username is not enrolled in this course',
                error_code='user_not_enrolled'
            )

        with self._get_user_or_raise(request, course_key) as grade_user:
            return self._get_single_user_grade(grade_user, course_key)


class CareerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A simple ViewSet for viewing career.
    """
    serializer_class = CareerSerializer
    filter_backends = (OrderingFilter, DjangoFilterBackend, SearchFilter)
    lookup_field = 'id'
    filterset_fields = search_fields = ordering_fields = '__all__'

    def get_queryset(self):
        return CareerModel.objects.filter(publish=True)
