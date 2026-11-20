from django.db import models

from campos.models import Establecimiento


class DisenoEspacial(models.Model):
    """
    [Integración] Último diseño espacial guardado desde el mapa de Agus para un establecimiento:
    contorno del terreno, sectores con cultivos y corredores florales.

    El mapa (mapa.js) arma un JSON completo (ubicación, cultivo, diseño, métricas,
    diagnóstico y geometrías GeoJSON). Lo guardamos entero en `datos`, y además copiamos
    algunos valores a columnas propias para poder mostrarlos o filtrarlos fácilmente
    (por ejemplo, saber si el diseño llega al 20 % de hábitat natural).

    OneToOne: un diseño por establecimiento. Guardar de nuevo reemplaza el anterior.
    """

    establecimiento = models.OneToOneField(
        Establecimiento,
        on_delete=models.CASCADE,
        related_name='diseno_espacial',
    )
    datos = models.JSONField(verbose_name="Diseño completo (JSON del mapa)")
    tipo_diseno = models.CharField(max_length=30, blank=True, verbose_name="Tipo de disposición")
    area_total_ha = models.DecimalField(max_digits=10, decimal_places=4, verbose_name="Área total (ha)")
    porcentaje_floral = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name="Porcentaje real de corredores florales"
    )
    cumple_minimo_20 = models.BooleanField(default=False, verbose_name="¿Llega al 20 % de hábitat natural?")
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Diseño espacial"
        verbose_name_plural = "Diseños espaciales"

    def __str__(self):
        return f"Diseño de {self.establecimiento.nombre} ({self.porcentaje_floral} % floral)"

    @property
    def parcela_geojson(self):
        """El contorno del terreno (GeoJSON) del último diseño, o None si no hay."""
        return (self.datos.get('geometrias') or {}).get('parcela')
