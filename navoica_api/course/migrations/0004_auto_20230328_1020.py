# Generated by Django 2.2.17 on 2023-03-28 10:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('navoica_course', '0003_auto_20230327_2115'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='coursecategory',
            options={'verbose_name': 'course category', 'verbose_name_plural': 'course categories'},
        ),
        migrations.AlterModelOptions(
            name='coursedifficulty',
            options={'verbose_name': 'course difficulty', 'verbose_name_plural': 'course difficulties'},
        ),
        migrations.AlterModelOptions(
            name='courseorganizer',
            options={'verbose_name': 'course organizer', 'verbose_name_plural': 'course organizers'},
        ),
        migrations.AlterField(
            model_name='courseorganizer',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='course-organizer/'),
        ),
        migrations.AlterField(
            model_name='courseorganizer',
            name='image_en',
            field=models.ImageField(blank=True, null=True, upload_to='course-organizer/'),
        ),
        migrations.AlterField(
            model_name='courseorganizer',
            name='image_pl',
            field=models.ImageField(blank=True, null=True, upload_to='course-organizer/'),
        ),
    ]
