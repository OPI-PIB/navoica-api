"""
Serializers classes for Navoica api v1
"""
from rest_framework import serializers

from lms.djangoapps.certificates.models import GeneratedCertificate


class GeneratedCertificateSerializer(serializers.ModelSerializer):
    profile_name = serializers.CharField(read_only=True, source='user.profile.name')
    username = serializers.CharField(read_only=True, source='user.username')
    email = serializers.CharField(read_only=True, source='user.email')
    class Meta:
        model = GeneratedCertificate
        fields = ['profile_name', 'username', 'email', 'created_date', 'grade']
