import logging
import os

from django.test.client import RequestFactory
from django.contrib.auth.models import AnonymousUser
from lms.djangoapps.certificates.views import render_cert_by_uuid
from bs4 import BeautifulSoup
import urllib.parse
from urllib.parse import urlparse
from django.conf import settings
import requests
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from lms.djangoapps.certificates.models import CertificateStatuses, GeneratedCertificate
from lms.djangoapps.instructor_task.models import InstructorTask
from shutil import make_archive
from lms.djangoapps.instructor_task.tasks_helper.runner import TaskProgress
from time import time

log = logging.getLogger(__name__)

def render_pdf(html,certificate_uuid,return_content=False):

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

        for href in soup.find_all('link'):
            link_href = href['href']
            o = urlparse(link_href)
            href['href'] = o._replace(netloc=settings.INTERNAL_HOST_IP, scheme="http").geturl()

    html = str(soup)
    log.info(
        "Cert [PDF]: %s" % html
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
        if return_content:
            return r.content

        path = default_storage.save('certificates/'+certificate_uuid+".pdf", ContentFile(r.content))
        certificate = GeneratedCertificate.objects.get(
            verify_uuid=certificate_uuid
        )
        certificate.download_url = default_storage.url(path)
        certificate.save()


def merging_all_course_certificates(_xmodule_instance_args, _entry_id, course_id, task_input, action_name):

    start_time = time()

    certificates = GeneratedCertificate.eligible_certificates.filter(
        status=CertificateStatuses.downloadable,
        course_id=course_id
    )

    task_progress = TaskProgress(action_name, certificates.count(), start_time)

    current_step = {'step': 'Merging Certificates'}
    task_progress.update_task_state(extra_meta=current_step)

    base_tmp = "/tmp/certificates/"
    path_tmp = base_tmp+str(course_id)+"/"
    try:
        os.makedirs(path_tmp)
    except OSError:
        pass

    factory = RequestFactory()
    fake_request = factory.get("")
    fake_request.user = AnonymousUser()
    fake_request.session = {}

    # Generate certificate for each student
    for certificate in certificates:
        task_progress.attempted += 1
        current_step = {'step': certificate.verify_uuid}

        output = render_cert_by_uuid(fake_request, certificate.verify_uuid)

        pdf_content = render_pdf(output.content, True)

        if pdf_content:
            with open(path_tmp+certificate.verify_uuid+".pdf", 'wb') as f:
                f.write(pdf_content)
            task_progress.succeeded += 1
        else:
            task_progress.failed += 1

        task_progress.update_task_state(extra_meta=current_step)

    cert_genereted_history, created = CertificateGenerationMergeHistory.objects.get_or_create(
        instructor_task=InstructorTask.objects.get(task_id=_xmodule_instance_args['task_id']),
    )
    cert_genereted_history.course_id = str(course_id)
    cert_genereted_history.save()

    current_step = {'step': 'Compressing all certificates to ZIP archive'}
    task_progress.update_task_state(extra_meta=current_step)

    make_archive(base_tmp+str(course_id), 'zip', root_dir=path_tmp, base_dir=None)

    fh = open(base_tmp+str(course_id)+'.zip', "r")
    if fh:
        file_content = ContentFile(fh.read())
        cert_genereted_history.pdf.save(str(course_id)+'.zip', file_content)
        cert_genereted_history.save()

    return task_progress.update_task_state(extra_meta=current_step)
