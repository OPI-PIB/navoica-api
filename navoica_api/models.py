# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import uuid
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


class CourseRunOpinionModel(models.Model):
    """
    Model for Course Opinion
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course_id = CourseKeyField(max_length=255)
    grade = models.DecimalField(max_digits=2, decimal_places=1)
    content = models.CharField(max_length=3000)
    user = models.ForeignKey(User, db_index=True, on_delete=models.CASCADE)
    reviewed = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['course_id', 'user'], name='constraint')
        ]
