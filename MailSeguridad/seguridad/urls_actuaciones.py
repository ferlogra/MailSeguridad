from __future__ import annotations

from django.urls import path

from . import views


urlpatterns = [
    path("", views.actuaciones_list_view, name="actuaciones_list"),
    path("nuevo/", views.actuacion_create_view, name="actuacion_create"),
    path("<int:pk>/", views.actuacion_detail_view, name="actuacion_detail"),
]
