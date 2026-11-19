from django.shortcuts import render

def panel_principal(request):
    # Calendario anual expresado en semanas (1 a 52) para Hemisferio Sur (Jujuy)
    especies = [
        # --- CULTIVOS ---
        {
            "id": "tomate",
            "nombre": "Tomate",
            "tipo": "cultivo",
            "tiempo_flor": "-",
            "fecha_max": "-",
            "nota": "Polinización por vibración (abejorros y abejas nativas).",
            "eventos": [
                {"clase": "flor-cultivo", "label": "Floración", "carril": 1, "rangos": [[40, 52], [1, 4]]},
                {"clase": "cosecha", "label": "Cosecha", "carril": 2, "rangos": [[49, 52], [1, 12]]},
            ],
        },
        {
            "id": "morron",
            "nombre": "Morrón",
            "tipo": "cultivo",
            "tiempo_flor": "-",
            "fecha_max": "-",
            "nota": "Mejora cuajado y tamaño del fruto con visitas de polinizadores.",
            "eventos": [
                {"clase": "flor-cultivo", "label": "Floración", "carril": 1, "rangos": [[42, 52], [1, 4]]},
                {"clase": "cosecha", "label": "Cosecha", "carril": 2, "rangos": [[1, 16]]},
            ],
        },
        {
            "id": "vid",
            "nombre": "Vid",
            "tipo": "cultivo",
            "tiempo_flor": "-",
            "fecha_max": "-",
            "nota": "Floración acotada en primavera; beneficia control biológico con corredores.",
            "eventos": [
                {"clase": "flor-cultivo", "label": "Floración", "carril": 1, "rangos": [[45, 50]]},
                {"clase": "cosecha", "label": "Cosecha", "carril": 2, "rangos": [[6, 13]]},
            ],
        },
        # --- FRANJAS FLORALES ---
        {
            "id": "calendula",
            "nombre": "Caléndula",
            "tipo": "floral",
            "tiempo_flor": "8–10 sem",
            "fecha_max": "Fin de Ago (Sem 35)",
            "nota": "Resiste frío moderado en Jujuy; atrae sírfidos y abejas.",
            "eventos": [
                {"clase": "plantado", "label": "Plantado (máx. Sem 35)", "carril": 1, "rangos": [[27, 35]]},
                {"clase": "flor-floral", "label": "Floración", "carril": 2, "rangos": [[36, 52]]},
            ],
        },
        {
            "id": "albahaca",
            "nombre": "Albahaca",
            "tipo": "floral",
            "tiempo_flor": "8–10 sem",
            "fecha_max": "Mediados Oct (Sem 42)",
            "nota": "Plantar tras riesgo de heladas; sostiene polinizadores en pleno verano.",
            "eventos": [
                {"clase": "plantado", "label": "Plantado (máx. Sem 42)", "carril": 1, "rangos": [[36, 42]]},
                {"clase": "flor-floral", "label": "Floración", "carril": 2, "rangos": [[45, 52], [1, 12]]},
            ],
        },
        {
            "id": "lavanda",
            "nombre": "Lavanda",
            "tipo": "floral",
            "tiempo_flor": "16–20 sem",
            "fecha_max": "Mediados Jul (Sem 28)",
            "nota": "Perenne resistente a sequía; ideal para bordes permanentes.",
            "eventos": [
                {"clase": "plantado", "label": "Plantado plantín (máx. Sem 28)", "carril": 1, "rangos": [[18, 28]]},
                {"clase": "flor-floral", "label": "Floración", "carril": 2, "rangos": [[40, 52], [1, 8]]},
            ],
        },
        {
            "id": "romero",
            "nombre": "Romero",
            "tipo": "floral",
            "tiempo_flor": "16–24 sem",
            "fecha_max": "Mediados May (Sem 20)",
            "nota": "Floración temprana; provee néctar al salir del invierno.",
            "eventos": [
                {"clase": "plantado", "label": "Plantado plantín (máx. Sem 20)", "carril": 1, "rangos": [[10, 20]]},
                {"clase": "flor-floral", "label": "Floración", "carril": 2, "rangos": [[32, 48]]},
            ],
        },
        {
            "id": "trebol",
            "nombre": "Trébol blanco",
            "tipo": "floral",
            "tiempo_flor": "10–12 sem",
            "fecha_max": "Fin de Ago (Sem 34)",
            "nota": "Cobertura viva entre hileras (excelente en Vid) y fijador de nitrógeno.",
            "eventos": [
                {"clase": "plantado", "label": "Siembra (máx. Sem 34)", "carril": 1, "rangos": [[27, 34]]},
                {"clase": "flor-floral", "label": "Floración", "carril": 2, "rangos": [[40, 52], [1, 8]]},
            ],
        },
        {
            "id": "mostaza",
            "nombre": "Mostaza blanca",
            "tipo": "floral",
            "tiempo_flor": "5–7 sem",
            "fecha_max": "Fin de Sep (Sem 39)",
            "nota": "Crecimiento muy rápido; útil para siembras tardías de emergencia.",
            "eventos": [
                {"clase": "plantado", "label": "Siembra rápida (máx. Sem 39)", "carril": 1, "rangos": [[33, 39]]},
                {"clase": "flor-floral", "label": "Floración", "carril": 2, "rangos": [[40, 51]]},
            ],
        },
    ]

    # recomendacion = None
    # if request.method == "POST":
    #     superficie = float(request.POST.get("superficie", 0))
    #     forma = request.POST.get("forma", "Rectangular")

    #     if superficie < 1000:
    #         recomendacion = (
    #             f"Lote pequeño ({superficie} m² - {forma}): Implementar 1 franja floral "
    #             "perimetral de 1.5 m de ancho con Caléndula y Albahaca para maximizar "
    #             "polinización sin restar área productiva."
    #         )
    #     elif 1000 <= superficie <= 5000:
    #         recomendacion = (
    #             f"Lote mediano ({superficie} m² - {forma}): Diseño en cuadrícula con "
    #             "franjas florales cada 25 metros y refugios perennes (Lavanda y Romero) en las esquinas."
    #         )
    #     else:
    #         recomendacion = (
    #             f"Lote extenso ({superficie} m² - {forma}): Corredores biológicos "
    #             "transversales de 3 m de ancho dividiendo el cultivo en bloques rotativos."
    #         )

    return render(request, "calendario/index.html", {
        "especies": especies,
        # "recomendacion": recomendacion,
    })
