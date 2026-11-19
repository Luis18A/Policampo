from django.shortcuts import render

# Create your views here.

def vista_mapa(request):
    return render(request, 'mapa/delimitar_terreno.html')