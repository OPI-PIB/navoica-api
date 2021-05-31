
from django.conf.urls import include, url
from static_template_view import views


urlpatterns = [
    url(r'^legend', views.render, {'template': 'legend.html'}, name="legend"),
    url(r'^accessibility$', views.render, {'template': 'accessibility.html'}, name="accessibility"),
    url(r'^cookies$', views.render, {'template': 'cookies.html'}, name="cookies"),
]
