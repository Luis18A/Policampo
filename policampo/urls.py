"""
URLs principales del proyecto. Cada app tiene su propio urls.py y acá se "incluyen".
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuentas/", include("usuarios.urls")),  # /cuentas/registro/, /cuentas/login/, /cuentas/logout/
    path("cuentas/", include("suscripciones.urls")),  # /cuentas/plan/, /cuentas/pago/ (solo visual)
    path("", include("principal.urls")),  # página principal
]
