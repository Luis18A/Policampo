from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

# El app_name permite referirse a las URLs como "usuarios:login", "usuarios:registro"...
app_name = "usuarios"

urlpatterns = [
    path("registro/", views.RegistroView.as_view(), name="registro"),
    path("login/", views.IngresoView.as_view(), name="login"),
    # LogoutView de Django: solo acepta POST (un botón en un formulario con CSRF).
    path("logout/", LogoutView.as_view(), name="logout"),
]
