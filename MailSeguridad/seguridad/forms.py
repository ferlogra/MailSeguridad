from __future__ import annotations

from django import forms
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError

from .email_config import EmailSettings
from .models import User


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email", "telefono", "fecha_baja", "rol"]
        widgets = {
            "fecha_baja": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "field")


class SignupForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label="Nombre de usuario",
        widget=forms.TextInput(attrs={"class": "field", "autocomplete": "username"}),
    )
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={"class": "field", "autocomplete": "email"}),
    )
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"class": "field", "autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Repite la contraseña",
        widget=forms.PasswordInput(attrs={"class": "field", "autocomplete": "new-password"}),
    )

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está registrado.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está registrado.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        if p1 and len(p1) < 8:
            raise forms.ValidationError("La contraseña debe tener al menos 8 caracteres.")
        return cleaned_data


class VerificationForm(forms.Form):
    code = forms.CharField(
        max_length=8,
        min_length=8,
        label="Código de verificación",
        widget=forms.TextInput(attrs={
            "class": "field", "placeholder": "12345678", "autocomplete": "off",
        }),
    )


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={
            "class": "field", "autocomplete": "email", "placeholder": "tu@correo.com",
        }),
    )


class PasswordResetForm(forms.Form):
    password1 = forms.CharField(
        label="Nueva contraseña",
        help_text=password_validation.password_validators_help_text_html(),
        widget=forms.PasswordInput(attrs={"class": "field", "autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Repite la contraseña",
        widget=forms.PasswordInput(attrs={"class": "field", "autocomplete": "new-password"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data


class EmailConfigForm(forms.Form):
    """Form backed by EmailSettings (JSON file)."""

    host = forms.CharField(
        label="Servidor SMTP", required=False,
        widget=forms.TextInput(attrs={"class": "field", "placeholder": "smtp.ejemplo.com"}),
    )
    port = forms.IntegerField(
        label="Puerto", required=False, initial=587,
        widget=forms.NumberInput(attrs={"class": "field"}),
    )
    from_email = forms.EmailField(
        label="Dirección de envío", required=False,
        widget=forms.EmailInput(attrs={"class": "field", "placeholder": "noreply@ejemplo.com"}),
    )
    username = forms.CharField(
        label="Usuario", required=False,
        widget=forms.TextInput(attrs={"class": "field", "placeholder": "usuario@ejemplo.com"}),
    )
    password = forms.CharField(
        label="Contraseña", required=False,
        widget=forms.PasswordInput(attrs={"class": "field", "autocomplete": "off"}),
        help_text="Déjalo vacío para mantener la contraseña actual.",
    )
    encryption_type = forms.ChoiceField(
        label="Tipo de cifrado",
        choices=[("none", "Sin cifrado"), ("starttls", "STARTTLS"), ("ssl_tls", "SSL/TLS")],
        widget=forms.Select(attrs={"class": "field"}),
    )
    use_starttls = forms.BooleanField(
        label="Usar STARTTLS", required=False, initial=True,
        widget=forms.CheckboxInput(attrs={"class": "field"}),
    )
    test_recipient = forms.EmailField(
        label="Correo de prueba", required=False,
        widget=forms.EmailInput(attrs={
            "class": "field", "placeholder": "destinatario@ejemplo.com",
        }),
    )

    def __init__(self, *args, **kwargs):
        settings: EmailSettings | None = kwargs.pop("settings", None)
        super().__init__(*args, **kwargs)
        if settings and not kwargs.get("data"):
            self.initial = {
                "host": settings.host,
                "port": settings.port,
                "from_email": settings.from_email,
                "username": settings.username,
                "encryption_type": settings.encryption_type,
                "use_starttls": settings.use_starttls,
            }

    def to_settings(self) -> EmailSettings:
        settings = EmailSettings(
            host=self.cleaned_data.get("host", ""),
            port=self.cleaned_data.get("port", 587),
            from_email=self.cleaned_data.get("from_email", ""),
            username=self.cleaned_data.get("username", ""),
            use_starttls=self.cleaned_data.get("use_starttls", True),
            encryption_type=self.cleaned_data.get("encryption_type", "starttls"),
        )
        raw_password = self.cleaned_data.get("password", "")
        if raw_password:
            settings.set_password(raw_password)
        return settings
