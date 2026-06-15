from __future__ import annotations

import json
import random
from typing import Any, cast

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db import models
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .email_config import EmailSettings
from .forms import (
    EmailConfigForm,
    PasswordResetForm,
    PasswordResetRequestForm,
    ProfileForm,
    SignupForm,
    VerificationForm,
)
from .models import Mensaje, PasswordResetToken, TableConfig, User

from .table_manager import (
    build_table_context,
    list_user_configs,
    paginate_queryset,
    tables,
)


# ── Helpers ──────────────────────────────────────────────────────


def _send_email_with_config(subject: str, message: str, recipient: str) -> None:
    """Send email using the saved SMTP config or fallback to Django settings."""
    from django.conf import settings as django_settings

    email_settings = EmailSettings.load()
    default_from = getattr(django_settings, "DEFAULT_FROM_EMAIL", "noreply@mailseguridad.local")

    if email_settings.is_testable():
        from django.core.mail.backends.smtp import EmailBackend
        from django.core.mail import EmailMessage

        if email_settings.encryption_type == "ssl_tls":
            use_tls, use_ssl = False, True
        elif email_settings.encryption_type == "starttls":
            use_tls, use_ssl = True, False
        else:
            use_tls, use_ssl = False, False

        backend = EmailBackend(
            host=email_settings.host,
            port=email_settings.port,
            username=email_settings.username,
            password=email_settings.get_password(),
            use_tls=use_tls,
            use_ssl=use_ssl,
            fail_silently=False,
        )
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=email_settings.from_email or default_from,
            to=[recipient],
            connection=backend,
        )
        email.send(fail_silently=False)
    else:
        send_mail(subject, message, default_from, [recipient])


# ── Core views ───────────────────────────────────────────────────


def home_view(request: HttpRequest) -> HttpResponse:
    user = cast(Any, request).user
    return redirect("menu" if user.is_authenticated else "accounts_login")


def health_view(request: HttpRequest) -> HttpResponse:
    return HttpResponse(b"ok")


@login_required
def menu_view(request: HttpRequest) -> HttpResponse:
    total_mensajes = Mensaje.objects.count()
    familias = (
        Mensaje.objects.values("familia")
        .exclude(familia__isnull=True)
        .exclude(familia="")
        .annotate(total=models.Count("id"))
        .order_by("-total")
    )
    revisiones = (
        Mensaje.objects.values("revision")
        .exclude(revision__isnull=True)
        .exclude(revision="")
        .annotate(total=models.Count("id"))
        .order_by("-revision")
    )
    user = cast(Any, request).user
    is_admin = user.is_superuser or getattr(user, "rol", None) == User.Rol.ADMINISTRADOR
    return render(request, "menu.html", {
        "total_mensajes": total_mensajes,
        "familias": familias,
        "revisiones": revisiones,
        "is_admin": is_admin,
    })


def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect("accounts_login")


# ── Signup ───────────────────────────────────────────────────────


def signup_view(request: HttpRequest) -> HttpResponse:
    """Two-step signup: (1) form, (2) email verification code."""
    # Step 2 — verify code
    if request.method == "POST" and "verification_code" in request.POST:
        pending = request.session.get("pending_signup")
        if not pending:
            messages.error(request, "La sesión ha expirado. Vuelve a iniciar el registro.")
            return redirect("signup")

        vform = VerificationForm(request.POST)
        if vform.is_valid():
            if vform.cleaned_data["code"] == pending["code"]:
                user = User.objects.create_user(
                    username=pending["username"],
                    email=pending["email"],
                    password=pending["password"],
                )
                user.rol = User.Rol.USUARIO_NORMAL
                user.save()
                del request.session["pending_signup"]
                authed = authenticate(
                    request,
                    username=pending["username"],
                    password=pending["password"],
                )
                if authed:
                    login(request, authed)
                messages.success(
                    request, f"¡Bienvenido, {user.username}! Tu cuenta ha sido creada."
                )
                return redirect("menu")
            else:
                vform.add_error("code", "El código de verificación no es correcto.")

        return render(request, "seguridad/signup.html", {
            "signup_form": SignupForm(),
            "verification_form": vform,
            "step": 2,
            "email": pending.get("email", ""),
        })

    # Step 1 — submit registration
    if request.method == "POST":
        sform = SignupForm(request.POST)
        if sform.is_valid():
            code = f"{random.randint(0, 99999999):08d}"
            request.session["pending_signup"] = {
                "username": sform.cleaned_data["username"],
                "email": sform.cleaned_data["email"],
                "password": sform.cleaned_data["password1"],
                "code": code,
            }
            subject = "MailSeguridad — Código de verificación"
            message = (
                f"Hola {sform.cleaned_data['username']},\n\n"
                f"Tu código de verificación para MailSeguridad es:\n\n"
                f"   {code}\n\n"
                f"Introduce este código en la pantalla de verificación para activar tu cuenta.\n\n"
                f"Si no has solicitado este registro, ignora este mensaje."
            )
            try:
                _send_email_with_config(subject, message, sform.cleaned_data["email"])
            except Exception as exc:
                messages.warning(request, f"No se ha podido enviar el correo: {exc}")

            return render(request, "seguridad/signup.html", {
                "signup_form": SignupForm(),
                "verification_form": VerificationForm(),
                "step": 2,
                "email": sform.cleaned_data["email"],
            })
        else:
            return render(request, "seguridad/signup.html", {
                "signup_form": sform,
                "verification_form": None,
                "step": 1,
            })

    return render(request, "seguridad/signup.html", {
        "signup_form": SignupForm(),
        "verification_form": None,
        "step": 1,
    })


# ── Password reset ───────────────────────────────────────────────


def password_reset_request(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = None

            if user is not None:
                import uuid

                token = str(uuid.uuid4())
                PasswordResetToken.objects.create(token=token, usuario=user)

                reset_url = request.build_absolute_uri(f"/password_reset/{token}/")
                subject = "MailSeguridad — Restablecimiento de contraseña"
                message = (
                    f"Hola {user.username},\n\n"
                    f"Has solicitado restablecer tu contraseña de MailSeguridad.\n\n"
                    f"Para crear una nueva contraseña, visita el siguiente enlace:\n\n"
                    f"   {reset_url}\n\n"
                    f"Este enlace es válido durante "
                    f"{settings.PASSWORD_RESET_TIMEOUT_MINUTES} minutos.\n\n"
                    f"Si no has solicitado este restablecimiento, ignora este mensaje."
                )
                try:
                    _send_email_with_config(subject, message, email)
                except Exception as exc:
                    messages.warning(
                        request, f"No se ha podido enviar el correo: {exc}"
                    )

            messages.success(
                request,
                "Si el correo está registrado, recibirás un enlace de restablecimiento.",
            )
            return redirect("accounts_login")

        return render(request, "seguridad/password_reset_request.html", {"form": form})

    return render(request, "seguridad/password_reset_request.html", {
        "form": PasswordResetRequestForm(),
    })


def password_reset_confirm(request: HttpRequest, token: str) -> HttpResponse:
    try:
        reset = PasswordResetToken.objects.get(token=token, used=False)
    except PasswordResetToken.DoesNotExist:
        return render(request, "seguridad/password_reset_invalid.html", status=404)

    if reset.is_expired():
        reset.delete()
        return render(
            request,
            "seguridad/password_reset_invalid.html",
            {"expired": True},
            status=410,
        )

    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data["password1"]
            user = reset.usuario
            user.set_password(password)
            user.save()
            reset.delete()
            messages.success(
                request, "Contraseña restablecida correctamente. Inicia sesión."
            )
            return redirect("accounts_login")
        return render(request, "seguridad/password_reset_confirm.html", {
            "form": form,
            "token": token,
            "username": reset.usuario.username,
        })

    form = PasswordResetForm()
    return render(request, "seguridad/password_reset_confirm.html", {
        "form": form,
        "token": token,
        "username": reset.usuario.username,
    })


# ── Profile ──────────────────────────────────────────────────────


@login_required
def profile_view(request: HttpRequest) -> HttpResponse:
    user = cast(Any, request).user
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect("menu")
    else:
        form = ProfileForm(instance=user)
    return render(request, "seguridad/profile_form.html", {"form": form})


# ── Email configuration (admin only) ─────────────────────────────


@login_required
def email_config_view(request: HttpRequest) -> HttpResponse:
    user = cast(Any, request).user
    is_admin = user.is_superuser or getattr(user, "rol", None) == User.Rol.ADMINISTRADOR
    if not is_admin:
        raise PermissionDenied("Solo los administradores pueden configurar el email.")

    settings = EmailSettings.load()
    test_ok = False
    test_error_detail = None

    if request.method == "POST":
        form = EmailConfigForm(request.POST, settings=settings)
        if form.is_valid():
            new_settings = form.to_settings()
            new_settings.save()
            settings = new_settings
            test_recipient = form.cleaned_data.get("test_recipient")
            if "test_email" in request.POST and test_recipient:
                try:
                    _send_email_with_config(
                        "MailSeguridad — Correo de prueba",
                        "Este mensaje confirma que la configuración de email funciona correctamente.\n\nSaludos.",
                        test_recipient,
                    )
                    test_ok = True
                    messages.success(
                        request,
                        f"Correo de prueba enviado correctamente a {test_recipient}.",
                    )
                except RuntimeError as exc:
                    messages.error(request, str(exc))
                except Exception as exc:
                    messages.error(
                        request, f"Error inesperado al enviar el correo de prueba: {exc}"
                    )
            else:
                messages.success(request, "Configuración de email guardada.")
        else:
            messages.error(request, "Corrige los errores del formulario.")
    else:
        form = EmailConfigForm(settings=settings)

    return render(request, "seguridad/email_config.html", {
        "form": form,
        "settings": settings,
        "test_ok": test_ok,
        "test_error_detail": test_error_detail,
    })


# ── Mensajes list ────────────────────────────────────────────────


@login_required
def mensajes_list_view(request: HttpRequest) -> HttpResponse:
    user = cast(Any, request).user

    # ── Search ────────────────────────────────────────────────
    search = request.GET.get("q", "").strip()
    qs = Mensaje.objects.all()
    if search:
        qs = qs.filter(
            Q(id_principal__icontains=search)
            | Q(asunto_resumen__icontains=search)
            | Q(familia__icontains=search)
            | Q(grupo__icontains=search)
            | Q(remitente_ultimo__icontains=search)
            | Q(estado__icontains=search)
            | Q(revision__icontains=search)
        )

    # ── Table config ──────────────────────────────────────────
    cfg = tables["mensajes_list"]
    table_ctx = build_table_context(request, user, cfg)
    sort_spec = table_ctx["sort_spec"]
    if sort_spec:
        order = [
            f"-{s['field']}" if s["direction"] == "desc" else s["field"]
            for s in sort_spec
        ]
        qs = qs.order_by(*order)
    else:
        qs = qs.order_by("-ultimo_email")

    # ── Pagination ────────────────────────────────────────────
    mensajes, page_obj, is_paginated = paginate_queryset(
        request, qs, cfg.paginate_by
    )

    return render(request, "seguridad/mensajes_list.html", {
        "mensajes": mensajes,
        "search": search,
        "page_obj": page_obj,
        "is_paginated": is_paginated,
        **table_ctx,
    })


# ── TableConfig API ──────────────────────────────────────────────


@login_required
@require_http_methods(["GET"])
def table_config_list_api(request: HttpRequest) -> JsonResponse:
    menu_option = request.GET.get("menu_option", "")
    if not menu_option:
        return JsonResponse({"error": "menu_option is required"}, status=400)
    configs = list_user_configs(request.user, menu_option)
    return JsonResponse({"configs": configs})


@login_required
@require_http_methods(["POST"])
def table_config_save_api(request: HttpRequest) -> JsonResponse:
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    menu_option = data.get("menu_option", "")
    name = data.get("name", "default")
    selected_fields = data.get("selected_fields", [])
    sort_order = data.get("sort_order")
    size_columns = data.get("size_columns")

    if not menu_option:
        return JsonResponse({"error": "menu_option is required"}, status=400)

    config, created = TableConfig.objects.update_or_create(
        usuario=request.user,
        menu_option=menu_option,
        name=name,
        defaults={
            "selected_fields": selected_fields,
            "sort_order": sort_order,
            "size_columns": size_columns,
        },
    )
    return JsonResponse({"status": "ok", "created": created, "id": config.pk})


@login_required
@require_http_methods(["POST"])
def table_config_delete_api(request: HttpRequest) -> JsonResponse:
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    config_id = data.get("id")
    if not config_id:
        return JsonResponse({"error": "id is required"}, status=400)

    try:
        config = TableConfig.objects.get(pk=config_id, usuario=request.user)
    except TableConfig.DoesNotExist:
        return JsonResponse({"error": "Config not found"}, status=404)

    config.delete()
    return JsonResponse({"status": "ok"})


# ── Mensaje detail (view / edit / delete) ──────────────────────────


@login_required
def mensaje_detail_view(request: HttpRequest, pk: int) -> HttpResponse:
    """View, edit, or delete a single mensaje record."""
    mensaje = get_object_or_404(Mensaje, pk=pk)

    # If delete was requested
    if request.method == "POST" and request.POST.get("_method") == "delete":
        user = cast(Any, request).user
        is_admin = user.is_superuser or getattr(user, "rol", None) == User.Rol.ADMINISTRADOR
        if not is_admin:
            raise PermissionDenied("Solo los administradores pueden eliminar mensajes.")
        mensaje.delete()
        messages.success(request, f"Mensaje {pk} eliminado correctamente.")
        return redirect("mensajes_list")

    # If save was requested
    if request.method == "POST" and request.POST.get("_method") == "save":
        # Map POST field names to model fields
        text_fields = [
            "familia", "id_principal", "grupo", "filtro", "asunto_resumen",
            "estado", "accion_tipo", "inc_relacionado", "cs_relacionado",
            "crq_asociado", "ventana_o_fecha", "ultimo_email",
            "remitente_ultimo", "message_ids", "outlook_urls", "revision",
        ]
        for fld in text_fields:
            val = request.POST.get(fld, "").strip()
            setattr(mensaje, fld, val or None)

        num_val = request.POST.get("num_mensajes", "").strip()
        mensaje.num_mensajes = int(num_val) if num_val else None

        mensaje.save()
        messages.success(request, f"Mensaje {pk} actualizado correctamente.")
        return redirect("mensaje_detail", pk=pk)

    # Get field labels from table_manager
    from .table_manager import tables

    cfg = tables.get("mensajes_list")
    field_labels = dict(cfg.columns) if cfg else {}

    # Ordered list of editable fields (excluding id)
    editable_fields = [
        "familia", "id_principal", "grupo", "filtro", "asunto_resumen",
        "estado", "accion_tipo", "inc_relacionado", "cs_relacionado",
        "crq_asociado", "ventana_o_fecha", "ultimo_email",
        "remitente_ultimo", "num_mensajes", "message_ids", "outlook_urls",
        "revision",
    ]
    user = cast(Any, request).user
    is_admin = user.is_superuser or getattr(user, "rol", None) == User.Rol.ADMINISTRADOR

    return render(request, "seguridad/mensaje_detail.html", {
        "mensaje": mensaje,
        "field_labels": field_labels,
        "editable_fields": editable_fields,
        "is_admin": is_admin,
    })


# ── Clear mensajes (admin only) ────────────────────────────────────


@login_required
@require_http_methods(["POST"])
def clear_mensajes_view(request: HttpRequest) -> HttpResponse:
    """Delete ALL records from the Mensajes table. Admin only."""
    user = cast(Any, request).user
    is_admin = user.is_superuser or getattr(user, "rol", None) == User.Rol.ADMINISTRADOR
    if not is_admin:
        raise PermissionDenied("Solo los administradores pueden borrar mensajes.")

    count, _ = Mensaje.objects.all().delete()
    messages.success(request, f"Se han borrado {count} mensajes de la base de datos.")
    return redirect("menu")

