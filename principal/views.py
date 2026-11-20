from django.shortcuts import render


def inicio(request):
    """Página principal. Por ahora es provisoria: la landing real es la próxima etapa."""
    return render(request, "principal/inicio.html")
