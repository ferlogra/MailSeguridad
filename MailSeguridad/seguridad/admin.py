from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Actuacion, Mensaje, PasswordResetToken, TableConfig, TipoActuacion, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "email", "rol", "is_staff", "is_active", "fecha_alta"]
    list_filter = ["rol", "is_staff", "is_active"]
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Información adicional", {"fields": ("telefono", "rol", "fecha_alta", "fecha_baja")}),
    )


@admin.register(TableConfig)
class TableConfigAdmin(admin.ModelAdmin):
    list_display = ["usuario", "menu_option", "name"]
    list_filter = ["menu_option"]


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ["usuario", "created_at", "used"]
    list_filter = ["used"]


@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    list_display = ["id", "id_principal", "familia", "grupo", "estado", "revision", "asunto_resumen", "ultimo_email"]
    list_filter = ["familia", "grupo", "estado", "revision"]
    search_fields = ["id_principal", "asunto_resumen", "familia", "remitente_ultimo"]
    list_per_page = 50


@admin.register(TipoActuacion)
class TipoActuacionAdmin(admin.ModelAdmin):
    list_display = ["id_tipo_actuacion", "grupo", "orden", "breve", "cierra"]
    list_filter = ["grupo", "cierra"]
    search_fields = ["breve", "amplio"]
    list_editable = ["orden", "breve", "cierra"]
    ordering = ["grupo", "orden"]


@admin.register(Actuacion)
class ActuacionAdmin(admin.ModelAdmin):
    list_display = ["id_actuacion", "id_tipo_actuacion", "fecha_hora", "breve", "cierra", "id_mensaje", "id_user"]
    list_filter = ["cierra", "fecha_hora"]
    search_fields = ["breve", "amplio"]
    list_select_related = ["id_tipo_actuacion", "id_user", "id_mensaje"]
    ordering = ["-fecha_hora"]
