from django.db import models
from abc import ABC, abstractmethod


class CourseManager(models.Manager):

    def get_or_none(self, **kwargs):
        try:
            return self.get(**kwargs)
        except:
            return None

    def get_serialized_or_none(self, **kwargs):
        try:
            return self.get_or_none(**kwargs).get_serialized()
        except Exception as e:
            print(e)
            return None


class CourseInfoAbstract(models.Model):

    objects = CourseManager()

    def get_serialized(self):
        from navoica_api.course.api.serializers.course_serializers import CourseTitleSerializer

        obj = CourseTitleSerializer(
            data={
                "id": self.pk,
                "title": self.title,
            }
        )
        obj.is_valid()

        return obj.data

    class Meta:
        abstract = True


class CourseOrganizer(CourseInfoAbstract):
    title = models.CharField(max_length=255)
    url = models.URLField(max_length=255, null=True, blank=True)
    image = models.ImageField(
        upload_to='course-organizer/', null=True, blank=True)

    def get_serialized(self):
        from navoica_api.course.api.serializers.course_serializers import CourseOrganizerSerializer
        return CourseOrganizerSerializer(
            instance=self
        ).data

    class Meta:
        verbose_name = "course organizer"
        verbose_name_plural = "course organizers"


class CourseDifficulty(CourseInfoAbstract):
    id = models.CharField(primary_key=True, max_length=100)
    title = models.CharField(max_length=255)

    class Meta:
        verbose_name = "course difficulty"
        verbose_name_plural = "course difficulties"


class CourseCategory(CourseInfoAbstract):
    id = models.CharField(primary_key=True, max_length=100)
    title = models.CharField(max_length=255)

    class Meta:
        verbose_name = "course category"
        verbose_name_plural = "course categories"
