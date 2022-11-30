from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings


def scorm_xblock_storage(xblock):
    return S3Boto3Storage(
        bucket=settings.AWS_STORAGE_BUCKET_NAME,
        access_key=settings.AWS_ACCESS_KEY_ID,
        secret_key=settings.AWS_SECRET_ACCESS_KEY,
        host=settings.AWS_S3_ENDPOINT_URL,
        querystring_expire=86400,
        custom_domain=settings.LMS_BASE + "/scorm-xblock"
    )
