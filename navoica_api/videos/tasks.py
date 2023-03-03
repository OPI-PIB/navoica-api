import tempfile

import ffmpeg
from celery import shared_task
from django.conf import settings

from navoica_api.videos import VIDEOS_LOG, path_to_resolution
from navoica_api.videos.storage import TemporaryStorage, VideoAzureStorage, RawVideoAzureStorage

videos_storage = VideoAzureStorage()
raw_videos_storage = RawVideoAzureStorage()
tmp_storage = TemporaryStorage()


def encode_upload_video(video_id, resolution):
    # ffmpeg -i $videoid -strict -2 -s $size $videoid.mp4
    VIDEOS_LOG.info("[Encode video] Starting: {} / {}".format(video_id, resolution))

    tmp_file = tempfile.NamedTemporaryFile(suffix='.mp4')

    stream = ffmpeg.input(tmp_storage.path(video_id))
    stream = ffmpeg.output(stream, tmp_file.name, **{'s': resolution, 'strict': '-2'})
    ffmpeg.run(stream, overwrite_output=True)

    VIDEOS_LOG.info("[Encode video] Uploading: %s %s" % (resolution, video_id))

    path = path_to_resolution(resolution=resolution, video_id=video_id)

    videos_storage.save(
        path, tmp_file
    )

    tmp_file.close()

    VIDEOS_LOG.info("[Encode video] Uploaded and deleted: %s" % path)


@shared_task(max_retries=3, default_retry_delay=60 * 5, queue=settings.HIGH_PRIORITY_QUEUE)
def encode_videos(video_id):
    VIDEOS_LOG.info("[Encode videos] Start encoding for: %s" % video_id)

    with raw_videos_storage.open(video_id) as f:
        tmp_storage.save(video_id, f)

    VIDEOS_LOG.info("[Encode videos] Finished downloading and saved: %s" % video_id)

    for resolution in settings.VIDEO_RESOLUTIONS:
        encode_upload_video(
            video_id,
            resolution
        )

    tmp_storage.delete(video_id)

    VIDEOS_LOG.info("[Encode videos] Finished encoding for: %s" % video_id)
