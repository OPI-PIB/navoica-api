
Navoica-api
==============

Navoica-api expanding openedx rest api.

Quick start
------------


1. Add "navoica-api" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'navoica_api',
        ...
    ]

2. Include the navoica-api URLconf in your project lms/urls.py like this:

    url(r'^api/navoica/', include('navoica_api.api.urls', namespace='navoica_api')),

Enjoy!
