"""
Vistas del mapa (parte de Agus), en dos pasos:
1. Entrada: registro del terreno (contorno y sectores dibujados sobre el mapa).
2. Salida: propuesta de rediseño con franjas florales, a partir del terreno guardado.

[Integración] Todas las vistas:
- piden sesión iniciada y usan _establecimiento_del_usuario (404 si la finca es de otra persona);
- [Unificación] solo funcionan para fincas cargadas por el método "mapa"
  (cada finca se edita únicamente con el método con el que se cargó).
"""

import json
from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from campos.models import MetodoCaracterizacion
from campos.views import (
    _establecimiento_del_usuario,
    _rechazo_json_si_otro_metodo,
    _redirigir_si_otro_metodo,
)

from .models import DisenoEspacial

# Tope de tamaño del JSON que aceptamos (2 MB)
TAMANIO_MAXIMO_BYTES = 2 * 1024 * 1024

# [Unificación] El formulario de alta (app campos) guarda la ecorregión por nombre;
# el mapa de Agus (policampo_common.js) usa estos códigos.
ECORREGION_A_CODIGO_MAPA = {
    'Valles Templados': 'valles_templados',
    'Quebrada de Humahuaca': 'quebrada',
    'Yungas': 'yungas',
    'Puna': 'puna',
}


def _leer_json(request):
    """Devuelve el JSON del cuerpo del pedido, o None si es demasiado grande o no es JSON válido."""
    if len(request.body) > TAMANIO_MAXIMO_BYTES:
        return None
    try:
        data = json.loads(request.body)
    except (ValueError, TypeError):
        return None
    return data if isinstance(data, dict) else None


def _superficie_del_terreno(data):
    """Superficie total (ha) que calculó el mapa, como Decimal; None si no viene o no es válida."""
    try:
        valor = Decimal(str((data.get('superficie') or {})['total_ha'])).quantize(Decimal('0.0001'))
    except (KeyError, TypeError, AttributeError, InvalidOperation):
        return None
    return valor if 0 < valor < Decimal('1000000') else None


# ==========================================
# 1. PÁGINA DE ENTRADA (Carga de Terreno)
# ==========================================
@login_required
def registro_terreno(request, pk):
    """Muestra la interfaz para dibujar el contorno y los sectores."""
    # Seguridad: Verifica que el usuario sea el dueño del establecimiento
    establecimiento = _establecimiento_del_usuario(request, pk)
    otro_metodo = _redirigir_si_otro_metodo(request, establecimiento, MetodoCaracterizacion.MAPA)
    if otro_metodo:
        return otro_metodo

    return render(request, 'mapa/registro_terreno.html', {
        'establecimiento': establecimiento,
        # [Unificación] Los datos ya cargados en el alta: completan la sección oculta del paso 1
        'datos_finca': {
            'nombre': establecimiento.nombre,
            'direccion': establecimiento.direccion,
            'departamento': establecimiento.departamento,
            'localidad': establecimiento.localidad,
            'ecorregion_codigo': ECORREGION_A_CODIGO_MAPA.get(establecimiento.ecorregion, ''),
        },
    })


@login_required
@require_POST
def guardar_terreno(request, pk):
    """Endpoint (API) que recibe los datos de Turf.js (Página 1) y los guarda."""
    establecimiento = _establecimiento_del_usuario(request, pk)
    rechazo = _rechazo_json_si_otro_metodo(establecimiento, MetodoCaracterizacion.MAPA)
    if rechazo:
        return rechazo

    data = _leer_json(request)
    if data is None:
        return JsonResponse({'ok': False, 'mensaje': 'Los datos del terreno no son válidos.'}, status=400)

    # [Unificación] La superficie total de una finca de mapa sale del contorno dibujado
    # (entrada_mapa.js la manda en superficie.total_ha); no se pide en el formulario de alta.
    superficie = _superficie_del_terreno(data)
    if superficie is not None:
        establecimiento.superficie_total_ha = superficie
        establecimiento.save(update_fields=['superficie_total_ha', 'actualizado_en'])

    # Guardamos el JSON con valores por defecto (en cero) en los campos obligatorios:
    # las métricas reales se calculan en el paso 2 (propuesta).
    DisenoEspacial.objects.update_or_create(
        establecimiento=establecimiento,
        defaults={
            'datos': data,
            'area_total_ha': Decimal('0.0'),
            'porcentaje_floral': Decimal('0.0'),
            'tipo_diseno': 'Borrador (Paso 1)',
            'cumple_minimo_20': False,
        }
    )
    return JsonResponse({'ok': True, 'mensaje': 'Terreno guardado exitosamente'})


# ==========================================
# 2. PÁGINA DE SALIDA (Propuesta de Rediseño)
# ==========================================
@login_required
def propuesta_redisenio(request, pk):
    """Muestra la propuesta de rediseño leyendo el JSON guardado en el paso 1."""
    establecimiento = _establecimiento_del_usuario(request, pk)
    otro_metodo = _redirigir_si_otro_metodo(request, establecimiento, MetodoCaracterizacion.MAPA)
    if otro_metodo:
        return otro_metodo

    diseno = DisenoEspacial.objects.filter(establecimiento=establecimiento).first()

    return render(request, 'mapa/propuesta_redisenio.html', {
        'establecimiento': establecimiento,
        # [Integración] Se pasa el dict tal cual: la plantilla lo convierte con json_script
        # (la forma segura de darle datos a JavaScript; antes se usaba json.dumps + |safe).
        'terreno': diseno.datos if diseno else None,
    })


@login_required
@require_POST
def guardar_propuesta(request, pk):
    """Endpoint (API) que guarda el rediseño final con franjas y métricas."""
    establecimiento = _establecimiento_del_usuario(request, pk)
    rechazo = _rechazo_json_si_otro_metodo(establecimiento, MetodoCaracterizacion.MAPA)
    if rechazo:
        return rechazo

    data = _leer_json(request)
    if data is None:
        return JsonResponse({'ok': False, 'mensaje': 'Los datos de la propuesta no son válidos.'}, status=400)

    try:
        metricas = data.get('metricas') or {}
        diseno_data = data.get('diseno') or {}
        diag_espacial = data.get('diagnostico_espacial') or {}
        area_total_ha = Decimal(str(metricas.get('area_total_ha', 0)))
        porcentaje_floral = Decimal(str(diseno_data.get('porcentaje_real', 0)))
    except (AttributeError, InvalidOperation):
        return JsonResponse({'ok': False, 'mensaje': 'Los datos de la propuesta no son válidos.'}, status=400)

    diseno, _ = DisenoEspacial.objects.update_or_create(
        establecimiento=establecimiento,
        defaults={
            'datos': data,
            'tipo_diseno': str(diseno_data.get('tipo', ''))[:30],
            'area_total_ha': area_total_ha,
            'porcentaje_floral': porcentaje_floral,
            'cumple_minimo_20': bool(diag_espacial.get('cumple_minimo_20_pct')),
        },
    )
    return JsonResponse({
        'ok': True,
        'mensaje': 'Propuesta de rediseño guardada',
        'area_ha': float(diseno.area_total_ha),
    })
