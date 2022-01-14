import logging
from functools import partial
import requests

from celery import task
from django.conf import settings
from django.utils.translation import ugettext_noop
from lms.djangoapps.instructor_task.tasks_base import BaseInstructorTask
from lms.djangoapps.instructor_task.tasks_helper.runner import run_main_task
from lms.djangoapps.certificates.models import GeneratedCertificate
from navoica_api.certificates.functions import render_pdf, merging_all_course_certificates

TASK_LOG = logging.getLogger('edx.celery.task')


@task(bind=True, max_retries=3, default_retry_delay=60 * 5)
def render_pdf_cert_by_pk(self, certificate_pk):
    certificate = GeneratedCertificate.objects.get(
        pk=certificate_pk
    )

    if not certificate.download_url and certificate.status == 'downloadable':

        TASK_LOG.info(
            "Certificates: Generating pdf for cert {}".format(
                certificate.pk))

        r = requests.get("http://{}/certificates/{}".format(settings.INTERNAL_HOST_IP, certificate.verify_uuid))

        if r.status_code == 200:
            certificate = render_pdf(html=r.content, certificate_pk=certificate_pk)
            if certificate:
                return certificate
        TASK_LOG.info(
            "Certificates: Retry generating pdf for cert {}".format(
                certificate.pk))
        self.retry()
    else:
        TASK_LOG.info(
            "Certificates: Skipping generate pdf for cert {}due to download_url exists or status is not downloadable".format(
                certificate.pk))


@task(base=BaseInstructorTask, queue=settings.HIGH_PRIORITY_QUEUE)
def merge_all_certificates(entry_id, xmodule_instance_args):
    """
    Grade students and generate certificates.
    """
    # Translators: This is a past-tense verb that is inserted into task progress messages as {action}.
    action_name = ugettext_noop('merge all certificates')
    TASK_LOG.info(
        u"Task: %s, InstructorTask ID: %s, Task type: %s, Preparing for task execution",
        xmodule_instance_args.get('task_id'), entry_id, action_name
    )

    task_fn = partial(merging_all_course_certificates, xmodule_instance_args)
    return run_main_task(entry_id, task_fn, action_name)
