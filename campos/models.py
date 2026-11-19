from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator


class DepartamentoJujuy(models.TextChoices):
    BELGRANO = 'Dr. Manuel Belgrano', 'Dr. Manuel Belgrano'
    PALPALA = 'Palpalá', 'Palpalá'
    EL_CARMEN = 'El Carmen', 'El Carmen'
    SAN_ANTONIO = 'San Antonio', 'San Antonio'
    SAN_PEDRO = 'San Pedro', 'San Pedro'
    LEDESMA = 'Ledesma', 'Ledesma'
    SANTA_BARBARA = 'Santa Bárbara', 'Santa Bárbara'
    TILCARA = 'Tilcara', 'Tilcara'
    TUMBAYA = 'Tumbaya', 'Tumbaya'
    HUMAHUACA = 'Humahuaca', 'Humahuaca'
    VALLE_GRANDE = 'Valle Grande', 'Valle Grande'
    COCHINOCA = 'Cochinoca', 'Cochinoca'
    RINCONADA = 'Rinconada', 'Rinconada'
    SANTA_CATALINA = 'Santa Catalina', 'Santa Catalina'
    YAVI = 'Yavi', 'Yavi'
    SUSQUES = 'Susques', 'Susques'


class Ecorregion(models.TextChoices):
    VALLES = 'Valles Templados', 'Valles Templados'
    QUEBRADA = 'Quebrada de Humahuaca', 'Quebrada de Humahuaca'
    YUNGAS = 'Yungas', 'Yungas'
    PUNA = 'Puna', 'Puna'
    OTRA = 'Otra', 'Otra'


class DisponibilidadAgua(models.TextChoices):
    ACEQUIA = 'Acequia / Turno de riego', 'Acequia / Turno de riego'
    RIO = 'Río / Vertiente natural', 'Río / Vertiente natural'
    POZO = 'Pozo / Bomba', 'Pozo / Bomba'
    RED = 'Red comunitaria de agua', 'Red comunitaria de agua'
    LLUVIA = 'Cosecha de lluvia / Represa', 'Cosecha de lluvia / Represa'
    LIMITADA = 'Limitada / Solo secano', 'Limitada / Solo secano'


class TipoUso(models.TextChoices):
    CULTIVO = 'cultivo_agricola', 'Cultivo agrícola'
    PASTURA = 'pastura', 'Pastura'
    SIN_CULTIVAR = 'sin_cultivar', 'Espacio sin cultivar'
    CAMINO = 'camino', 'Camino / Calzada'
    AGUA = 'agua', 'Agua (acequia, estanque, reservorio)'
    CONSTRUCCION = 'construccion', 'Construcción (vivienda, galpón, corral)'
    OTRO = 'otro', 'Otro uso'


class UbicacionRelativa(models.TextChoices):
    ARRIBA_IZQUIERDA = 'arriba_izquierda', 'Arriba a la izquierda'
    ARRIBA_CENTRO = 'arriba_centro', 'Arriba al centro'
    ARRIBA_DERECHA = 'arriba_derecha', 'Arriba a la derecha'
    CENTRO_IZQUIERDA = 'centro_izquierda', 'Centro a la izquierda'
    CENTRO = 'centro', 'Centro'
    CENTRO_DERECHA = 'centro_derecha', 'Centro a la derecha'
    ABAJO_IZQUIERDA = 'abajo_izquierda', 'Abajo a la izquierda'
    ABAJO_CENTRO = 'abajo_centro', 'Abajo al centro'
    ABAJO_DERECHA = 'abajo_derecha', 'Abajo a la derecha'


class MetodoCaracterizacion(models.TextChoices):
    CUESTIONARIO = 'cuestionario', 'Registrar por superficies (cuestionario)'
    CROQUIS_MANUAL = 'croquis_manual', 'Dibujar mi terreno (croquis manual)'
    AMBOS = 'ambos', 'Ambos métodos utilizados'


COLORES_POLICAMPO = [
    ('#2b8a3e', 'Verde fuerte'),
    ('#339af0', 'Celeste'),
    ('#ff922b', 'Naranja'),
    ('#fcc419', 'Amarillo'),
    ('#e64980', 'Rosa'),
    ('#cc5de8', 'Fucsia'),
    ('#845ef7', 'Violeta'),
    ('#20c997', 'Turquesa'),
]


class Establecimiento(models.Model):
    nombre = models.CharField(max_length=150, verbose_name="Nombre del establecimiento")
    direccion = models.CharField(
        max_length=250,
        blank=True,
        verbose_name="Dirección o Paraje",
        help_text="Ubicación física para localizar el establecimiento (no inventa cultivos)"
    )
    departamento = models.CharField(
        max_length=100,
        choices=DepartamentoJujuy.choices,
        default=DepartamentoJujuy.TILCARA,
        verbose_name="Departamento"
    )
    localidad = models.CharField(max_length=120, verbose_name="Localidad")
    ecorregion = models.CharField(
        max_length=50,
        choices=Ecorregion.choices,
        default=Ecorregion.QUEBRADA,
        verbose_name="Ecorregión"
    )
    superficie_total_ha = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))],
        verbose_name="Superficie total (hectáreas)"
    )
    largo_estimado_m = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('1.00'))],
        verbose_name="Largo estimado (metros, opcional)"
    )
    ancho_estimado_m = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('1.00'))],
        verbose_name="Ancho estimado (metros, opcional)"
    )
    disponibilidad_agua = models.CharField(
        max_length=100,
        choices=DisponibilidadAgua.choices,
        default=DisponibilidadAgua.ACEQUIA,
        verbose_name="Disponibilidad de agua"
    )
    cultivo_principal = models.CharField(
        max_length=150,
        verbose_name="Cultivo principal"
    )
    metodo_caracterizacion = models.CharField(
        max_length=30,
        choices=MetodoCaracterizacion.choices,
        default=MetodoCaracterizacion.CUESTIONARIO,
        verbose_name="Método de caracterización"
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Establecimiento"
        verbose_name_plural = "Establecimientos"
        ordering = ['-creado_en']

    def __str__(self):
        return f"{self.nombre} ({self.localidad}, {self.departamento})"

    @property
    def superficie_total_m2(self) -> Decimal:
        return self.superficie_total_ha * Decimal('10000.0')

    @property
    def superficie_distribuida_ha(self) -> Decimal:
        total = sum((p.superficie_ha or Decimal('0.0000')) for p in self.parcelas.all())
        return total if total else Decimal('0.0000')

    @property
    def superficie_distribuida_m2(self) -> Decimal:
        return self.superficie_distribuida_ha * Decimal('10000.0')

    @property
    def superficie_restante_ha(self) -> Decimal:
        restante = self.superficie_total_ha - self.superficie_distribuida_ha
        return max(Decimal('0.0000'), restante)

    @property
    def superficie_restante_m2(self) -> Decimal:
        return self.superficie_restante_ha * Decimal('10000.0')

    @property
    def porcentaje_utilizado(self) -> float:
        if not self.superficie_total_ha or self.superficie_total_ha <= 0:
            return 0.0
        pct = float((self.superficie_distribuida_ha / self.superficie_total_ha) * 100)
        return round(pct, 2)

    def get_datos_para_proceso(self) -> dict:
        """
        Estructura común de información para integración con el futuro módulo Proceso.
        Recupera la caracterización completa (datos del establecimiento, parcelas,
        cultivos y superficies) sin importar si provino de cuestionario o dibujo manual.
        """
        parcelas_data = []
        for p in self.parcelas.all():
            parcelas_data.append({
                'id': p.pk,
                'nombre': p.nombre,
                'tipo_uso': p.tipo_uso,
                'tipo_uso_display': p.get_tipo_uso_display(),
                'cultivo': p.cultivo or 'Sin cultivo específico',
                'superficie_ha': float(p.superficie_ha) if p.superficie_ha is not None else None,
                'superficie_m2': float(p.superficie_m2) if p.superficie_ha is not None else None,
                'ubicacion_relativa': p.ubicacion_relativa,
                'color_hex': p.color_hex,
                'origen_ingreso': p.origen,
                'observaciones': p.observaciones,
                'tiene_geometria_croquis': bool(p.geometria_visual),
                'geometria_croquis': p.geometria_visual or {},
            })

        return {
            'establecimiento_id': self.pk,
            'nombre': self.nombre,
            'direccion': self.direccion,
            'localidad': self.localidad,
            'departamento': self.departamento,
            'ecorregion': self.ecorregion,
            'superficie_total_ha': float(self.superficie_total_ha),
            'superficie_total_m2': float(self.superficie_total_m2),
            'disponibilidad_agua': self.disponibilidad_agua,
            'cultivo_principal': self.cultivo_principal,
            'metodo_caracterizacion': self.metodo_caracterizacion,
            'metodo_caracterizacion_display': self.get_metodo_caracterizacion_display(),
            'total_parcelas': len(parcelas_data),
            'superficie_distribuida_ha': float(self.superficie_distribuida_ha),
            'superficie_restante_ha': float(self.superficie_restante_ha),
            'porcentaje_utilizado': self.porcentaje_utilizado,
            'parcelas': parcelas_data,
        }


class Parcela(models.Model):
    ORIGEN_CHOICES = [
        ('cuestionario', 'Cuestionario por superficies'),
        ('croquis_manual', 'Dibujo manual'),
    ]

    establecimiento = models.ForeignKey(
        Establecimiento,
        on_delete=models.CASCADE,
        related_name='parcelas'
    )
    nombre = models.CharField(max_length=120, verbose_name="Nombre de la parcela")
    tipo_uso = models.CharField(
        max_length=50,
        choices=TipoUso.choices,
        default=TipoUso.CULTIVO,
        verbose_name="Tipo de uso"
    )
    cultivo = models.CharField(
        max_length=120,
        blank=True,
        verbose_name="Nombre del cultivo"
    )
    superficie_ha = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.0001'))],
        verbose_name="Superficie (hectáreas, opcional en croquis manual)"
    )
    ubicacion_relativa = models.CharField(
        max_length=50,
        choices=UbicacionRelativa.choices,
        default=UbicacionRelativa.CENTRO,
        verbose_name="Ubicación relativa"
    )
    color_hex = models.CharField(
        max_length=7,
        default='#2b8a3e',
        verbose_name="Color de visualización"
    )
    observaciones = models.TextField(
        blank=True,
        verbose_name="Observaciones opcionales"
    )
    origen = models.CharField(
        max_length=30,
        choices=ORIGEN_CHOICES,
        default='cuestionario',
        verbose_name="Origen del registro"
    )
    geometria_visual = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Geometría visual del dibujo en croquis (x, y, w, h)"
    )
    orden = models.PositiveIntegerField(default=0)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Parcela"
        verbose_name_plural = "Parcelas"
        ordering = ['orden', 'id']

    def __str__(self):
        sup_str = f"{self.superficie_ha} ha" if self.superficie_ha else "Sup. no esp."
        return f"{self.nombre} ({sup_str}) - {self.establecimiento.nombre}"

    @property
    def superficie_m2(self) -> Decimal:
        if self.superficie_ha:
            return self.superficie_ha * Decimal('10000.0')
        return Decimal('0.0')


class CroquisManual(models.Model):
    """
    Metadatos de lienzo del dibujo manual.
    Las parcelas reales se almacenan unificadas en la tabla Parcela.
    """
    establecimiento = models.OneToOneField(
        Establecimiento,
        on_delete=models.CASCADE,
        related_name='croquis_manual'
    )
    perimetro_largo_m = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('100.00'),
        verbose_name="Perímetro visual largo"
    )
    perimetro_ancho_m = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('100.00'),
        verbose_name="Perímetro visual ancho"
    )
    datos_figuras = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Copia de respaldo vectorial"
    )
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Croquis Manual de {self.establecimiento.nombre}"


class UbicacionGeografica(models.Model):
    establecimiento = models.OneToOneField(
        Establecimiento,
        on_delete=models.CASCADE,
        related_name='ubicacion_gis'
    )
    latitud = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="Latitud"
    )
    longitud = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="Longitud"
    )
    zoom = models.IntegerField(default=14, verbose_name="Nivel de zoom")
    poligono_geojson = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Polígono geográfico GeoJSON"
    )
    superficie_gis_ha = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Superficie GIS estimada (ha)"
    )
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Ubicación GIS de {self.establecimiento.nombre}"
