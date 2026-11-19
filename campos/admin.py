from django.contrib import admin

from .models import CroquisManual, Establecimiento, Parcela, UbicacionGeografica


class ParcelaEnLinea(admin.TabularInline):
    """Muestra las parcelas dentro de la ficha del establecimiento en el panel /admin."""
    model = Parcela
    extra = 0
    fields = ("nombre", "tipo_uso", "cultivo", "superficie_ha", "ubicacion_relativa", "origen")


@admin.register(Establecimiento)
class EstablecimientoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "usuario", "localidad", "departamento", "superficie_total_ha", "metodo_caracterizacion")
    list_filter = ("departamento", "ecorregion", "metodo_caracterizacion")
    search_fields = ("nombre", "localidad", "usuario__username", "usuario__email")
    inlines = [ParcelaEnLinea]


admin.site.register(CroquisManual)
admin.site.register(UbicacionGeografica)
