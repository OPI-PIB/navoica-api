'''
Config of navoica API app
'''
from __future__ import unicode_literals

from django.apps import AppConfig
# from openedx.core.djangoapps.plugins.constants import ProjectType, SettingsType, PluginURLs, PluginSettings


class NavoicaApiConfig(AppConfig):
    """
    Application Configuration for Instructor.
    """
    name = u'navoica_api'

    # plugin_app = {
    #     PluginURLs.CONFIG: {
    #         ProjectType.LMS: {
    #             PluginURLs.NAMESPACE: u'navoica_api',
    #             PluginURLs.REGEX: u'api/navoica/',
    #             PluginURLs.RELATIVE_PATH: u'api.urls',
    #         }
    #     },
    # }  # config like plugin - switch on in next release
