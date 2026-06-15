from __future__ import annotations

from django.urls import path

from . import views


urlpatterns = [
    path("", views.mensajes_list_view, name="mensajes_list"),
    path("<int:pk>/", views.mensaje_detail_view, name="mensaje_detail"),
]
