# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import CourseKeyField
from django.db import models
from lms.djangoapps.instructor_task.models import InstructorTask
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

class CertificateGenerationMergeHistory(TimeStampedModel):
    course_id = CourseKeyField(max_length=255)
    generated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    pdf = models.FileField(upload_to="merge_certificates/%Y/%m/%d/")
    instructor_task = models.ForeignKey(InstructorTask, on_delete=models.CASCADE)

    def get_task_name(self):
        if self.pdf.name:
            return _("generated")
        return _("generating")

    class Meta(object):
        app_label = "certificates"
