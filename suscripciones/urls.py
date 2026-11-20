from django.urls import path

from . import views

app_name = "suscripciones"

urlpatterns = [
    path("plan/", views.PlanView.as_view(), name="plan"),
    path("pago/", views.PagoView.as_view(), name="pago"),
]
