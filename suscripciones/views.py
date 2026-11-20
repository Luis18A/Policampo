"""
Pantallas de plan y pago.

IMPORTANTE: por ahora son SOLO VISUALES. No se cobra nada, no se piden datos de tarjeta
y no se guarda el plan en la base de datos. Pagos/suscripciones son parte de otro
integrante del grupo: cuando se implementen de verdad, se hace en esta app.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

# Datos del único plan. Están acá (y no escritos en el HTML) para que sea fácil cambiarlos.
# TODO: precio de ejemplo, lo tiene que definir el grupo.
PLAN_PRO = {
    "nombre": "PoliCampo Pro",
    "precio": "4.500",
    "moneda": "ARS",
    "periodo": "mes",
    "incluye": [
        "Registro de fincas y cultivos (formulario o croquis)",
        "Diagnóstico de biodiversidad del terreno",
        "Propuestas de rediseño con franjas florales y plantas de servicio",
        "Calendario agroecológico de siembra, mantenimiento y floración",
        "Informes técnicos descargables",
    ],
}


class PlanView(LoginRequiredMixin, TemplateView):
    """
    Paso 2 después de registrarse: muestra el plan.
    LoginRequiredMixin: si no iniciaste sesión, te manda al login (LOGIN_URL en settings).
    """

    template_name = "suscripciones/plan.html"
    extra_context = {"plan": PLAN_PRO}


class PagoView(LoginRequiredMixin, TemplateView):
    """Pantalla de pago de muestra: resumen + medios de pago, con el botón Pagar deshabilitado."""

    template_name = "suscripciones/pago.html"
    extra_context = {"plan": PLAN_PRO}
