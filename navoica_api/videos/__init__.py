import logging

VIDEOS_LOG = logging.getLogger('navoica_api.videos')


def path_to_resolution(resolution, video_id):
    return "{}/{}".format(resolution, video_id)
