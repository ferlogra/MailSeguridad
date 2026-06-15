from __future__ import annotations

from django.urls import path

from . import views


urlpatterns = [
    path("list/", views.table_config_list_api, name="table_config_list"),
    path("save/", views.table_config_save_api, name="table_config_save"),
    path("delete/", views.table_config_delete_api, name="table_config_delete"),
]
