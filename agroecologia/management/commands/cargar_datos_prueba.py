from django.core.management.base import BaseCommand
from datetime import date
from agroecologia.models import (
    Finca, Cultivo, CultivoFinca, CultivoServicio, CompatibilidadCultivo,
    Diagnostico, PropuestaRediseno, FranjaCultivoServicio, Informe
)


class Command(BaseCommand):
    help = 'Carga datos agronómicos de prueba para Jujuy (Fincas, Cultivos, Servicios, Diagnóstico e Informe)'

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando carga de datos agronómicos...")

        # 1. Cultivos Comerciales
        tomate, _ = Cultivo.objects.get_or_create(
            nombre="Tomate Redondo",
            defaults={
                'variedad': 'Platense / Perita',
                'periodo_florecimiento': 'Octubre a Febrero',
                'tipo_polinizacion': 'Entomófila por vibración (Bombus y abejas solitarias)',
                'requerimiento_polinizacion': 'Alto: la vibración incrementa notablemente el cuaje y tamaño del fruto'
            }
        )

        pimiento, _ = Cultivo.objects.get_or_create(
            nombre="Pimiento Morrón",
            defaults={
                'variedad': 'Cuadrado Rojo',
                'periodo_florecimiento': 'Noviembre a Marzo',
                'tipo_polinizacion': 'Mixta (autógama con alta respuesta entomófila)',
                'requerimiento_polinizacion': 'Moderado a Alto: mejora el número de semillas y grosor de pulpa'
            }
        )

        # 2. Plantas de Servicio / Franjas Florales
        calendula, _ = CultivoServicio.objects.get_or_create(
            nombre_comun="Caléndula",
            defaults={
                'nombre_cientifico': 'Calendula officinalis',
                'tipo_servicio': 'Borde multifuncional / Franja floral fija',
                'periodo_florecimiento': 'Septiembre a Mayo (prolongado)',
                'periodo_siembra': 'Marzo a Mayo (Otoño) o Agosto (Primavera)',
                'necesidad_corte': 'Baja: despunte floral post-pico de floración',
                'necesidad_agua': 'Baja a moderada, rústica ante sequías templadas',
                'beneficios': 'Atrae sírfidos, crisopas y coccinélidos predadores de pulgones y trips. Repele nemátodos del suelo.'
            }
        )

        borraja, _ = CultivoServicio.objects.get_or_create(
            nombre_comun="Borraja",
            defaults={
                'nombre_cientifico': 'Borago officinalis',
                'tipo_servicio': 'Franja floral atrayente de polinizadores',
                'periodo_florecimiento': 'Octubre a Marzo',
                'periodo_siembra': 'Abril a Junio (Otoño)',
                'necesidad_corte': 'Media: corte a fin de ciclo para resembrar o mulch',
                'necesidad_agua': 'Moderada, responde muy bien al riego por goteo',
                'beneficios': 'Rica fuente de néctar continuo para abejas nativas y abejorros. Fortalece la polinización del tomate.'
            }
        )

        vicia, _ = CultivoServicio.objects.get_or_create(
            nombre_comun="Vicia Villosa",
            defaults={
                'nombre_cientifico': 'Vicia villosa',
                'tipo_servicio': 'Cultivo de cobertura / Franja biológica mixta',
                'periodo_florecimiento': 'Septiembre a Noviembre',
                'periodo_siembra': 'Abril a Mayo',
                'necesidad_corte': 'Rolado o siega al 50-70% de floración si se usa como cobertura',
                'necesidad_agua': 'Baja, aprovecha la humedad residual otoñal',
                'beneficios': 'Fijación biológica de nitrógeno (hasta 120 kg N/ha), refugio para avispas parasitoides de orugas.'
            }
        )

        trebol, _ = CultivoServicio.objects.get_or_create(
            nombre_comun="Trébol Blanco",
            defaults={
                'nombre_cientifico': 'Trifolium repens',
                'tipo_servicio': 'Estrato cubresuelo permanente',
                'periodo_florecimiento': 'Octubre a Enero',
                'periodo_siembra': 'Marzo a Abril',
                'necesidad_corte': 'Baja: tolerante a cortes periódicos de mantenimiento',
                'necesidad_agua': 'Moderada a alta en verano',
                'beneficios': 'Excelente cobertura viva que suprime malezas, frena erosión en bordes y aporta polen dulce.'
            }
        )

        # 3. Compatibilidades
        CompatibilidadCultivo.objects.get_or_create(
            cultivo=tomate, cultivo_servicio=calendula,
            defaults={'grado': 5, 'motivo_descripcion': 'Sinergia excelente: combate trips y mosca blanca mientras aporta floración continua.'}
        )
        CompatibilidadCultivo.objects.get_or_create(
            cultivo=tomate, cultivo_servicio=borraja,
            defaults={'grado': 5, 'motivo_descripcion': 'Atracción directa de Bombus terrestres y nativos para la vibración de flores de tomate.'}
        )
        CompatibilidadCultivo.objects.get_or_create(
            cultivo=tomate, cultivo_servicio=vicia,
            defaults={'grado': 4, 'motivo_descripcion': 'Aporte de nitrógeno y refugio invernal para insectos predadores beneficiosos.'}
        )
        CompatibilidadCultivo.objects.get_or_create(
            cultivo=tomate, cultivo_servicio=trebol,
            defaults={'grado': 4, 'motivo_descripcion': 'Protección del suelo en cabeceras de riego sin competir agresivamente por luz.'}
        )

        # 4. Finca de prueba en Jujuy
        finca, _ = Finca.objects.get_or_create(
            nombre="Finca La Candelaria",
            defaults={
                'ubicacion': 'Perico (Valle Templado), Jujuy',
                'tipo_suelo': 'Franco arenoso con buen drenaje',
                'superficie': 10.00,
                'forma_terreno': 'Rectangular con orientación Norte-Sur',
                'capacidad_riego': 'Riego por goteo con cabezal automatizado',
                'pendiente': 'Suave (1.5%) con desagüe natural al Este',
                'disponibilidad_agua': 'Permanente mediante turno de consorcio de riego',
                'precipitacion_anual': 680
            }
        )

        # 5. Cultivo en la Finca
        CultivoFinca.objects.get_or_create(
            finca=finca, cultivo=tomate,
            defaults={
                'fecha_siembra': date(2026, 9, 15),
                'fecha_cosecha': date(2027, 2, 28),
                'superficie_ocupada': 9.70
            }
        )

        # 6. Diagnóstico
        diagnostico, _ = Diagnostico.objects.get_or_create(
            finca=finca,
            defaults={
                'superficie_total': 10.00,
                'superficie_floral_actual': 0.30,
                'porcentaje_floral_actual': 3.0,
                'porcentaje_recomendado': 20.0,
                'deficit_biodiversidad': 17.0,
                'superficie_requerida_ha': 1.70,
                'nivel_riesgo': 'CRITICO',
                'areas_aptas': 'Cabecera Norte (300 m x 5 m), cabecera Sur (300 m x 5 m) y borde lateral Este colindante al camino de servicio y canal secundario (800 m x 4 m).',
                'observaciones': 'La finca destina únicamente el 3% de su superficie a vegetación no comercial. Esto genera un déficit crítico de biodiversidad funcional (-17% frente a la norma agronómica recomendada del 20%). Existe riesgo severo de presión de plagas (trips, Tuta absoluta) y baja tasa de cuaje por déficit de insectos polinizadores en los meses pico (Noviembre-Enero).'
            }
        )

        # 7. Propuesta de Rediseño
        propuesta, _ = PropuestaRediseno.objects.get_or_create(
            diagnostico=diagnostico,
            defaults={
                'titulo': 'Plan Integral de Bandas Florales y Bordes Multifuncionales',
                'tipo_estructura': 'Borde multifuncional perimetral + Corredores transversales internos',
                'superficie_propuesta_ha': 1.70,
                'porcentaje_recuperado': 20.0,
                'disposicion_espacial': 'Se disponen 2 corredores florales transversales de 3 metros intercalados cada 80 metros de cultivo productivo, complementados con un borde multifuncional permanente de 4 metros sobre el margen Este, totalizando 1.70 hectáreas de infraestructura ecológica.'
            }
        )

        # 8. Especies asignadas a la franja floral
        FranjaCultivoServicio.objects.get_or_create(
            propuesta=propuesta, cultivo_servicio=calendula,
            defaults={
                'porcentaje_en_franja': 35.0,
                'rol_agroecologico': 'Estrato medio floral de atracción masiva y control de trips',
                'calendario_siembra': 'Siembra a principios de Agosto o Marzo',
                'calendario_floracion': 'Floración plena de Octubre a Abril',
                'calendario_mantenimiento': 'Despunte manual en Diciembre para estimular refloración'
            }
        )

        FranjaCultivoServicio.objects.get_or_create(
            propuesta=propuesta, cultivo_servicio=borraja,
            defaults={
                'porcentaje_en_franja': 25.0,
                'rol_agroecologico': 'Estrato alto - néctar continuo para abejorros Bombus',
                'calendario_siembra': 'Siembra otoñal (Mayo) o primaveral temprana (Agosto)',
                'calendario_floracion': 'Floración enérgica Noviembre a Febrero',
                'calendario_mantenimiento': 'Control de semillas post-floración para evitar competencia'
            }
        )

        FranjaCultivoServicio.objects.get_or_create(
            propuesta=propuesta, cultivo_servicio=vicia,
            defaults={
                'porcentaje_en_franja': 25.0,
                'rol_agroecologico': 'Fijación simbiótica de nitrógeno y hospedero de microavispas',
                'calendario_siembra': 'Siembra en línea en Mayo',
                'calendario_floracion': 'Septiembre a Noviembre',
                'calendario_mantenimiento': 'Corte superficial o rolado suave en Diciembre'
            }
        )

        FranjaCultivoServicio.objects.get_or_create(
            propuesta=propuesta, cultivo_servicio=trebol,
            defaults={
                'porcentaje_en_franja': 15.0,
                'rol_agroecologico': 'Estrato cubresuelo, retención de humedad y control de malezas',
                'calendario_siembra': 'Siembra al voleo en Marzo-Abril',
                'calendario_floracion': 'Octubre a Enero',
                'calendario_mantenimiento': 'Poda baja post-verano'
            }
        )

        # 9. Informe Técnico
        Informe.objects.get_or_create(
            propuesta=propuesta,
            defaults={
                'codigo_informe': 'INF-JUJ-2026-001',
                'titulo': 'Informe Técnico de Rediseño Territorial con Bandas Florales',
                'resumen_ejecutivo': 'Evaluación técnica y propuesta de ordenamiento agroecológico para Finca La Candelaria en Perico, Jujuy. El presente informe detalla la transición desde una cobertura floral deficitaria del 3.0% hacia el estándar agroecológico del 20.0%, incorporando 1.70 ha de bandas florales fijas y bordes multifuncionales para maximizar el control biológico y la polinización en cultivo de tomate.'
            }
        )

        self.stdout.write(self.style.SUCCESS("Datos de prueba cargados exitosamente."))
