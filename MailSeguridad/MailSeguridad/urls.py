from __future__ import annotations

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from seguridad import views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="accounts_login"),
    path("logout/", views.logout_view, name="logout"),
    path("accounts/logout/", views.logout_view, name="accounts_logout"),
    path("registro/", views.signup_view, name="signup"),
    path("password_reset/", views.password_reset_request, name="password_reset_request"),
    path("password_reset/<str:token>/", views.password_reset_confirm, name="password_reset_confirm"),
    path("email-config/", views.email_config_view, name="email_config"),
    path("usuario/", include("seguridad.user_urls")),
    path("mensajes/", include("seguridad.urls")),
    path("tipoactuaciones/", include("seguridad.urls_tipoactuaciones")),
    path("actuaciones/", include("seguridad.urls_actuaciones")),
    path("actuaciones-tickets/", views.actuaciones_tickets_view, name="actuaciones_tickets"),
    path("config-tabla/", include("seguridad.urls_table_config")),
    path("menu/", views.menu_view, name="menu"),
    path("mensajes/borrar-todos/", views.clear_mensajes_view, name="clear_mensajes"),
    path("", views.home_view, name="home"),
    path("__health__/", views.health_view, name="health"),
    path("docs/", views.docs_view, name="docs"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
