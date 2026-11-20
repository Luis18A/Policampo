import json
from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from campos.views import _establecimiento_del_usuario
from .models import DisenoEspacial

# Tope de tamaño del JSON que aceptamos (2 MB)
TAMANIO_MAXIMO_BYTES = 2 * 1024 * 1024


# ==========================================
# 1. PÁGINA DE ENTRADA (Carga de Terreno)
# ==========================================
@login_required
def registro_terreno(request, pk):
    """Muestra la interfaz para dibujar el contorno y los sectores."""
    # Seguridad: Verifica que el usuario sea el dueño del establecimiento
    establecimiento = _establecimiento_del_usuario(request, pk)

    return render(request, 'mapa/registro_terreno.html', {
        'establecimiento': establecimiento,
    })

@login_required
@require_POST
def guardar_terreno(request, pk):
    """Endpoint (API) que recibe los datos de Turf.js (Página 1) y los guarda."""
    establecimiento = _establecimiento_del_usuario(request, pk)

    if len(request.body) > TAMANIO_MAXIMO_BYTES:
        return JsonResponse({'ok': False, 'mensaje': 'El diseño es demasiado grande.'}, status=400)

    try:
        data = json.loads(request.body)
        
        # Guardamos el JSON con valores por defecto (en cero) para evitar el Error 500
        # en los campos obligatorios de la base de datos.
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
    except Exception as e:
        print(f"Error al guardar terreno: {e}") 
        return JsonResponse({'ok': False, 'mensaje': 'Error interno del servidor.'}, status=500)


# ==========================================
# 2. PÁGINA DE SALIDA (Propuesta de Rediseño)
# ==========================================
@login_required
def propuesta_redisenio(request, pk):
    """Muestra la propuesta de rediseño leyendo el JSON guardado en el paso 1."""
    establecimiento = _establecimiento_del_usuario(request, pk)
    
    diseno = DisenoEspacial.objects.filter(establecimiento=establecimiento).first()
    terreno_json = diseno.datos if diseno else None

    return render(request, 'mapa/propuesta_redisenio.html', {
        'establecimiento': establecimiento,
        'terreno_json': json.dumps(terreno_json) if terreno_json else None,
    })

@login_required
@require_POST
def guardar_propuesta(request, pk):
    """Endpoint (API) que guarda el rediseño final con franjas y métricas."""
    establecimiento = _establecimiento_del_usuario(request, pk)

    if len(request.body) > TAMANIO_MAXIMO_BYTES:
        return JsonResponse({'ok': False, 'mensaje': 'El diseño es demasiado grande.'}, status=400)

    try:
        data = json.loads(request.body)
        metricas = data.get('metricas', {})
        diseno_data = data.get('diseno', {})
        diag_espacial = data.get('diagnostico_espacial', {})
        
        area_total_ha = Decimal(str(metricas.get('area_total_ha', 0)))
        porcentaje_floral = Decimal(str(diseno_data.get('porcentaje_real', 0)))
        
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
    except Exception as e:
        print(f"Error al guardar propuesta: {e}")
        return JsonResponse({'ok': False, 'mensaje': 'Error interno.'}, status=500)