"""
Vistas del mapa de diseño espacial (parte de Agus).

[Integración] Su versión original tenía una vista sin login ni establecimiento, y la de guardar
no estaba conectada a ninguna URL. Ahora:
- el mapa se abre para UN establecimiento del usuario que inició sesión;
- al guardar, el diseño queda en la base (modelo DisenoEspacial);
- se reutiliza _establecimiento_del_usuario de la app campos: si el establecimiento
  es de otra persona, la respuesta es 404.
"""

import json
from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from campos.views import _establecimiento_del_usuario

from .models import DisenoEspacial

# Tope de tamaño del JSON que aceptamos (2 MB): un diseño normal pesa unos pocos KB.
TAMANIO_MAXIMO_BYTES = 2 * 1024 * 1024


def _centro_del_diseno(diseno):
    """Lat/lng guardadas en el diseño (la arma mapa.js en datos["ubicacion"]), o None."""
    ubicacion = (diseno.datos or {}).get('ubicacion') if diseno else None
    try:
        return {'lat': float(ubicacion['lat']), 'lng': float(ubicacion['lng']), 'zoom': 16}
    except (TypeError, KeyError, ValueError):
        return None


@login_required
def vista_mapa(request, pk):
    establecimiento = _establecimiento_del_usuario(request, pk)
    diseno = DisenoEspacial.objects.filter(establecimiento=establecimiento).first()

    # [Unificación] El mapa de Sol se eliminó: el contorno y el centro iniciales
    # salen solo del último diseño guardado (si no hay, el mapa arranca en Jujuy).
    parcela_inicial = diseno.parcela_geojson if diseno else None
    centro_inicial = _centro_del_diseno(diseno)

    return render(request, 'mapa/delimitar_terreno.html', {
        'establecimiento': establecimiento,
        'diseno': diseno,
        # Se pasan al template con el filtro json_script (forma segura de darle datos a JavaScript)
        'parcela_inicial': parcela_inicial,
        'centro_inicial': centro_inicial,
    })


@login_required
@require_POST
def guardar_diseno(request, pk):
    establecimiento = _establecimiento_del_usuario(request, pk)

    if len(request.body) > TAMANIO_MAXIMO_BYTES:
        return JsonResponse({'ok': False, 'mensaje': 'El diseño es demasiado grande.'}, status=400)

    # Validamos lo mínimo que necesitamos antes de guardar
    try:
        data = json.loads(request.body)
        metricas = data['metricas']
        parcela = data['geometrias']['parcela']
        area_total_ha = Decimal(str(metricas['area_total_ha']))
        porcentaje_floral = Decimal(str(data['diseno']['porcentaje_real']))
        if not isinstance(parcela, dict) or 'type' not in parcela:
            raise ValueError('La parcela no es un GeoJSON válido.')
    except (ValueError, KeyError, TypeError, InvalidOperation):
        return JsonResponse({'ok': False, 'mensaje': 'Los datos del diseño no son válidos.'}, status=400)

    diseno, _ = DisenoEspacial.objects.update_or_create(
        establecimiento=establecimiento,
        defaults={
            'datos': data,
            'tipo_diseno': str(data['diseno'].get('tipo') or '')[:30],
            'area_total_ha': area_total_ha,
            'porcentaje_floral': porcentaje_floral,
            'cumple_minimo_20': bool((data.get('diagnostico_espacial') or {}).get('cumple_minimo_20_pct')),
        },
    )
    return JsonResponse({
        'ok': True,
        'mensaje': 'Diseño guardado',
        'area_ha': float(diseno.area_total_ha),
    })
