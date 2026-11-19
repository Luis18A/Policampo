from django.db import models
from django.contrib.auth.models import User


class Finca(models.Model):
    """
    Finca o parcela productiva en Jujuy.
    """
    id_finca = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='fincas')
    nombre = models.CharField(max_length=150, verbose_name="Nombre de la Finca")
    ubicacion = models.CharField(max_length=200, verbose_name="Ubicación / Localidad (Jujuy)")
    tipo_suelo = models.CharField(max_length=100, verbose_name="Tipo de Suelo")
    superficie = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Superficie total (ha)")
    forma_terreno = models.CharField(max_length=150, blank=True, default="Polígono regular", verbose_name="Forma del terreno")
    capacidad_riego = models.CharField(max_length=100, default="Riego por goteo", verbose_name="Capacidad y tipo de riego")
    pendiente = models.CharField(max_length=100, default="Suave (1-3%)", verbose_name="Pendiente del terreno")
    disponibilidad_agua = models.CharField(max_length=150, default="Permanente (Canal de riego)", verbose_name="Disponibilidad de agua")
    precipitacion_anual = models.PositiveIntegerField(default=650, verbose_name="Precipitación media anual (mm)")
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'fincas'
        verbose_name = 'Finca'
        verbose_name_plural = 'fincas'

    def __str__(self):
        return f"{self.nombre} ({self.ubicacion}) - {self.superficie} ha"


class Cultivo(models.Model):
    """
    Cultivo comercial o de renta (frutas / hortalizas).
    """
    id_cultivo = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, verbose_name="Nombre del cultivo")
    variedad = models.CharField(max_length=100, blank=True, verbose_name="Variedad")
    periodo_florecimiento = models.CharField(max_length=120, verbose_name="Período de florecimiento")
    tipo_polinizacion = models.CharField(max_length=150, verbose_name="Tipo de polinización")
    requerimiento_polinizacion = models.CharField(max_length=200, blank=True, verbose_name="Requerimiento de polinizadores")

    class Meta:
        db_table = 'cultivos'
        verbose_name = 'Cultivo Comercial'
        verbose_name_plural = 'cultivos'

    def __str__(self):
        return self.nombre


class CultivoFinca(models.Model):
    """
    Cultivo comercial sembrado en una finca específica.
    """
    id_cultivo_finca = models.AutoField(primary_key=True)
    finca = models.ForeignKey(Finca, on_delete=models.CASCADE, related_name='cultivos_asociados')
    cultivo = models.ForeignKey(Cultivo, on_delete=models.CASCADE, related_name='fincas_asociadas')
    fecha_siembra = models.DateField(verbose_name="Fecha de siembra")
    fecha_cosecha = models.DateField(null=True, blank=True, verbose_name="Fecha estimada de cosecha")
    superficie_ocupada = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Superficie ocupada (ha)")

    class Meta:
        db_table = 'cultivos_fincas'
        verbose_name = 'Cultivo en Finca'
        verbose_name_plural = 'cultivos_fincas'

    def __str__(self):
        return f"{self.cultivo.nombre} en {self.finca.nombre} ({self.superficie_ocupada} ha)"


class CultivoServicio(models.Model):
    """
    Plantas de servicio / especies florales benéficas.
    Diferenciación INTA:
    - Franja floral / Borde multifuncional (permanente)
    - Cultivo de servicio / Puente verde (rotación en lote)
    """
    id_cultivo_servicio = models.AutoField(primary_key=True)
    nombre_comun = models.CharField(max_length=100, verbose_name="Nombre común")
    nombre_cientifico = models.CharField(max_length=150, blank=True, verbose_name="Nombre científico")
    tipo_servicio = models.CharField(
        max_length=100,
        default="Corredor biológico / Franja floral",
        verbose_name="Tipo de servicio agroecológico"
    )
    periodo_florecimiento = models.CharField(max_length=120, verbose_name="Período de florecimiento")
    periodo_siembra = models.CharField(max_length=120, verbose_name="Período de siembra")
    necesidad_corte = models.CharField(max_length=120, verbose_name="Necesidad de corte / poda")
    necesidad_agua = models.CharField(max_length=120, verbose_name="Necesidad de agua")
    beneficios = models.TextField(verbose_name="Beneficios y servicios ecosistémicos")

    class Meta:
        db_table = 'cultivos_servicios'
        verbose_name = 'Cultivo de Servicio / Especie Floral'
        verbose_name_plural = 'cultivos_servicios'

    def __str__(self):
        return f"{self.nombre_comun} ({self.nombre_cientifico})"


class CompatibilidadCultivo(models.Model):
    """
    Matriz de asociación y compatibilidad entre cultivo comercial y planta de servicio.
    Escala de grado: -5 (antagonismo) a +5 (máxima sinergia y control biológico).
    """
    cultivo = models.ForeignKey(Cultivo, on_delete=models.CASCADE, related_name='compatibilidades')
    cultivo_servicio = models.ForeignKey(CultivoServicio, on_delete=models.CASCADE, related_name='asociaciones')
    grado = models.IntegerField(default=5, verbose_name="Grado de compatibilidad (-5 a +5)")
    motivo_descripcion = models.TextField(verbose_name="Motivo y justificación agronómica")

    class Meta:
        db_table = 'compatibilidades_cultivos'
        verbose_name = 'Compatibilidad de Cultivos'
        verbose_name_plural = 'compatibilidades_cultivos'
        unique_together = ('cultivo', 'cultivo_servicio')

    def __str__(self):
        return f"{self.cultivo.nombre} + {self.cultivo_servicio.nombre_comun} [{'+' if self.grado > 0 else ''}{self.grado}]"


class Diagnostico(models.Model):
    """
    Evaluación del estado actual de biodiversidad y déficit de la finca.
    """
    RIESGOS = [
        ('CRITICO', 'Déficit Crítico de Biodiversidad'),
        ('MODERADO', 'Déficit Moderado'),
        ('ADECUADO', 'Nivel Adecuado'),
    ]

    id_diagnostico = models.AutoField(primary_key=True)
    finca = models.ForeignKey(Finca, on_delete=models.CASCADE, related_name='diagnosticos')
    superficie_total = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Superficie analizada (ha)")
    superficie_floral_actual = models.DecimalField(max_digits=8, decimal_places=2, default=0.0, verbose_name="Área floral actual (ha)")
    porcentaje_floral_actual = models.DecimalField(max_digits=5, decimal_places=1, default=0.0, verbose_name="% actual de biodiversidad")
    porcentaje_recomendado = models.DecimalField(max_digits=5, decimal_places=1, default=20.0, verbose_name="% recomendado (Regla 20%)")
    deficit_biodiversidad = models.DecimalField(max_digits=5, decimal_places=1, default=20.0, verbose_name="Déficit calculado (%)")
    superficie_requerida_ha = models.DecimalField(max_digits=8, decimal_places=2, default=0.0, verbose_name="Superficie floral requerida (ha)")
    nivel_riesgo = models.CharField(max_length=20, choices=RIESGOS, default='CRITICO')
    areas_aptas = models.TextField(verbose_name="Áreas aptas para intervención")
    observaciones = models.TextField(verbose_name="Diagnóstico agroecológico")
    fecha_diagnostico = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'diagnosticos'
        verbose_name = 'Diagnóstico'
        verbose_name_plural = 'diagnosticos'
        ordering = ['-fecha_diagnostico']

    def __str__(self):
        return f"Diagnóstico #{self.id_diagnostico} - {self.finca.nombre} ({self.nivel_riesgo})"


class PropuestaRediseno(models.Model):
    """
    Propuesta de rediseño territorial con bandas florales y bordes multifuncionales.
    """
    id_propuesta = models.AutoField(primary_key=True)
    diagnostico = models.ForeignKey(Diagnostico, on_delete=models.CASCADE, related_name='propuestas')
    titulo = models.CharField(max_length=200, default="Propuesta de Borde Multifuncional y Corredores Florales")
    tipo_estructura = models.CharField(max_length=150, default="Franja Floral Fija y Borde Multifuncional")
    superficie_propuesta_ha = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Superficie propuesta (ha)")
    porcentaje_recuperado = models.DecimalField(max_digits=5, decimal_places=1, default=20.0, verbose_name="% final de biodiversidad")
    disposicion_espacial = models.TextField(verbose_name="Disposición espacial y distribución")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'propuestas_redisenos'
        verbose_name = 'Propuesta de Rediseño'
        verbose_name_plural = 'propuestas_redisenos'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Propuesta #{self.id_propuesta} para {self.diagnostico.finca.nombre}"


class FranjaCultivoServicio(models.Model):
    """
    Especies de servicio asignadas a la propuesta de franja floral y su planificación.
    """
    id_franja_servicio = models.AutoField(primary_key=True)
    propuesta = models.ForeignKey(PropuestaRediseno, on_delete=models.CASCADE, related_name='especies_asignadas')
    cultivo_servicio = models.ForeignKey(CultivoServicio, on_delete=models.CASCADE)
    porcentaje_en_franja = models.DecimalField(max_digits=5, decimal_places=1, default=25.0, verbose_name="% en la mezcla de siembra")
    rol_agroecologico = models.CharField(max_length=150, verbose_name="Rol en la franja")
    calendario_siembra = models.CharField(max_length=150, verbose_name="Época óptima de siembra")
    calendario_floracion = models.CharField(max_length=150, verbose_name="Ventana de floración")
    calendario_mantenimiento = models.CharField(max_length=150, verbose_name="Mantenimiento y cortes")

    class Meta:
        db_table = 'franjas_cultivos_servicios'
        verbose_name = 'Especie en Franja Floral'
        verbose_name_plural = 'franjas_cultivos_servicios'

    def __str__(self):
        return f"{self.cultivo_servicio.nombre_comun} ({self.porcentaje_en_franja}%) en Propuesta #{self.propuesta.id_propuesta}"


class Informe(models.Model):
    """
    Informe técnico descargable emitido para la toma de decisiones.
    """
    id_informe = models.AutoField(primary_key=True)
    propuesta = models.OneToOneField(PropuestaRediseno, on_delete=models.CASCADE, related_name='informe')
    codigo_informe = models.CharField(max_length=50, unique=True, verbose_name="Código de informe")
    titulo = models.CharField(max_length=250, default="Informe Técnico de Rediseño Agroecológico y Biodiversidad")
    resumen_ejecutivo = models.TextField(verbose_name="Resumen ejecutivo")
    fecha_emision = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'informes'
        verbose_name = 'Informe Técnico'
        verbose_name_plural = 'informes'
        ordering = ['-fecha_emision']

    def __str__(self):
        return f"{self.codigo_informe} - {self.propuesta.diagnostico.finca.nombre}"
