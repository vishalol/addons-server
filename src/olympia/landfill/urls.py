from django.conf.urls import include, url

from . import views


urlpatterns = [
    url(r'^generate-addons/$', views.GenerateAddons.as_view(),
        name='landfill.generate-addons'),
    url(r'^cleanup/$', views.Cleanup.as_view(), name='landfill.cleanup'),
]
