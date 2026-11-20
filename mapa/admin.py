from django.contrib import admin

from .models import DisenoEspacial


@admin.register(DisenoEspacial)
class DisenoEspacialAdmin(admin.ModelAdmin):
    list_display = ("establecimiento", "tipo_diseno", "area_total_ha", "porcentaje_floral", "cumple_minimo_20", "actualizado_en")
    list_filter = ("tipo_diseno", "cumple_minimo_20")
    search_fields = ("establecimiento__nombre", "establecimiento__usuario__username")
