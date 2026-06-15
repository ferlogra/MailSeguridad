from __future__ import annotations

from django.contrib import admin

from .models import Mensaje, PasswordResetToken, TableConfig, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["username", "email", "rol", "is_active", "fecha_alta"]
    list_filter = ["rol", "is_active"]


@admin.register(TableConfig)
class TableConfigAdmin(admin.ModelAdmin):
    list_display = ["usuario", "menu_option", "name"]


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ["usuario", "created_at", "used"]


@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    list_display = ["id", "id_principal", "familia", "asunto_resumen", "ultimo_email"]
    search_fields = ["id_principal", "asunto_resumen"]
