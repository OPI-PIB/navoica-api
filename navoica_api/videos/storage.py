from django.core.files.storage import FileSystemStorage
from storages.backends.azure_storage import AzureStorage
from storages.backends.s3boto3 import S3Boto3Storage


class VideoAzureStorage(AzureStorage):
    azure_container = 'movies'


class RawVideoAzureStorage(AzureStorage):
    azure_container = 'movies'
    location = 'videos'

class VideoS3Storage(S3Boto3Storage):
    bucket_name = 'navoica-movies'
    custom_domain = None
    addressing_style = 'virtual'

class RawVideoS3Storage(S3Boto3Storage):
    bucket_name = 'navoica-movies'
    location = 'videos'
    addressing_style = 'virtual'
    custom_domain = None

class TemporaryStorage(FileSystemStorage):
    location = '/edx/var/edxapp/tmp/'
    base_url = ''
