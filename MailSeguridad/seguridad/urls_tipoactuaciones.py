from __future__ import annotations

from django.urls import path

from . import views


urlpatterns = [
    path("", views.tipoactuaciones_list_view, name="tipoactuaciones_list"),
    path("nuevo/", views.tipoactuacion_create_view, name="tipoactuacion_create"),
    path("<int:pk>/", views.tipoactuacion_detail_view, name="tipoactuacion_detail"),
]
