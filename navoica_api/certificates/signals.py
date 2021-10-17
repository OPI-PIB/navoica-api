import logging
from lms.djangoapps.certificates.models import GeneratedCertificate
from openedx.core.djangoapps.signals.signals import COURSE_CERT_AWARDED
from django.dispatch import receiver
from navoica_api.certificates.tasks import render_pdf_cert_by_uuid

log = logging.getLogger(__name__)


@receiver(COURSE_CERT_AWARDED, sender=GeneratedCertificate)
def handle_generating_cert_awarded(certificate, user, course_key, **kwargs):
    log.info("Signal: COURSE_CERT_AWARDED received. Checking certificate for course: {}".format(course_key))
    if not certificate.download_url:
        log.info(
            "Signal: COURSE_CERT_AWARDED Generating certificate: {} for course: {} and user: {}".format(certificate.pk,
                                                                                                        course_key,
                                                                                                        user.pk))
        render_pdf_cert_by_uuid.delay(certificate.verify_uuid)
