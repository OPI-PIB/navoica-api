# Generated by Django 2.2.17 on 2021-07-20 10:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
import opaque_keys.edx.django.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CertificateGenerationMergeHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('course_id', opaque_keys.edx.django.models.CourseKeyField(max_length=255)),
                ('pdf', models.FileField(upload_to='merge_certificates/%Y/%m/%d/')),
                ('generated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('instructor_task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='instructor_task.InstructorTask')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
