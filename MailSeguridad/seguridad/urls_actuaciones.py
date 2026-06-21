from __future__ import annotations

from django.urls import path

from . import views


urlpatterns = [
    path("", views.actuaciones_list_view, name="actuaciones_list"),
    path("nuevo/", views.actuacion_create_view, name="actuacion_create"),
    path("<int:pk>/", views.actuacion_detail_view, name="actuacion_detail"),
    path("api/por-mensaje/<str:mensaje_id>/", views.actuaciones_por_mensaje_api, name="actuaciones_por_mensaje"),
    path("api/recientes/<str:mensaje_id>/", views.actuaciones_recientes_api, name="actuaciones_recientes_api"),
    path("api/crear/", views.actuacion_create_api, name="actuacion_create_api"),
    path("api/aplicar/<int:pk>/<str:mensaje_id>/", views.actuacion_aplicar_api, name="actuacion_aplicar_api"),
    path("api/<int:pk>/eliminar/", views.actuacion_delete_api, name="actuacion_delete_api"),
    path("api/<int:pk>/actualizar/", views.actuacion_update_api, name="actuacion_update_api"),
]
