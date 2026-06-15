from __future__ import annotations

from django.urls import path

from . import views


urlpatterns = [
    path("", views.tipoactuaciones_list_view, name="tipoactuaciones_list"),
    path("<int:pk>/", views.tipoactuacion_detail_view, name="tipoactuacion_detail"),
]
