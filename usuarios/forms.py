from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Usuario


class RegistroForm(UserCreationForm):
    """
    Formulario de registro. UserCreationForm (de Django) ya trae:
    - password1 / password2 con confirmación y validadores de seguridad
    - validación de que el username no exista (sin distinguir mayúsculas)
    - guardado de la contraseña CIFRADA (nunca en texto plano)

    Nosotros agregamos el email obligatorio y único.
    El campo `rol` NO está en el formulario: todo registro es rol Usuario.
    """

    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )

    class Meta(UserCreationForm.Meta):
        model = Usuario
        # Solo estos campos se toman de lo que envía el navegador.
        # Si alguien agrega a mano "rol=ADMINISTRADOR" en la petición, se ignora.
        fields = ("username", "email")
        labels = {"username": "Nombre de usuario"}

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta registrada con este email.")
        return email


class LoginForm(AuthenticationForm):
    """
    Formulario de inicio de sesión de Django, con el campo renombrado.
    Lo que se escriba acá llega como `username` a nuestro backend
    (UsuarioOEmailBackend), que decide si es un usuario o un email.
    """

    username = forms.CharField(
        label="Usuario o email",
        widget=forms.TextInput(attrs={"autofocus": True, "autocomplete": "username"}),
    )

    error_messages = {
        **AuthenticationForm.error_messages,
        # Mensaje genérico: no revelamos si el usuario existe o no.
        "invalid_login": "Usuario/email o contraseña incorrectos.",
    }
