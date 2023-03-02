from django.db.models.signals import post_save
from django.dispatch import receiver
from edxval.models import Video

from navoica_api.videos import VIDEOS_LOG
from navoica_api.videos.tasks import encode_videos


@receiver(post_save, sender=Video, dispatch_uid="navoica_api_encode_video_recv")
def encode_video_recv(sender, instance, **kwargs):
    if instance.status == 'upload_completed':
        VIDEOS_LOG.info("Video Signal: Generating videos for Video: {}".format(instance.pk))
        encode_videos.delay(instance.edx_video_id)
