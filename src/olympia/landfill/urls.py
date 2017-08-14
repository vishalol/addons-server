from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^generate-addons/$', views.GenerateAddons.as_view(),
        name='landfill.generate-addons'),
    url(r'^dump-current-state/$', views.DumpCurrentState.as_view(),
        name='landfill.dump-current-state'),
    url(r'^restore-current-state/$', views.RestoreCurrentState.as_view(),
        name='landfill.restore-current-state'),
]
