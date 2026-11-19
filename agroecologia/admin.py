from django.contrib import admin
from .models import (
    Finca,
    Cultivo,
    CultivoFinca,
    CultivoServicio,
    CompatibilidadCultivo,
    Diagnostico,
    PropuestaRediseno,
    FranjaCultivoServicio,
    Informe,
)

@admin.register(Finca)
class FincaAdmin(admin.ModelAdmin):
    list_display = ('id_finca', 'nombre', 'ubicacion', 'superficie', 'tipo_suelo', 'capacidad_riego')
    search_fields = ('nombre', 'ubicacion')

@admin.register(Cultivo)
class CultivoAdmin(admin.ModelAdmin):
    list_display = ('id_cultivo', 'nombre', 'periodo_florecimiento', 'tipo_polinizacion')
    search_fields = ('nombre',)

@admin.register(CultivoFinca)
class CultivoFincaAdmin(admin.ModelAdmin):
    list_display = ('id_cultivo_finca', 'finca', 'cultivo', 'fecha_siembra', 'superficie_ocupada')

@admin.register(CultivoServicio)
class CultivoServicioAdmin(admin.ModelAdmin):
    list_display = ('id_cultivo_servicio', 'nombre_comun', 'nombre_cientifico', 'tipo_servicio', 'periodo_florecimiento')
    search_fields = ('nombre_comun', 'nombre_cientifico')

@admin.register(CompatibilidadCultivo)
class CompatibilidadCultivoAdmin(admin.ModelAdmin):
    list_display = ('cultivo', 'cultivo_servicio', 'grado')
    list_filter = ('grado',)

@admin.register(Diagnostico)
class DiagnosticoAdmin(admin.ModelAdmin):
    list_display = ('id_diagnostico', 'finca', 'porcentaje_floral_actual', 'deficit_biodiversidad', 'nivel_riesgo', 'fecha_diagnostico')
    list_filter = ('nivel_riesgo',)

@admin.register(PropuestaRediseno)
class PropuestaRedisenoAdmin(admin.ModelAdmin):
    list_display = ('id_propuesta', 'diagnostico', 'superficie_propuesta_ha', 'porcentaje_recuperado', 'fecha_creacion')

@admin.register(FranjaCultivoServicio)
class FranjaCultivoServicioAdmin(admin.ModelAdmin):
    list_display = ('id_franja_servicio', 'propuesta', 'cultivo_servicio', 'porcentaje_en_franja', 'rol_agroecologico')

@admin.register(Informe)
class InformeAdmin(admin.ModelAdmin):
    list_display = ('codigo_informe', 'propuesta', 'fecha_emision')
