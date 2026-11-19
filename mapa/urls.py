from django.urls import path
from . import views

urlpatterns = [
    path('delimitar/', views.vista_mapa, name='delimitar_terreno'),
]