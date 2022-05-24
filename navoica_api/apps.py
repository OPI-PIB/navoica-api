'''
Config of navoica API app
'''
from __future__ import unicode_literals
from django.apps import AppConfig
from django.db.models.signals import post_save

class NavoicaApiConfig(AppConfig):
    """
    Application Configuration for Instructor.
    """
    name = u'navoica_api'

    def ready(self):
        from navoica_api.certificates.signals.handlers import update_cert
        # post_save.connect(update_cert)

    # plugin_app = {
    #     PluginURLs.CONFIG: {
    #         ProjectType.LMS: {
    #             PluginURLs.NAMESPACE: u'navoica_api',
    #             PluginURLs.REGEX: u'api/navoica/',
    #             PluginURLs.RELATIVE_PATH: u'api.urls',
    #         }
    #     },
    # }  # config like plugin - switch on in next release
