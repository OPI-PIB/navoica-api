from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers


class UserSerializer(serializers.Serializer):
    """
    Class that serializes the User model and UserProfile model together.
    """

    def to_representation(self, user):
        try:
            user_profile = user.profile
        except ObjectDoesNotExist:
            user_profile = None

        data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "date_joined": user.date_joined,
            "is_active": user.is_active,
            "name": None,
            "gender": None,
            "year_of_birth": None,
            "level_of_education": None,

        }

        if user_profile:
            data.update(
                {
                    "name": user_profile.name,
                    "gender": user_profile.gender,
                    "year_of_birth": user_profile.year_of_birth,
                    "level_of_education": user_profile.level_of_education
                }
            )
