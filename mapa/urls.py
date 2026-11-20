from django.urls import path
from . import views

app_name = 'mapa'

# [Integración] Cada diseño pertenece a un establecimiento (el <pk> es el del Establecimiento de campos)
urlpatterns = [
    # 1. Página de Entrada (Registro de Terreno) y su endpoint de guardado
    path('establecimientos/<int:pk>/terreno/', views.registro_terreno, name='registro_terreno'),
    path('establecimientos/<int:pk>/terreno/guardar/', views.guardar_terreno, name='guardar_terreno'),
    
    # 2. Página de Salida (Propuesta de Rediseño) y su endpoint de guardado
    path('establecimientos/<int:pk>/propuesta/', views.propuesta_redisenio, name='propuesta_redisenio'),
    path('establecimientos/<int:pk>/propuesta/guardar/', views.guardar_propuesta, name='guardar_propuesta'),
]