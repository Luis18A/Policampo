"""
URLs principales del proyecto. Cada app tiene su propio urls.py y acá se "incluyen".
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuentas/", include("usuarios.urls")),  # /cuentas/registro/, /cuentas/login/, /cuentas/logout/
    path("cuentas/", include("suscripciones.urls")),  # /cuentas/plan/, /cuentas/pago/ (solo visual)
    path("campos/", include("campos.urls")),  # carga de establecimientos (parte de Sol)
    path("campos/", include("mapa.urls")),  # diseño en el mapa: /campos/establecimientos/<id>/disenar/ (parte de Agus)
    path("", include("principal.urls")),  # página principal
]
