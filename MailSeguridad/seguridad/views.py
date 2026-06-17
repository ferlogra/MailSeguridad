from __future__ import annotations

import json
import os
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
    CustomPasswordChangeForm,
    EmailConfigForm,
    PasswordResetForm,
    PasswordResetRequestForm,
    ProfileForm,
    SignupForm,
    VerificationForm,
)
from .models import Actuacion, Mensaje, PasswordResetToken, TableConfig, TipoActuacion, User

from .table_manager import (
    _parse_sort,
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


@login_required
@require_http_methods(["GET", "POST"])
def password_change_view(request: HttpRequest) -> HttpResponse:
    user = cast(Any, request).user
    if request.method == "POST":
        form = CustomPasswordChangeForm(request.POST, user=user)
        if form.is_valid():
            user.set_password(form.cleaned_data["new_password1"])
            user.save()
            messages.success(request, "Contrasena cambiada correctamente.")
            return redirect("profile")
        return render(request, "seguridad/password_change_form.html", {"form": form})

    form = CustomPasswordChangeForm(user=user)
    return render(request, "seguridad/password_change_form.html", {"form": form})


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

    # ── Extract filters ──
    search = request.GET.get("q", "").strip()
    familia = request.GET.get("familia", "").strip()
    grupo_val = request.GET.get("grupo", "").strip()  # avoid shadowing model name
    remitente_ultimo = request.GET.get("remitente_ultimo", "").strip()
    estado = request.GET.get("estado", "").strip()
    revision = request.GET.get("revision", "").strip()
    fecha_desde = request.GET.get("fecha_desde", "").strip()
    fecha_hasta = request.GET.get("fecha_hasta", "").strip()
    field_filter = request.GET.get("field", "").strip()
    field_value = request.GET.get("value", "").strip()

    # ── Base queryset ──
    qs = Mensaje.objects.all()

    # ── Full-text search (OR) ──
    if search:
        qs = qs.filter(
            Q(id_principal__icontains=search)
            | Q(asunto_resumen__icontains=search)
            | Q(familia__icontains=search)
            | Q(grupo__icontains=search)
            | Q(remitente_ultimo__icontains=search)
            | Q(estado__icontains=search)
            | Q(revision__icontains=search)
            | Q(to__icontains=search)
            | Q(cc__icontains=search)
            | Q(user__icontains=search)
            | Q(internet_message_id__icontains=search)
            | Q(cs_relacionado__icontains=search)
        )

    # ── Advanced filters (AND) ──
    if familia:
        qs = qs.filter(familia__iexact=familia)
    if grupo_val:
        qs = qs.filter(grupo__iexact=grupo_val)
    if remitente_ultimo:
        qs = qs.filter(remitente_ultimo__icontains=remitente_ultimo)
    if estado:
        qs = qs.filter(estado__iexact=estado)
    if revision:
        qs = qs.filter(revision__iexact=revision)
    if fecha_desde:
        qs = qs.filter(ultimo_email__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(ultimo_email__lte=fecha_hasta)
    if field_filter and field_value:
        # ── Pre-filter by field=value (reuses mensajes list with existing features) ──
        ALLOWED_FIELDS = frozenset({
            "to", "internet_message_id", "conversation_id",
            "cs_relacionado", "inc_relacionado",
        })
        if field_filter in ALLOWED_FIELDS:
            filter_key = field_filter + "__exact"
            qs = qs.filter(**{filter_key: field_value})

    # ── Distinct values for dropdowns ──
    familias_list = (
        Mensaje.objects.values_list("familia", flat=True)
        .exclude(familia__isnull=True).exclude(familia="")
        .distinct().order_by("familia")
    )
    grupos_list = (
        Mensaje.objects.values_list("grupo", flat=True)
        .exclude(grupo__isnull=True).exclude(grupo="")
        .distinct().order_by("grupo")
    )
    estados_list = (
        Mensaje.objects.values_list("estado", flat=True)
        .exclude(estado__isnull=True).exclude(estado="")
        .distinct().order_by("estado")
    )
    revisiones_list = (
        Mensaje.objects.values_list("revision", flat=True)
        .exclude(revision__isnull=True).exclude(revision="")
        .distinct().order_by("revision")
    )

    # ── Build base query string (preserve filters for sort/pagination) ──
    import urllib.parse
    params = request.GET.copy()
    params.pop("page", None)
    params.pop("sort", None)
    base_query_string = params.urlencode()

    # ── Table config ──
    cfg = tables["mensajes_list"]
    table_ctx = build_table_context(request, user, cfg, base_query_string=base_query_string)
    sort_spec = table_ctx["sort_spec"]
    if sort_spec:
        order = [
            f"-{s['field']}" if s["direction"] == "desc" else s["field"]
            for s in sort_spec
        ]
        qs = qs.order_by(*order)
    else:
        qs = qs.order_by("-ultimo_email")

    # ── Pagination ──
    mensajes, page_obj, is_paginated = paginate_queryset(request, qs, cfg.paginate_by)

    return render(request, "seguridad/mensajes_list.html", {
        "mensajes": mensajes,
        "page_title": "Mensajes",
        "search": search,
        "familia": familia, "grupo": grupo_val,
        "remitente_ultimo": remitente_ultimo,
        "estado": estado, "revision": revision,
        "fecha_desde": fecha_desde, "fecha_hasta": fecha_hasta,
        "familias": familias_list, "grupos": grupos_list,
        "estados": estados_list, "revisiones": revisiones_list,
        "base_query_string": base_query_string,
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
            "body", "to", "cc", "user",
            "internet_message_headers", "internet_message_id", "conversation_id",
        ]
        for fld in text_fields:
            val = request.POST.get(fld, "").strip()
            setattr(mensaje, fld, val or None)

        num_val = request.POST.get("num_mensajes", "").strip()
        mensaje.num_mensajes = int(num_val) if num_val else None

        # Boolean field
        mensaje.is_body_html = request.POST.get("is_body_html") == "on"

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
        "revision", "is_body_html", "to", "cc", "user",
        "internet_message_headers", "internet_message_id", "conversation_id",
        "body",
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


# ── Tipo Actuaciones ─────────────────────────────────────────────


@login_required
def tipoactuaciones_list_view(request: HttpRequest) -> HttpResponse:
    """List/catalog of TipoActuacion records."""
    user = cast(Any, request).user
    search = request.GET.get("q", "").strip()
    qs = TipoActuacion.objects.all()
    if search:
        qs = qs.filter(
            Q(breve__icontains=search)
            | Q(amplio__icontains=search)
            | Q(grupo__icontains=search)
        )
    cfg = tables["tipoactuaciones_list"]
    table_ctx = build_table_context(request, user, cfg)
    sort_spec = table_ctx["sort_spec"]
    if sort_spec:
        order = [
            f"-{s['field']}" if s["direction"] == "desc" else s["field"]
            for s in sort_spec
        ]
        qs = qs.order_by(*order)
    else:
        qs = qs.order_by("grupo", "orden")
    records, page_obj, is_paginated = paginate_queryset(request, qs, cfg.paginate_by)
    return render(request, "seguridad/tipoactuaciones_list.html", {
        "records": records,
        "search": search,
        "page_obj": page_obj,
        "is_paginated": is_paginated,
        **table_ctx,
    })


@login_required
def tipoactuacion_create_view(request: HttpRequest) -> HttpResponse:
    """Create a new TipoActuacion record."""
    if request.method == "POST":
        obj = TipoActuacion(
            grupo=int(request.POST.get("grupo", 0)),
            orden=int(request.POST.get("orden", 0)),
            breve=request.POST.get("breve", "").strip(),
            amplio=request.POST.get("amplio", "").strip(),
            cierra=request.POST.get("cierra") == "on",
        )
        obj.save()
        messages.success(request, f"Tipo de actuación {obj.pk} creado.")
        return redirect("tipoactuacion_detail", pk=obj.pk)
    from .table_manager import tables as _t
    cfg = _t.get("tipoactuaciones_list")
    field_labels = dict(cfg.columns) if cfg else {}
    obj = TipoActuacion(grupo=0, orden=0, breve="", amplio="", cierra=False)
    user = cast(Any, request).user
    is_admin = user.is_superuser or getattr(user, "rol", None) == User.Rol.ADMINISTRADOR
    return render(request, "seguridad/tipoactuacion_detail.html", {
        "obj": obj,
        "field_labels": field_labels,
        "is_admin": is_admin,
        "is_new": True,
    })


@login_required
def tipoactuacion_detail_view(request: HttpRequest, pk: int) -> HttpResponse:
    """View/edit a single TipoActuacion record."""
    obj = get_object_or_404(TipoActuacion, pk=pk)
    if request.method == "POST":
        if request.POST.get("_method") == "delete":
            obj.delete()
            messages.success(request, f"Tipo de actuación {pk} eliminado.")
            return redirect("tipoactuaciones_list")
        # save
        obj.grupo = int(request.POST.get("grupo", 0))
        obj.orden = int(request.POST.get("orden", 0))
        obj.breve = request.POST.get("breve", "").strip()
        obj.amplio = request.POST.get("amplio", "").strip()
        obj.cierra = request.POST.get("cierra") == "on"
        obj.save()
        messages.success(request, f"Tipo de actuación {pk} actualizado.")
        return redirect("tipoactuacion_detail", pk=pk)
    from .table_manager import tables as _t
    cfg = _t.get("tipoactuaciones_list")
    field_labels = dict(cfg.columns) if cfg else {}
    user = cast(Any, request).user
    is_admin = user.is_superuser or getattr(user, "rol", None) == User.Rol.ADMINISTRADOR
    return render(request, "seguridad/tipoactuacion_detail.html", {
        "obj": obj,
        "field_labels": field_labels,
        "is_admin": is_admin,
    })


# ── Actuaciones ──────────────────────────────────────────────────


@login_required
def actuaciones_list_view(request: HttpRequest) -> HttpResponse:
    """List of Actuacion records."""
    user = cast(Any, request).user
    search = request.GET.get("q", "").strip()
    qs = Actuacion.objects.select_related("id_tipo_actuacion", "id_user").all()
    if search:
        qs = qs.filter(
            Q(breve__icontains=search)
            | Q(amplio__icontains=search)
            | Q(id_tipo_actuacion__breve__icontains=search)
        )
    cfg = tables["actuaciones_list"]
    table_ctx = build_table_context(request, user, cfg)
    sort_spec = table_ctx["sort_spec"]
    if sort_spec:
        order = [
            f"-{s['field']}" if s["direction"] == "desc" else s["field"]
            for s in sort_spec
        ]
        qs = qs.order_by(*order)
    else:
        qs = qs.order_by("-fecha_hora")
    records, page_obj, is_paginated = paginate_queryset(request, qs, cfg.paginate_by)
    return render(request, "seguridad/actuaciones_list.html", {
        "records": records,
        "search": search,
        "page_obj": page_obj,
        "is_paginated": is_paginated,
        **table_ctx,
    })


@login_required
def actuacion_create_view(request: HttpRequest) -> HttpResponse:
    """Create a new Actuacion record."""
    if request.method == "POST":
        tipo_pk = request.POST.get("id_tipo_actuacion", "").strip()
        id_tipo = get_object_or_404(TipoActuacion, pk=int(tipo_pk)) if tipo_pk else None
        from django.utils import timezone as tz
        fecha_str = request.POST.get("fecha_hora", "").strip()
        if fecha_str:
            from datetime import datetime
            try:
                fecha = datetime.strptime(fecha_str, "%Y-%m-%dT%H:%M")
            except ValueError:
                fecha = tz.now()
        else:
            fecha = tz.now()
        obj = Actuacion(
            id_tipo_actuacion=id_tipo,
            id_user=request.user,
            fecha_hora=fecha,
            breve=request.POST.get("breve", "").strip(),
            amplio=request.POST.get("amplio", "").strip(),
            cierra=request.POST.get("cierra") == "on",
        )
        obj.save()
        messages.success(request, f"Actuación {obj.pk} creada.")
        return redirect("actuacion_detail", pk=obj.pk)
    from .table_manager import tables as _t
    cfg = _t.get("actuaciones_list")
    field_labels = dict(cfg.columns) if cfg else {}
    tipos = TipoActuacion.objects.all().order_by("grupo", "orden")
    user = cast(Any, request).user
    is_admin = user.is_superuser or getattr(user, "rol", None) == User.Rol.ADMINISTRADOR
    return render(request, "seguridad/actuacion_detail.html", {
        "obj": None,
        "field_labels": field_labels,
        "tipos": tipos,
        "is_admin": is_admin,
        "is_new": True,
    })


# ── Actuaciones API ──────────────────────────────────────────────


@login_required
def actuaciones_por_mensaje_api(request: HttpRequest, mensaje_id: str) -> JsonResponse:
    """Return JSON list of actuaciones for a mensaje."""
    qs = Actuacion.objects.filter(mensaje=mensaje_id).select_related("id_tipo_actuacion", "id_user").order_by("-fecha_hora")
    data = [
        {
            "id_actuacion": a.id_actuacion,
            "id_tipo_actuacion": a.id_tipo_actuacion_id,
            "tipo_breve": a.id_tipo_actuacion.breve if a.id_tipo_actuacion else "",
            "fecha_hora": a.fecha_hora.isoformat() if a.fecha_hora else None,
            "breve": a.breve,
            "amplio": a.amplio,
            "cierra": a.cierra,
            "username": a.id_user.username if a.id_user else "",
        }
        for a in qs
    ]
    return JsonResponse({"actuaciones": data})


@login_required
@require_http_methods(["POST"])
def actuacion_create_api(request: HttpRequest) -> JsonResponse:
    """Create an actuacion via JSON API."""
    from django.utils import timezone as tz
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    tipo_pk = body.get("id_tipo_actuacion")
    if not tipo_pk:
        return JsonResponse({"error": "id_tipo_actuacion required"}, status=400)
    tipo = get_object_or_404(TipoActuacion, pk=tipo_pk)
    obj = Actuacion(
        id_tipo_actuacion=tipo,
        id_user=request.user,
        fecha_hora=tz.now(),
        breve=body.get("breve", "").strip(),
        amplio=body.get("amplio", "").strip(),
        cierra=body.get("cierra", False),
        mensaje=body.get("mensaje"),
    )
    obj.save()
    return JsonResponse({"status": "ok", "id": obj.pk})


@login_required
@require_http_methods(["POST"])
def actuacion_delete_api(request: HttpRequest, pk: int) -> JsonResponse:
    """Delete an actuacion."""
    obj = get_object_or_404(Actuacion, pk=pk)
    obj.delete()
    return JsonResponse({"status": "ok"})


@login_required
@require_http_methods(["POST"])
def actuacion_update_api(request: HttpRequest, pk: int) -> JsonResponse:
    """Update an actuacion via JSON API."""
    obj = get_object_or_404(Actuacion, pk=pk)
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    tipo_pk = body.get("id_tipo_actuacion")
    if tipo_pk:
        obj.id_tipo_actuacion = get_object_or_404(TipoActuacion, pk=tipo_pk)
    from django.utils import timezone as tz
    fecha_str = body.get("fecha_hora", "").strip()
    if fecha_str:
        from datetime import datetime
        try:
            obj.fecha_hora = datetime.strptime(fecha_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            obj.fecha_hora = tz.now()
    obj.breve = body.get("breve", obj.breve).strip()
    obj.amplio = body.get("amplio", obj.amplio).strip()
    obj.cierra = body.get("cierra", obj.cierra)
    obj.id_user = request.user
    obj.save()
    return JsonResponse({"status": "ok", "id": obj.pk})


@login_required
def tipoactuaciones_lista_api(request: HttpRequest) -> JsonResponse:
    """Return JSON list of all TipoActuaciones for dropdowns."""
    tipos = TipoActuacion.objects.all().order_by("grupo", "orden")
    data = [{"id": t.id_tipo_actuacion, "grupo": t.grupo, "orden": t.orden, "breve": t.breve} for t in tipos]
    return JsonResponse({"tipos": data})


@login_required
def actuacion_detail_view(request: HttpRequest, pk: int) -> HttpResponse:
    """View/edit a single Actuacion record."""
    obj = get_object_or_404(Actuacion.objects.select_related("id_tipo_actuacion", "id_user"), pk=pk)
    if request.method == "POST":
        if request.POST.get("_method") == "delete":
            obj.delete()
            messages.success(request, f"Actuación {pk} eliminada.")
            return redirect("actuaciones_list")
        # save
        tipo_pk = request.POST.get("id_tipo_actuacion", "").strip()
        if tipo_pk:
            obj.id_tipo_actuacion = get_object_or_404(TipoActuacion, pk=int(tipo_pk))
        from django.utils import timezone as tz
        fecha_str = request.POST.get("fecha_hora", "").strip()
        if fecha_str:
            from datetime import datetime
            try:
                obj.fecha_hora = datetime.strptime(fecha_str, "%Y-%m-%dT%H:%M")
            except ValueError:
                obj.fecha_hora = tz.now()
        else:
            obj.fecha_hora = tz.now()
        obj.breve = request.POST.get("breve", "").strip()
        obj.amplio = request.POST.get("amplio", "").strip()
        obj.cierra = request.POST.get("cierra") == "on"
        obj.id_user = request.user
        obj.save()
        messages.success(request, f"Actuación {pk} actualizada.")
        return redirect("actuacion_detail", pk=pk)
    from .table_manager import tables as _t
    cfg = _t.get("actuaciones_list")
    field_labels = dict(cfg.columns) if cfg else {}
    tipos = TipoActuacion.objects.all().order_by("grupo", "orden")
    user = cast(Any, request).user
    is_admin = user.is_superuser or getattr(user, "rol", None) == User.Rol.ADMINISTRADOR
    return render(request, "seguridad/actuacion_detail.html", {
        "obj": obj,
        "field_labels": field_labels,
        "tipos": tipos,
        "is_admin": is_admin,
    })


@login_required
def docs_view(request: HttpRequest) -> HttpResponse:
    """View documentation markdown files from the project directories."""
    import glob
    import markdown as md_lib

    # Project root is C:\ps1 (parent of Django project root)
    project_root = settings.BASE_DIR.parent
    md_files = sorted(glob.glob(os.path.join(str(project_root), "**", "*.md"), recursive=True))

    file_list = []
    for fp in md_files:
        rel = os.path.relpath(fp, str(project_root))
        file_list.append({"path": fp, "name": rel})

    selected = request.GET.get("file", "")
    content_html = ""
    if selected:
        matched = [f for f in md_files if os.path.relpath(f, str(project_root)) == selected]
        if matched:
            try:
                with open(matched[0], "r", encoding="utf-8") as fh:
                    raw = fh.read()
                content_html = md_lib.markdown(raw, extensions=["fenced_code", "tables"])
            except Exception:
                content_html = "<p><em>Error al leer el archivo.</em></p>"

    return render(request, "docs.html", {
        "file_list": file_list,
        "selected": selected,
        "content_html": content_html,
    })


@login_required
def actuaciones_tickets_view(request: HttpRequest) -> HttpResponse:
    """Show mensajes with their related actuaciones (flat LEFT JOIN)."""
    from django.db import connection

    # ── Extract filters (same as mensajes_list) ──
    search = request.GET.get("q", "").strip()
    familia = request.GET.get("familia", "").strip()
    grupo_val = request.GET.get("grupo", "").strip()
    remitente_ultimo = request.GET.get("remitente_ultimo", "").strip()
    estado = request.GET.get("estado", "").strip()
    revision = request.GET.get("revision", "").strip()
    fecha_desde = request.GET.get("fecha_desde", "").strip()
    fecha_hasta = request.GET.get("fecha_hasta", "").strip()

    # ── Distinct values for dropdowns ──
    familias_list = list(Mensaje.objects.values_list("familia", flat=True).exclude(familia__isnull=True).exclude(familia="").distinct().order_by("familia"))
    grupos_list = list(Mensaje.objects.values_list("grupo", flat=True).exclude(grupo__isnull=True).exclude(grupo="").distinct().order_by("grupo"))
    estados_list = list(Mensaje.objects.values_list("estado", flat=True).exclude(estado__isnull=True).exclude(estado="").distinct().order_by("estado"))
    revisiones_list = list(Mensaje.objects.values_list("revision", flat=True).exclude(revision__isnull=True).exclude(revision="").distinct().order_by("revision"))

    # ── Build SQL ──
    sql = """
        SELECT m.Id AS id,
               m.Familia AS familia,
               m.ID_principal AS id_principal,
               m.Grupo AS grupo,
               m.Filtro AS filtro,
               m.Asunto_resumen AS asunto_resumen,
               m.Estado AS estado,
               m.Accion_tipo AS accion_tipo,
               m.INC_relacionado AS inc_relacionado,
               m.CS_relacionado AS cs_relacionado,
               m.CRQ_asociado AS crq_asociado,
               m.Ventana_o_fecha AS ventana_o_fecha,
               m.Ultimo_email_2026 AS ultimo_email,
               m.Remitente_ultimo AS remitente_ultimo,
               m.Num_Mensajes AS num_mensajes,
               m.MessageIds AS message_ids,
               m.OutlookUrls AS outlook_urls,
               m.Revision AS revision,
               m.Body AS body,
               m."User" AS "user",
               m.IsBodyHTML AS is_body_html,
               m."To" AS "to",
               m."Cc" AS cc,
               m.InternetMessageHeaders AS internet_message_headers,
               m.InternetMessageId AS internet_message_id,
               m.ConversationId AS conversation_id,
               a.IdActuacion AS act_id,
               t.Breve AS act_tipo,
               a.FechaHora AS act_fecha,
               a.Breve AS act_breve,
               a.Amplio AS act_amplio,
               a.Cierra AS act_cierra,
               u.username AS act_user
        FROM Mensajes m
        LEFT JOIN Actuaciones a ON m.InternetMessageId = a.Mensaje
        LEFT JOIN TipoActuaciones t ON a.IdTipoActuacion = t.IdTipoActuacion
        LEFT JOIN seguridad_user u ON a.IdUser = u.id
        WHERE 1=1
    """

    params = []

    # ── Full-text search ──
    if search:
        sql += """ AND (
            m.ID_principal LIKE ? OR m.Asunto_resumen LIKE ? OR m.Familia LIKE ?
            OR m.Grupo LIKE ? OR m.Remitente_ultimo LIKE ? OR m.Estado LIKE ?
            OR m.Revision LIKE ? OR m."To" LIKE ? OR m."Cc" LIKE ? OR m."User" LIKE ?
            OR m.InternetMessageId LIKE ? OR m.CS_relacionado LIKE ?
            OR a.Breve LIKE ? OR t.Breve LIKE ? OR u.username LIKE ?
        )"""
        like = f"%{search}%"
        params.extend([like] * 15)

    # ── Advanced filters ──
    if familia:
        sql += " AND m.Familia = ?"
        params.append(familia)
    if grupo_val:
        sql += " AND m.Grupo = ?"
        params.append(grupo_val)
    if remitente_ultimo:
        sql += " AND m.Remitente_ultimo LIKE ?"
        params.append(f"%{remitente_ultimo}%")
    if estado:
        sql += " AND m.Estado = ?"
        params.append(estado)
    if revision:
        sql += " AND m.Revision = ?"
        params.append(revision)
    if fecha_desde:
        sql += " AND m.Ultimo_email_2026 >= ?"
        params.append(fecha_desde)
    if fecha_hasta:
        sql += " AND m.Ultimo_email_2026 <= ?"
        params.append(fecha_hasta)

    # ── Execute ──
    # NOTE: Use raw sqlite3 cursor to avoid Django's CursorDebugWrapper.
    # CursorDebugWrapper calls last_executed_query() which does sql % params,
    # but raw SQL uses ? placeholders (not %s like Django ORM), causing
    # "not all arguments converted during string formatting" TypeError
    # when any filter param is set with DEBUG=True.
    raw_cursor = connection.connection.cursor()
    try:
        raw_cursor.execute(sql, params)
        columns = [col[0] for col in raw_cursor.description]
        all_rows = [dict(zip(columns, row)) for row in raw_cursor.fetchall()]
    finally:
        raw_cursor.close()

    # ── Sort ──
    from seguridad.table_manager import tables, build_table_context
    cfg = tables["actuaciones_tickets"]
    sort_raw = request.GET.get("sort", "")
    sort_spec = _parse_sort(sort_raw, cfg.sort_fields) if sort_raw else []

    # Sort in Python (list of dicts)
    for s in reversed(sort_spec):
        reverse = s["direction"] == "desc"
        field = s["field"]
        all_rows.sort(key=lambda r, f=field: (str(r.get(f, "") or "")).lower(), reverse=reverse)

    # ── Paginate ──
    from django.core.paginator import Paginator
    paginator = Paginator(all_rows, cfg.paginate_by)
    page = request.GET.get("page", 1)
    try:
        page_obj = paginator.page(page)
    except Exception:
        page_obj = paginator.page(1)

    # ── Build query string ──
    import urllib.parse
    params_qs = request.GET.copy()
    params_qs.pop("page", None)
    base_qs = params_qs.urlencode()

    table_ctx = build_table_context(request, request.user, cfg, base_query_string=base_qs)

    return render(request, "seguridad/mensajes_list.html", {
        "mensajes": page_obj.object_list,
        "page_obj": page_obj,
        "is_paginated": page_obj.has_other_pages(),
        "page_title": "Actuaciones",
        "search": search,
        "familia": familia,
        "grupo": grupo_val,
        "remitente_ultimo": remitente_ultimo,
        "estado": estado,
        "revision": revision,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "familias": familias_list,
        "grupos": grupos_list,
        "estados": estados_list,
        "revisiones": revisiones_list,
        **table_ctx,
    })


# ── AccionesAuto ─────────────────────────────────────────────────


@login_required
def accionesauto_list_view(request: HttpRequest) -> HttpResponse:
    """List AccionesAuto records."""
    user = cast(Any, request).user
    search = request.GET.get("q", "").strip()
    qs = AccionesAuto.objects.all()
    if search:
        qs = qs.filter(
            Q(DescAccAuto__icontains=search) | Q(Tipo__icontains=search)
        )
    cfg = tables["accionesauto_list"]
    table_ctx = build_table_context(request, user, cfg)
    sort_spec = table_ctx["sort_spec"]
    if sort_spec:
        order = [
            f"-{s['field']}" if s["direction"] == "desc" else s["field"]
            for s in sort_spec
        ]
        qs = qs.order_by(*order)
    else:
        qs = qs.order_by("IDAccAuto")
    records, page_obj, is_paginated = paginate_queryset(request, qs, cfg.paginate_by)
    return render(request, "seguridad/accionesauto_list.html", {
        "records": records,
        "search": search,
        "page_obj": page_obj,
        "is_paginated": is_paginated,
        **table_ctx,
    })


@login_required
def accionesauto_create_view(request: HttpRequest) -> HttpResponse:
    """Create a new AccionesAuto record."""
    padres = AccionesAuto.objects.all().order_by("DescAccAuto")
    if request.method == "POST":
        hijo_pk = request.POST.get("Hijo", "").strip()
        hijo = get_object_or_404(AccionesAuto, pk=int(hijo_pk)) if hijo_pk else None
        obj = AccionesAuto(
            DescAccAuto=request.POST.get("DescAccAuto", "").strip(),
            Tipo=request.POST.get("Tipo", "Mensaje"),
            Hijo=hijo,
        )
        obj.save()
        messages.success(request, f"Acción automática {obj.pk} creada.")
        return redirect("accionesauto_detail", pk=obj.pk)
    from .table_manager import tables as _t
    cfg = _t.get("accionesauto_list")
    field_labels = dict(cfg.columns) if cfg else {}
    user = cast(Any, request).user
    is_admin = user.is_superuser or getattr(user, "rol", None) == User.Rol.ADMINISTRADOR
    return render(request, "seguridad/accionesauto_detail.html", {
        "obj": None,
        "field_labels": field_labels,
        "is_admin": is_admin,
        "is_new": True,
        "padres": padres,
    })


@login_required
def accionesauto_detail_view(request: HttpRequest, pk: int) -> HttpResponse:
    """View/edit a single AccionesAuto record + inline AccAutoFields."""
    obj = get_object_or_404(AccionesAuto, pk=pk)
    padres = AccionesAuto.objects.exclude(IDAccAuto=pk).order_by("DescAccAuto")

    # ── Delete parent ──
    if request.method == "POST" and request.POST.get("_method") == "delete":
        obj.delete()
        messages.success(request, f"Acción automática {pk} eliminada.")
        return redirect("accionesauto_list")

    # ── Save parent ──
    if request.method == "POST" and request.POST.get("_method") == "save":
        hijo_pk = request.POST.get("Hijo", "").strip()
        hijo = get_object_or_404(AccionesAuto, pk=int(hijo_pk)) if hijo_pk else None
        obj.DescAccAuto = request.POST.get("DescAccAuto", "").strip()
        obj.Tipo = request.POST.get("Tipo", "Mensaje")
        obj.Hijo = hijo
        obj.save()
        messages.success(request, f"Acción automática {pk} actualizada.")
        return redirect("accionesauto_detail", pk=pk)

    # ── Add child field ──
    if request.method == "POST" and request.POST.get("_method") == "add_field":
        AccAutoFields.objects.create(
            IDAccAuto=obj,
            Orden=int(request.POST.get("Orden", 0)),
            Field=request.POST.get("Field", "").strip(),
            Cond=request.POST.get("Cond", "EQ"),
            Valor=request.POST.get("Valor", "").strip(),
        )
        messages.success(request, "Campo añadido.")
        return redirect("accionesauto_detail", pk=pk)

    # ── Delete child field ──
    if request.method == "POST" and request.POST.get("_method") == "del_field":
        field_pk = request.POST.get("field_pk", "").strip()
        if field_pk:
            AccAutoFields.objects.filter(pk=int(field_pk), IDAccAuto=obj).delete()
            messages.success(request, "Campo eliminado.")
        return redirect("accionesauto_detail", pk=pk)

    # ── GET ──
    campos = AccAutoFields.objects.filter(IDAccAuto=obj).order_by("Orden")
    from .table_manager import tables as _t
    cfg = _t.get("accionesauto_list")
    field_labels = dict(cfg.columns) if cfg else {}
    user = cast(Any, request).user
    is_admin = user.is_superuser or getattr(user, "rol", None) == User.Rol.ADMINISTRADOR
    return render(request, "seguridad/accionesauto_detail.html", {
        "obj": obj,
        "field_labels": field_labels,
        "is_admin": is_admin,
        "padres": padres,
        "campos": campos,
    })

