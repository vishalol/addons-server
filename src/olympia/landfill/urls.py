from django.conf.urls import include, url

from . import views

urlpatterns = [
    url(r'^generate-addon-user/$', views.AddonUserCreate.as_view(),
        name='landfill.generate-addon-user'),
]
