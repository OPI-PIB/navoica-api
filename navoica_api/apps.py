'''
Config of navoica API app
'''
from __future__ import unicode_literals
from django.apps import AppConfig


class NavoicaApiConfig(AppConfig):
    """
    Application Configuration for Instructor.
    """
    name = u'navoica_api'

    def ready(self):
        pass

    # plugin_app = {
    #     PluginURLs.CONFIG: {
    #         ProjectType.LMS: {
    #             PluginURLs.NAMESPACE: u'navoica_api',
    #             PluginURLs.REGEX: u'api/navoica/',
    #             PluginURLs.RELATIVE_PATH: u'api.urls',
    #         }
    #     },
    # }  # config like plugin - switch on in next release
