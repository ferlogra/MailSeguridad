from __future__ import annotations

from django.urls import path

from . import views


urlpatterns = [
    path("", views.profile_view, name="profile"),
    path("cambiar-contrasena/", views.password_change_view, name="password_change"),
]
