from django.db import IntegrityError, transaction
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_http_methods, require_POST
from lms.djangoapps.instructor.views.api import common_exceptions_400
from opaque_keys.edx.keys import CourseKey
from navoica_api.certificates.tasks import merge_all_certificates
from lms.djangoapps.instructor_task.api_helper import (
    check_arguments_for_overriding, check_arguments_for_rescoring,
    check_entrance_exam_problems_for_rescoring,
    encode_entrance_exam_and_student_input, encode_problem_and_student_input,
    submit_task)
from common.djangoapps.util.json_request import JsonResponse
from django.utils.translation import ugettext as _

from navoica_api.models import CertificateGenerationMergeHistory


def merge_certificates(request, course_key):
    task_type = 'merge_all_certificates_all'
    task_input = {}

    task_class = merge_all_certificates
    task_key = ""

    instructor_task = submit_task(request, task_type, task_class, course_key,
                                  task_input, task_key)

    obj, created = CertificateGenerationMergeHistory.objects.get_or_create(
        instructor_task=instructor_task,
    )
    obj.course_id = course_key
    obj.generated_by = request.user
    obj.save()

    return instructor_task

@transaction.non_atomic_requests
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_POST
@common_exceptions_400
def start_merge_certificates(request, course_id):
    """
     Start regenerating certificates for students whose certificate statuses lie with in 'certificate_statuses'
     entry in POST data.
     """
    course_key = CourseKey.from_string(course_id)
    merge_certificates(request, course_key)
    response_payload = {
        'message': _('Merging certificates task has been started. '
                     'You can view the status of the generation task in the "Pending Tasks" section.'),
        'success': True
    }
    return JsonResponse(response_payload)
