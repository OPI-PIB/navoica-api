from lms.djangoapps.certificates.models import GeneratedCertificate
from openedx.core.djangoapps.signals.signals import COURSE_CERT_AWARDED
from django.dispatch import receiver
from navoica_api.certificates.tasks import render_pdf_cert_by_uuid

@receiver(COURSE_CERT_AWARDED, sender=GeneratedCertificate)
def handle_generating_cert_awarded(certificate, user, course_key, **kwargs):
    if not certificate.download_url:
        render_pdf_cert_by_uuid.delay(certificate.verify_uuid)
