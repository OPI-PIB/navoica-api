import logging
import os
import uuid
from shutil import make_archive
from time import time
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from django.apps import apps
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils.translation import ugettext as _
from lms.djangoapps.certificates.models import CertificateStatuses, GeneratedCertificate

log = logging.getLogger(__name__)


def render_pdf(html, certificate_pk):
    soup = BeautifulSoup(html, "html.parser")

    """
    information: replace all url from navoica.pl to internal ip address due to incorrect routing from inside host
    """
    if settings.INTERNAL_HOST_IP:
        for img in soup.find_all(['img', 'script']):
            if img.get("src", None):
                img_src = img['src']
                o = urlparse(img_src)
                img['src'] = o._replace(netloc=settings.INTERNAL_HOST_IP, scheme="http").geturl()

        for href in soup.find_all(['link', 'base']):
            link_href = href['href']
            o = urlparse(link_href)
            href['href'] = o._replace(netloc=settings.INTERNAL_HOST_IP, scheme="http").geturl()

    html = str(soup)
    log.info(
        "Cert [PDF]: {}".format(html)
    )

    multipart_form_data = {
        'file': ('index.html', html),
        'marginTop': (None, '0',),
        'marginBottom': (None, '0',),
        'marginLeft': (None, '0',),
        'marginRight': (None, '0',),
        'landscape': (None, 'true',),
    }

    # $ docker run --rm -p 3000:3000 thecodingmachine/gotenberg:5
    r = requests.post(settings.GOTENBERG_URL + 'convert/html', files=multipart_form_data)

    if r.status_code == 200:
        path = default_storage.save('certificates/' + str(uuid.uuid4()) + '.pdf', ContentFile(r.content))
        certificate = GeneratedCertificate.objects.get(
            pk=certificate_pk
        )
        certificate.download_url = default_storage.url(path)
        certificate.save(update_fields=['download_url'])
        return certificate


if apps.is_installed("lms.djangoapps.instructor_task"):
    def merging_all_course_certificates(_xmodule_instance_args, _entry_id, course_id, task_input, action_name):

        from lms.djangoapps.instructor_task.models import InstructorTask
        from lms.djangoapps.instructor_task.tasks_helper.runner import TaskProgress
        from navoica_api.models import CertificateGenerationMergeHistory

        start_time = time()

        certificates = GeneratedCertificate.eligible_certificates.filter(
            status=CertificateStatuses.downloadable,
            course_id=course_id
        ).exclude(download_url='')

        task_progress = TaskProgress(action_name, certificates.count(), start_time)

        current_step = {'step': _('Merging Certificates')}
        task_progress.update_task_state(extra_meta=current_step)

        base_tmp = "/tmp/certificates/"
        path_tmp = base_tmp + str(course_id) + "/"

        try:
            os.makedirs(path_tmp)
        except OSError:
            pass

        # Download certificate for each student
        for certificate in certificates:
            task_progress.attempted += 1
            current_step = {'step': certificate.verify_uuid}

            r = requests.get(certificate.download_url)
            if r.status_code == 200:
                with open(path_tmp + certificate.verify_uuid + ".pdf", 'wb') as f:
                    f.write(r.content)
                task_progress.succeeded += 1
            else:
                task_progress.failed += 1

            task_progress.update_task_state(extra_meta=current_step)

        cert_generated_history, created = CertificateGenerationMergeHistory.objects.get_or_create(
            instructor_task=InstructorTask.objects.get(task_id=_xmodule_instance_args['task_id']),
        )
        cert_generated_history.course_id = str(course_id)
        cert_generated_history.save()

        current_step = {'step': _('Compressing all certificates to ZIP archive')}
        task_progress.update_task_state(extra_meta=current_step)

        make_archive(base_tmp + str(course_id), 'zip', root_dir=path_tmp, base_dir=None)

        fh = open(base_tmp + str(course_id) + '.zip', "rb")
        if fh:
            file_content = ContentFile(fh.read())
            cert_generated_history.pdf.save(str(course_id) + '.zip', file_content)
            cert_generated_history.save()

        return task_progress.update_task_state(extra_meta=current_step)
