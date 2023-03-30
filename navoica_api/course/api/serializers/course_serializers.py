from navoica_api.course.models import CourseOrganizer
from rest_framework import serializers
from django_countries.serializer_fields import CountryField


class CourseOrganizerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseOrganizer
        fields = ['id', 'title', 'image', 'url']


class CourseTitleSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()


class CourseDisplayValueSerializer(serializers.Serializer):
    display_name = serializers.CharField()
    value = serializers.CharField()


class CourseValueSerializer(serializers.Serializer):
    value = serializers.CharField()


class CourseLanguageSerializer(serializers.Serializer):
    code = serializers.CharField()
    title = serializers.CharField()


class CourseInfoSerializer(serializers.Serializer):
    difficulty = CourseTitleSerializer(required=False)
    organizer = CourseOrganizerSerializer(required=False)
    category = CourseTitleSerializer(required=False)
    timetable = CourseTitleSerializer(required=False)

    external_enroll_url = CourseDisplayValueSerializer(required=False)
    append_eu_logos_certificate = CourseDisplayValueSerializer(required=False)

    availability = serializers.CharField(required=False)

    course_name = serializers.CharField(required=False)
    course_organization = serializers.CharField(required=False)
    course_run = serializers.CharField(required=False)
    course_language = CourseLanguageSerializer(required=False)
