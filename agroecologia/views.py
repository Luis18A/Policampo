from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from decimal import Decimal
from .models import (
    Finca, Cultivo, CultivoFinca, CultivoServicio, CompatibilidadCultivo,
    Diagnostico, PropuestaRediseno, FranjaCultivoServicio, Informe
)


def diagnostico_view(request, id_diagnostico=None):
    """
    Vista del Módulo de Diagnóstico:
    Evalúa la finca, calcula el déficit de biodiversidad frente al 20%
    y muestra el estado ecológico y las áreas aptas para intervención.
    """
    if id_diagnostico:
        diagnostico = get_object_or_404(Diagnostico, id_diagnostico=id_diagnostico)
    else:
        diagnostico = Diagnostico.objects.first()

    fincas = Finca.objects.all()

    # Procesar simulación o nuevo cálculo de diagnóstico si se envía formulario POST
    if request.method == 'POST':
        try:
            finca_id = request.POST.get('finca_id')
            finca_obj = get_object_or_404(Finca, id_finca=finca_id)
            superficie_total = Decimal(request.POST.get('superficie_total', finca_obj.superficie))
            superficie_floral = Decimal(request.POST.get('superficie_floral', '0.0'))

            # Cálculo de regla agronómica del 20%
            porcentaje_actual = (superficie_floral / superficie_total) * Decimal('100.0') if superficie_total > 0 else Decimal('0.0')
            porcentaje_recomendado = Decimal('20.0')
            deficit = max(Decimal('0.0'), porcentaje_recomendado - porcentaje_actual)
            superficie_requerida = max(Decimal('0.0'), (superficie_total * Decimal('0.20')) - superficie_floral)

            if deficit > Decimal('10.0'):
                nivel_riesgo = 'CRITICO'
            elif deficit > Decimal('0.0'):
                nivel_riesgo = 'MODERADO'
            else:
                nivel_riesgo = 'ADECUADO'

            nuevo_diag = Diagnostico.objects.create(
                finca=finca_obj,
                superficie_total=superficie_total,
                superficie_floral_actual=superficie_floral,
                porcentaje_floral_actual=round(porcentaje_actual, 1),
                porcentaje_recomendado=porcentaje_recomendado,
                deficit_biodiversidad=round(deficit, 1),
                superficie_requerida_ha=round(superficie_requerida, 2),
                nivel_riesgo=nivel_riesgo,
                areas_aptas="Bordes perimetrales del predio y cabeceras de melgas productivas.",
                observaciones=f"Diagnóstico recalculado: déficit de biodiversidad del {deficit:.1f}%. Se requiere incorporar {superficie_requerida:.2f} ha de bandas florales para alcanzar el estándar del 20%."
            )
            messages.success(request, "Diagnóstico generado correctamente con las reglas agronómicas.")
            return redirect('diagnostico_detalle', id_diagnostico=nuevo_diag.id_diagnostico)
        except Exception as e:
            messages.error(request, f"Error al calcular diagnóstico: {e}")

    # Obtener cultivos de la finca actual
    cultivos_asociados = []
    propuesta_activa = None
    if diagnostico:
        cultivos_asociados = diagnostico.finca.cultivos_asociados.select_related('cultivo').all()
        propuesta_activa = diagnostico.propuestas.first()

    context = {
        'diagnostico': diagnostico,
        'fincas': fincas,
        'cultivos_asociados': cultivos_asociados,
        'propuesta_activa': propuesta_activa,
    }
    return render(request, 'agroecologia/diagnostico.html', context)


def informe_view(request, id_informe=None):
    """
    Vista del Módulo de Informe Técnico:
    Muestra la propuesta de rediseño detallada, las especies de servicio recomendadas,
    la matriz de compatibilidad, el calendario agroecológico y estilos @media print para PDF.
    """
    if id_informe:
        informe = get_object_or_404(Informe, id_informe=id_informe)
    else:
        informe = Informe.objects.first()

    propuesta = informe.propuesta if informe else None
    diagnostico = propuesta.diagnostico if propuesta else None
    finca = diagnostico.finca if diagnostico else None

    # Especies en la franja con compatibilidad evaluada
    especies_detalle = []
    if propuesta:
        cultivo_comercial = finca.cultivos_asociados.first().cultivo if finca.cultivos_asociados.exists() else None
        for item in propuesta.especies_asignadas.select_related('cultivo_servicio').all():
            comp = None
            if cultivo_comercial:
                comp = CompatibilidadCultivo.objects.filter(
                    cultivo=cultivo_comercial,
                    cultivo_servicio=item.cultivo_servicio
                ).first()
            especies_detalle.append({
                'item': item,
                'servicio': item.cultivo_servicio,
                'compatibilidad': comp.grado if comp else 5,
                'motivo': comp.motivo_descripcion if comp else item.cultivo_servicio.beneficios,
            })

    # Cronograma mensual agroecológico
    meses_calendario = [
        {'mes': 'Agosto', 'accion': 'Preparación de suelo en bordes y siembra temprana (Caléndula / Borraja)'},
        {'mes': 'Septiembre', 'accion': 'Emergencia de plántulas y riego de asiento; inicio floración temprana'},
        {'mes': 'Octubre', 'accion': 'Pico de floración activa - Solapamiento con floración del cultivo comercial'},
        {'mes': 'Noviembre', 'accion': 'Máxima atracción de Bombus y parasitoides; siembra de especies tardías'},
        {'mes': 'Diciembre', 'accion': 'Monitoreo de predadores; despunte y poda selectiva para refloración'},
        {'mes': 'Enero - Febrero', 'accion': 'Mantenimiento del corredor biológico y protección en cosecha'},
        {'mes': 'Marzo - Mayo', 'accion': 'Semillado natural para autosiembra anual y siembra de vicia invernal'},
    ]

    context = {
        'informe': informe,
        'propuesta': propuesta,
        'diagnostico': diagnostico,
        'finca': finca,
        'especies_detalle': especies_detalle,
        'meses_calendario': meses_calendario,
    }
    return render(request, 'agroecologia/informe.html', context)
