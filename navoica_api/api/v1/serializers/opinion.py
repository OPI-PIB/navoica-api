from navoica_api.models import CourseRunOpinionModel
from rest_framework import serializers


class AdminMeta:
    """
    Meta class for AdminCourseOpinionSerializer
    """
    model = CourseRunOpinionModel
    fields = (
        'id',
        'course_id',
        'grade',
        'content',
        'user',
        'reviewed',
        'created',
        'last_updated',
    )
    lookup_field = 'id'


class CourseMeta(AdminMeta):
    """
    Meta class for CourseOpinionSerializer
    """
    read_only_fields = ('reviewed', 'course_id', 'user')


class CreateCourseMeta(AdminMeta):
    """
    Meta class for CreateCourseOpinionSerializer
    """
    read_only_fields = ('reviewed',)


class AdminCourseOpinionSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer Class for CourseOpinion Model for user with staff = true
    """
    user = serializers.StringRelatedField(many=False)

    Meta = AdminMeta

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        validated_data['user'] = user
        return super().create(validated_data)


class CourseOpinionSerializer(AdminCourseOpinionSerializer):
    """
    Serializer Class for CourseOpinion Model
    """
    Meta = CourseMeta


class CreateCourseOpinionSerializer(AdminCourseOpinionSerializer):
    """
    Serializer Class for CourseOpinion Model
    """
    Meta = CreateCourseMeta
