from django.urls import path

from . import views

app_name = 'mapa'

# [Integración] Cada diseño pertenece a un establecimiento (el <pk> es el del Establecimiento de campos)
urlpatterns = [
    path('establecimientos/<int:pk>/disenar/', views.vista_mapa, name='delimitar_terreno'),
    path('establecimientos/<int:pk>/disenar/guardar/', views.guardar_diseno, name='guardar_diseno'),
]
