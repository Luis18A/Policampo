import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

def vista_mapa(request):
    return render(request, 'mapa/delimitar_terreno.html')

@require_POST
def guardar_diseno(request):
    data = json.loads(request.body)
    # data contiene: ubicacion, cultivo_principal, diseno, metricas,
    # diagnostico_espacial y geometrias (parcela, sectores_cultivo, corredores_florales)
    # Acá guardás en tus modelos (Parcela / PropuestaRedisenio)
    return JsonResponse({'ok': True, 'mensaje': 'Diseño recibido', 'area_ha': data['metricas']['area_total_ha']})