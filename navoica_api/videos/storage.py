from django.core.files.storage import FileSystemStorage
from storages.backends.azure_storage import AzureStorage


class VideoAzureStorage(AzureStorage):
    azure_container = 'movies'


class RawVideoAzureStorage(AzureStorage):
    azure_container = 'movies'
    location = 'videos'


class TemporaryStorage(FileSystemStorage):
    location = '/edx/var/edxapp/tmp/'
    base_url = ''
