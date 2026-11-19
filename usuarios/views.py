from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import LoginForm, RegistroForm


class RegistroView(CreateView):
    """
    Muestra el formulario de registro (GET) y crea el usuario (POST).
    CreateView hace casi todo: valida el formulario y llama a form.save().
    """

    form_class = RegistroForm
    template_name = "usuarios/registro.html"
    # Después de registrarse, el paso 2 es elegir el plan (pantalla solo visual por ahora).
    success_url = reverse_lazy("suscripciones:plan")

    def dispatch(self, request, *args, **kwargs):
        # Si ya inició sesión, no tiene sentido registrarse de nuevo.
        if request.user.is_authenticated:
            return redirect("principal:inicio")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        respuesta = super().form_valid(form)  # guarda el usuario en self.object
        # Inicia sesión automáticamente con el usuario recién creado.
        login(self.request, self.object)
        messages.success(self.request, f"¡Bienvenido/a a PoliCampo, {self.object.username}!")
        return respuesta


class IngresoView(LoginView):
    """LoginView de Django usando nuestro formulario 'Usuario o email'."""

    form_class = LoginForm
    template_name = "usuarios/login.html"
    # Si ya está logueado y entra a /login, lo manda al inicio.
    redirect_authenticated_user = True
