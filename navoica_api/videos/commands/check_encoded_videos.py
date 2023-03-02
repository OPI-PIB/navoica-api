from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from edxval.models import Video
from navoica_api.videos.tasks import encode_videos

from navoica_api.videos import path_to_resolution, VIDEOS_LOG
from navoica_api.videos.storage import VideoAzureStorage
from django.conf import settings


class Command(BaseCommand):
    help = 'Check that all videos added in the last 7 days have all resolutions'

    def handle(self, *args, **options):
        videos_storage = VideoAzureStorage()
        for video in Video.objects.filter(status='upload_completed', created__gte=datetime.now() - timedelta(days=7)):
            for resolution in settings.VIDEO_RESOLUTIONS:
                path = path_to_resolution(resolution=resolution, video_id=video.edx_video_id)
                if not videos_storage.exists(path):
                    VIDEOS_LOG.info("[Encode video] Sending to encode {}".format(video.edx_video_id))
                    encode_videos.delay(video.edx_video_id)
                    break
