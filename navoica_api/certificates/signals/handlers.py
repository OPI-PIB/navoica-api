import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from lms.djangoapps.certificates.models import GeneratedCertificate
from common.djangoapps.student.models import CourseEnrollment

from navoica_api.certificates.tasks import render_pdf_cert_by_pk

TASK_LOG = logging.getLogger('navoica_api.certificates')


@receiver(post_save, sender=GeneratedCertificate, dispatch_uid="navoica_api_update_cert_signal")
def update_cert(sender, instance, **kwargs):
    TASK_LOG.info("Certificates Signal: Generating pdf for cert {}".format(instance.pk))
    render_pdf_cert_by_pk.delay(instance.pk)


@receiver(pre_save, sender=CourseEnrollment, dispatch_uid="navoica_api_update_course_enrollment")
def update_course_enrollment(sender, instance, **kwargs):
    if instance.mode != 'honor':
        TASK_LOG.info("Course Enrollment Signal: changing mode to honor instead of {}".format(instance.mode))
        instance.mode = 'honor'
