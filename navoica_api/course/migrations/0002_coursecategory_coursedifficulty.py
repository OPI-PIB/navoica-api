# Generated by Django 2.2.17 on 2023-03-27 21:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('navoica_course', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseCategory',
            fields=[
                ('id', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='CourseDifficulty',
            fields=[
                ('id', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
            ],
        ),
    ]