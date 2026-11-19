from django.urls import path
from . import views

urlpatterns = [
    path('', views.diagnostico_view, name='diagnostico'),
    path('diagnostico/<int:id_diagnostico>/', views.diagnostico_view, name='diagnostico_detalle'),
    path('informe/', views.informe_view, name='informe'),
    path('informe/<int:id_informe>/', views.informe_view, name='informe_detalle'),
]
