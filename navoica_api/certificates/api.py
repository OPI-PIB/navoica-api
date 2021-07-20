from django.db import IntegrityError, transaction
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_http_methods, require_POST
from lms.djangoapps.instructor.views.api import common_exceptions_400


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
    lms.djangoapps.instructor_task.api.merge_certificates(request, course_key)
    response_payload = {
        'message': _('Merging certificates task has been started. '
                     'You can view the status of the generation task in the "Pending Tasks" section.'),
        'success': True
    }
    return JsonResponse(response_payload)
