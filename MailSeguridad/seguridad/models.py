from __future__ import annotations

import base64
import json
from datetime import timedelta

from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


# ── App version ──────────────────────────────────────────────────


# ── User ─────────────────────────────────────────────────────────


class User(AbstractUser):
    class Rol(models.TextChoices):
        ADMINISTRADOR = "administrador", "administrador"
        USUARIO_NORMAL = "usuario normal", "usuario normal"

    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=32, blank=True)
    fecha_alta = models.DateTimeField(auto_now_add=True)
    fecha_baja = models.DateTimeField(null=True, blank=True)
    rol = models.CharField(
        max_length=32, choices=Rol.choices, default=Rol.USUARIO_NORMAL
    )


# ── Password reset token ───────────────────────────────────────


class PasswordResetToken(models.Model):
    """One-time password reset token with configurable validity."""

    token = models.CharField(max_length=36, unique=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    def is_expired(self) -> bool:
        timeout = getattr(settings, "PASSWORD_RESET_TIMEOUT_MINUTES", 10)
        return timezone.now() > self.created_at + timedelta(minutes=timeout)

    def is_valid(self) -> bool:
        return not self.used and not self.is_expired()

    def __str__(self) -> str:
        return f"Reset {self.token[:8]}… — {self.usuario.username}"


# ── TableConfig (Configuraciones de tabla) ──────────────────────


class TableConfig(models.Model):
    """Saved column, sort, and size configuration for a table view."""

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    menu_option = models.CharField(
        max_length=64,
        help_text="Identificador de la opción del menú (mensajes_list, etc.)",
    )
    name = models.CharField(
        max_length=64,
        help_text="Nombre de la configuración. 'default' se carga automáticamente.",
    )
    selected_fields = models.JSONField(
        default=list, help_text="Lista ordenada de campos visibles"
    )
    sort_order = models.JSONField(
        null=True, blank=True, help_text="Orden de registros (ej. ['-received', 'family'])"
    )
    size_columns = models.JSONField(
        null=True, blank=True, help_text="Anchos en píxeles por columna"
    )

    class Meta:
        unique_together = [("usuario", "menu_option", "name")]
        verbose_name = "Configuración de tabla"
        verbose_name_plural = "Configuraciones de tabla"

    def __str__(self) -> str:
        return f"[{self.menu_option}] {self.name} — {self.usuario.username}"


# ── Mensajes (from external mail_Seguridad.db) ──────────────────


class Mensaje(models.Model):
    """Modelo que mapea la tabla Mensajes de mail_Seguridad.db.

    Esta tabla es creada y poblada por el script get-Mail.ps1.
    Django la maneja como solo-lectura a través de una segunda base de datos.
    """

    id = models.BigAutoField(primary_key=True, db_column="Id")
    familia = models.TextField(null=True, blank=True, db_column="Familia")
    id_principal = models.TextField(null=True, blank=True, db_column="ID_principal")
    grupo = models.TextField(null=True, blank=True, db_column="Grupo")
    filtro = models.TextField(null=True, blank=True, db_column="Filtro")
    asunto_resumen = models.TextField(null=True, blank=True, db_column="Asunto_resumen")
    estado = models.TextField(null=True, blank=True, db_column="Estado")
    accion_tipo = models.TextField(null=True, blank=True, db_column="Accion_tipo")
    inc_relacionado = models.TextField(null=True, blank=True, db_column="INC_relacionado")
    cs_relacionado = models.TextField(null=True, blank=True, db_column="CS_relacionado")
    crq_asociado = models.TextField(null=True, blank=True, db_column="CRQ_asociado")
    ventana_o_fecha = models.TextField(null=True, blank=True, db_column="Ventana_o_fecha")
    ultimo_email = models.TextField(null=True, blank=True, db_column="Ultimo_email_2026")
    remitente_ultimo = models.TextField(null=True, blank=True, db_column="Remitente_ultimo")
    num_mensajes = models.IntegerField(null=True, blank=True, db_column="Num_Mensajes")
    message_ids = models.TextField(null=True, blank=True, db_column="MessageIds")
    outlook_urls = models.TextField(null=True, blank=True, db_column="OutlookUrls")
    revision = models.TextField(null=True, blank=True, db_column="Revision")
    id_actuacion = models.IntegerField(default=0, db_column="IdActuacion")
    body = models.TextField(null=True, blank=True, db_column="Body")
    is_body_html = models.BooleanField(null=True, blank=True, db_column="IsBodyHTML")
    to = models.TextField(null=True, blank=True, db_column="To")
    cc = models.TextField(null=True, blank=True, db_column="Cc")
    user = models.TextField(null=True, blank=True, db_column="User")

    class Meta:
        managed = False
        db_table = "Mensajes"
        verbose_name = "Mensaje"
        verbose_name_plural = "Mensajes"
        ordering = ["-id"]

    def __str__(self) -> str:
        return f"{self.id_principal or self.asunto_resumen or '(sin ID)'}"


class TipoActuacion(models.Model):
    """Catálogo de tipos de actuación."""

    id_tipo_actuacion = models.AutoField(primary_key=True, db_column="IdTipoActuacion")
    grupo = models.IntegerField(db_column="Grupo", default=0)
    orden = models.PositiveSmallIntegerField(db_column="Orden", default=0)
    breve = models.CharField(max_length=256, db_column="Breve")
    amplio = models.TextField(max_length=8192, blank=True, default="", db_column="Amplio")
    cierra = models.BooleanField(default=False, db_column="Cierra")

    class Meta:
        managed = True
        db_table = "TipoActuaciones"
        verbose_name = "Tipo de actuación"
        verbose_name_plural = "Tipos de actuación"
        ordering = ["grupo", "orden"]

    def __str__(self) -> str:
        return f"[{self.grupo}.{self.orden}] {self.breve}"


class Actuacion(models.Model):
    """Registro de actuaciones sobre mensajes."""

    id_actuacion = models.AutoField(primary_key=True, db_column="IdActuacion")
    id_tipo_actuacion = models.ForeignKey(
        TipoActuacion,
        on_delete=models.PROTECT,
        db_column="IdTipoActuacion",
        verbose_name="Tipo de actuación",
    )
    id_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="IdUser",
        verbose_name="Usuario",
    )
    fecha_hora = models.DateTimeField(
        default=timezone.now,
        db_column="FechaHora",
        verbose_name="Fecha y hora",
    )
    breve = models.CharField(max_length=256, db_column="Breve", verbose_name="Breve")
    amplio = models.TextField(
        max_length=8192, blank=True, default="", db_column="Amplio", verbose_name="Amplio"
    )
    cierra = models.BooleanField(default=False, db_column="Cierra", verbose_name="Cierra")
    id_mensaje = models.ForeignKey(
        Mensaje,
        on_delete=models.CASCADE,
        null=True, blank=True,
        db_column="IdMensaje",
        verbose_name="Mensaje",
    )

    class Meta:
        managed = True
        db_table = "Actuaciones"
        verbose_name = "Actuación"
        verbose_name_plural = "Actuaciones"
        ordering = ["-fecha_hora"]

    def __str__(self) -> str:
        return f"{self.fecha_hora:%d/%m/%Y %H:%M} — {self.breve[:60]}"
