from __future__ import annotations

from django.urls import path

from . import views


urlpatterns = [
    path("", views.accionesauto_list_view, name="accionesauto_list"),
    path("nuevo/", views.accionesauto_create_view, name="accionesauto_create"),
    path("<int:pk>/", views.accionesauto_detail_view, name="accionesauto_detail"),
]
