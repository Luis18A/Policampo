from django.urls import path
from . import views

app_name = 'campos'

urlpatterns = [
    # Pantalla de entrada inicial (Módulo de Caracterización)
    path('', views.pantalla_entrada, name='pantalla_entrada'),

    # Mis establecimientos (Lista y registro)
    path('establecimientos/', views.establecimientos_lista, name='establecimientos_lista'),
    path('establecimientos/nuevo/', views.establecimiento_crear, name='establecimiento_crear'),
    path('establecimientos/<int:pk>/', views.establecimiento_detalle, name='establecimiento_detalle'),
    path('establecimientos/<int:pk>/editar/', views.establecimiento_editar, name='establecimiento_editar'),

    # Opción A: Cuestionario de superficies y parcelas
    path('establecimientos/<int:pk>/cuestionario/', views.parcelas_cuestionario, name='parcelas_cuestionario'),
    path('establecimientos/<int:pk>/parcelas/<int:parcela_id>/editar/', views.parcela_editar, name='parcela_editar'),
    path('establecimientos/<int:pk>/parcelas/<int:parcela_id>/eliminar/', views.parcela_eliminar, name='parcela_eliminar'),

    # Primera representación: Croquis automático (SVG determinístico, no editable)
    path('establecimientos/<int:pk>/croquis-automatico/', views.croquis_automatico, name='croquis_automatico'),

    # Opción B: Dibujar mi terreno (Croquis manual interactivo)
    path('establecimientos/<int:pk>/croquis-manual/', views.croquis_manual, name='croquis_manual'),
    path('establecimientos/<int:pk>/croquis-manual/guardar/', views.croquis_manual_guardar, name='croquis_manual_guardar'),

    # Integración con futuro módulo Proceso (API de estructura de datos unificada)
    path('establecimientos/<int:pk>/proceso/', views.proceso_datos_api, name='proceso_datos_api'),

    # [Unificación] El mapa geográfico de Sol se eliminó: la ubicación y el diseño
    # sobre el mapa ahora los maneja la app mapa (parte de Agus).
]
