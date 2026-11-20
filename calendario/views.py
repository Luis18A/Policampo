from itertools import combinations
from django.shortcuts import render


def expandir_semanas(rangos):
    semanas = set()
    for inicio, fin in rangos:
        for s in range(inicio, fin + 1):
            semanas.add(s)
    return semanas


def generar_propuestas_por_cultivo(especies):
    cultivos = [e for e in especies if e["tipo"] == "cultivo"]
    florales = [e for e in especies if e["tipo"] == "floral"]

    propuestas_dict = {}

    for cult in cultivos:
        ev_flor = next(ev for ev in cult["eventos"] if ev["clase"] == "flor-cultivo")
        semanas_cultivo = expandir_semanas(ev_flor["rangos"])
        inicio_cultivo = ev_flor["rangos"][0][0]
        semana_anticipo = inicio_cultivo - 1 if inicio_cultivo > 1 else 52

        validas = []
        for f1, f2 in combinations(florales, 2):
            s1 = expandir_semanas(
                next(ev for ev in f1["eventos"] if ev["clase"] == "flor-floral")["rangos"]
            )
            s2 = expandir_semanas(
                next(ev for ev in f2["eventos"] if ev["clase"] == "flor-floral")["rangos"]
            )
            semanas_combo = s1 | s2

            # Regla 1: Florecer al menos 1 semana antes del cultivo
            cumple_anticipo = semana_anticipo in semanas_combo

            # Regla 2: Cubrir más del 80% de la floración del cultivo
            cubiertas = len(semanas_cultivo & semanas_combo)
            cobertura_pct = round((cubiertas / len(semanas_cultivo)) * 100, 1)

            if cumple_anticipo and cobertura_pct > 80:
                # Costo estimado cada 100 m² asumiendo mezcla 50% / 50% en superficie
                costo_100m2 = (
                    (50 * f1["densidad_gm2"] / 1000.0) * f1["costo_usd_kg"]
                    + (50 * f2["densidad_gm2"] / 1000.0) * f2["costo_usd_kg"]
                )
                perennes = int(f1["perenne"]) + int(f2["perenne"])
                validas.append({
                    "ids": [f1["id"], f2["id"]],
                    "nombres": f"{f1['nombre']} + {f2['nombre']}",
                    "especies": [
                        {
                            "id": f1["id"],
                            "nombre": f1["nombre"],
                            "densidad_gm2": f1["densidad_gm2"],
                            "costo_usd_kg": f1["costo_usd_kg"],
                            "fecha_max": f1["fecha_max"],
                            "perenne": f1["perenne"],
                            "nota_siembra": f1["nota_siembra"],
                        },
                        {
                            "id": f2["id"],
                            "nombre": f2["nombre"],
                            "densidad_gm2": f2["densidad_gm2"],
                            "costo_usd_kg": f2["costo_usd_kg"],
                            "fecha_max": f2["fecha_max"],
                            "perenne": f2["perenne"],
                            "nota_siembra": f2["nota_siembra"],
                        },
                    ],
                    "cobertura_pct": cobertura_pct,
                    "semanas_cubiertas": cubiertas,
                    "semanas_cultivo": len(semanas_cultivo),
                    "semana_anticipo": semana_anticipo,
                    "semanas_totales_flor": len(semanas_combo),
                    "costo_100m2": round(costo_100m2, 2),
                    "perennes": perennes,
                })

        # Propuesta 1: Mayor cobertura al menor costo de semilla
        validas_eco = sorted(validas, key=lambda x: (-x["cobertura_pct"], x["costo_100m2"]))
        seleccionadas = []
        if validas_eco:
            op1 = dict(validas_eco[0])
            op1["etiqueta"] = "Opción 1: Económica y rápida implantación"
            seleccionadas.append(op1)

            # Propuesta 2: Combinación distinta priorizando perennes / mayor ventana floral
            ids_op1 = set(op1["ids"])
            sin_repetir = [v for v in validas if set(v["ids"]).isdisjoint(ids_op1)]
            candidatas_op2 = sin_repetir if sin_repetir else [v for v in validas if v["ids"] != op1["ids"]]

            if candidatas_op2:
                op2 = dict(
                    sorted(
                        candidatas_op2,
                        key=lambda x: (-x["perennes"], -x["cobertura_pct"], -x["semanas_totales_flor"]),
                    )[0]
                )
                op2["etiqueta"] = "Opción 2: Alternativa de mayor persistencia / biodiversidad"
                seleccionadas.append(op2)

        propuestas_dict[cult["id"]] = seleccionadas

    return propuestas_dict


def panel_principal(request):
    especies = [
        # --- CULTIVOS ECONÓMICOS ---
        {
            "id": "tomate",
            "nombre": "Tomate",
            "tipo": "cultivo",
            "dist_max_m": 50,
            "tiempo_flor": "-",
            "fecha_max": "-",
            "nota": "Polinización por vibración (abejorros y abejas nativas). Espaciado recomendado <= 50 m.",
            "eventos": [
                {"clase": "flor-cultivo", "label": "Floración", "carril": 1, "rangos": [[40, 52], [1, 4]]},
                {"clase": "cosecha", "label": "Cosecha", "carril": 2, "rangos": [[49, 52], [1, 12]]},
            ],
        },
        {
            "id": "morron",
            "nombre": "Morrón",
            "tipo": "cultivo",
            "dist_max_m": 50,
            "tiempo_flor": "-",
            "fecha_max": "-",
            "nota": "Mejora cuajado y tamaño del fruto con visitas frecuentes. Espaciado recomendado <= 50 m.",
            "eventos": [
                {"clase": "flor-cultivo", "label": "Floración", "carril": 1, "rangos": [[42, 52], [1, 4]]},
                {"clase": "cosecha", "label": "Cosecha", "carril": 2, "rangos": [[1, 16]]},
            ],
        },
        {
            "id": "vid",
            "nombre": "Vid",
            "tipo": "cultivo",
            "dist_max_m": 75,
            "tiempo_flor": "-",
            "fecha_max": "-",
            "nota": "Floración acotada en primavera; referencia conservadora de abejas solitarias (100 m x 0.75 = 75 m).",
            "eventos": [
                {"clase": "flor-cultivo", "label": "Floración", "carril": 1, "rangos": [[45, 50]]},
                {"clase": "cosecha", "label": "Cosecha", "carril": 2, "rangos": [[6, 13]]},
            ],
        },
        # --- FRANJAS FLORALES (con densidad en g/m² y costo aprox USD/kg) ---
        {
            "id": "calendula",
            "nombre": "Caléndula",
            "tipo": "floral",
            "perenne": False,
            "densidad_gm2": 0.8,
            "costo_usd_kg": 35.0,
            "nota_siembra": "Siembra directa (6–10 kg/ha).",
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
            "perenne": False,
            "densidad_gm2": 0.3,
            "costo_usd_kg": 45.0,
            "nota_siembra": "Semilla fina, alto rendimiento por kg (2–4 kg/ha).",
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
            "perenne": True,
            "densidad_gm2": 0.15,
            "costo_usd_kg": 160.0,
            "nota_siembra": "Costo calculado en semilla; en campo suele recomendarse plantín (2–3/m²).",
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
            "perenne": True,
            "densidad_gm2": 0.15,
            "costo_usd_kg": 200.0,
            "nota_siembra": "Costo calculado en semilla; en campo suele recomendarse plantín (2–3/m²).",
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
            "perenne": True,
            "densidad_gm2": 0.6,
            "costo_usd_kg": 11.5,
            "nota_siembra": "Siembra al voleo (5–8 kg/ha); fija nitrógeno.",
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
            "perenne": False,
            "densidad_gm2": 1.2,
            "costo_usd_kg": 6.0,
            "nota_siembra": "Muy económica y de emergencia rápida (10–15 kg/ha).",
            "tiempo_flor": "5–7 sem",
            "fecha_max": "Fin de Sep (Sem 39)",
            "nota": "Crecimiento muy rápido; útil para siembras tardías de emergencia.",
            "eventos": [
                {"clase": "plantado", "label": "Siembra rápida (máx. Sem 39)", "carril": 1, "rangos": [[33, 39]]},
                {"clase": "flor-floral", "label": "Floración", "carril": 2, "rangos": [[40, 51]]},
            ],
        },
    ]

    propuestas = generar_propuestas_por_cultivo(especies)

    return render(request, "calendario/index.html", {
        "especies": especies,
        "propuestas": propuestas,
    })
