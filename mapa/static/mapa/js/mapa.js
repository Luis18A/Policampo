/**
 * PoliCampo - Módulo de Mapa y Rediseño Espacial (Leaflet + Geoman + Turf.js)
 * ---------------------------------------------------------------------------
 * Diseñado para funcionar de forma independiente (prototipo HTML/JS) y listo
 * para integrarse en un template de Django mediante:
 *   1) Inputs ocultos dentro de un <form method="POST">
 *   2) Evento personalizado `policampo:disenoGuardado`
 *   3) `localStorage` (clave: `policampo_ultimo_diseno`) para conectar con los
 *      módulos de Recomendaciones e Informe en el prototipo
 *   4) Helper `enviarADjango(url, payload)` con soporte CSRF
 */

(function () {
    'use strict';

    // =========================================================================
    // 1. CATÁLOGO DE CULTIVOS Y PLANTAS DE SERVICIO (Base Jujuy - PoliCampo)
    // =========================================================================
    const CATALOGO_CULTIVOS = {
        frutilla: {
            nombre: 'Frutilla',
            color: '#e11d48',
            fillColor: '#fb7185',
            plantasServicio: 'Trigo sarraceno, Vicia, Caléndula y Borraja (atraen abejas nativas y sírfidos que mejoran el calibre y simetría del fruto).'
        },
        arandano: {
            nombre: 'Arándano',
            color: '#4f46e5',
            fillColor: '#818cf8',
            plantasServicio: 'Lavanda, Romero, Vicia y flora espontánea nativa (favorecen abejorros nativos clave para la polinización por vibración).'
        },
        durazno: {
            nombre: 'Durazno',
            color: '#ea580c',
            fillColor: '#fb923c',
            plantasServicio: 'Mostaza blanca, Hinojo, Trébol blanco y Vicia (floración temprana sincronizada previa a la floración del frutal).'
        },
        tomate: {
            nombre: 'Tomate',
            color: '#dc2626',
            fillColor: '#f87171',
            plantasServicio: 'Albahaca, Caléndula, Hinojo y Borraja (atraen abejorros nativos y enemigos naturales contra mosca blanca y pulgones).'
        },
        pimiento: {
            nombre: 'Pimiento',
            color: '#16a34a',
            fillColor: '#4ade80',
            plantasServicio: 'Trigo sarraceno, Cilantro en flor, Caléndula e Hinojo (refugio para parasitoides y abejas solitarias).'
        },
        palta: {
            nombre: 'Palta',
            color: '#15803d',
            fillColor: '#86efac',
            plantasServicio: 'Hinojo, Trigo sarraceno, Flora nativa de Yungas y Salvia (incrementan la tasa de cuajado en floración dicógama).'
        },
        horticolas: {
            nombre: 'Hortícolas mixtas',
            color: '#0d9488',
            fillColor: '#5eead4',
            plantasServicio: 'Banda mixta con Hinojo, Vicia, Caléndula, Trigo sarraceno y conservación de flora espontánea local.'
        }
    };

    const NOMBRES_DISPOSICION = {
        perimetral: 'Cerco Perimetral (Bordes)',
        transversal: 'Corredores Transversales (Franjas)',
        central: 'Islas de Biodiversidad (Grupos aislados)',
        matriz: 'Diseño en Matriz (Perimetral + Franjas)'
    };

    // Parcela de demostración en zona hortícola de Perico, Jujuy (~3.1 ha)
    const PARCELA_DEMO_PERICO = {
        type: 'Feature',
        properties: { nombre: 'Finca Ejemplo - Perico' },
        geometry: {
            type: 'Polygon',
            coordinates: [[
                [-65.1258, -24.3872],
                [-65.1235, -24.3870],
                [-65.1232, -24.3883],
                [-65.1243, -24.3885],
                [-65.1242, -24.3891],
                [-65.1259, -24.3889],
                [-65.1258, -24.3872]
            ]]
        }
    };

    // =========================================================================
    // 2. ESTADO DE LA APLICACIÓN
    // =========================================================================
    const state = {
        poligonoBaseLayer: null,
        poligonoBaseGeoJSON: null,
        propuestaGeoJSON: null,
        sectores: [], // [{ id, nombre, cultivoKey, geojson, areaM2 }]
        modoDibujo: 'parcela', // 'parcela' | 'sector'
        sectorPendienteGeoJSON: null,
        ultimoPayload: null,
        anchoBandaEstimadoM: null
    };

    // =========================================================================
    // 3. REFERENCIAS AL DOM
    // =========================================================================
    const dom = {
        selectorZona: document.getElementById('selector-zona'),
        btnMiUbicacion: document.getElementById('btn-mi-ubicacion'),
        buscadorLugar: document.getElementById('buscador-lugar'),
        btnBuscar: document.getElementById('btn-buscar'),
        estadoBusqueda: document.getElementById('estado-busqueda'),
        btnDibujarParcela: document.getElementById('btn-dibujar-parcela'),
        btnLimpiarTodo: document.getElementById('btn-limpiar-todo'),
        btnCargarDemo: document.getElementById('btn-cargar-demo'),
        btnImprimir: document.getElementById('btn-imprimir'),
        alertaGeometria: document.getElementById('alerta-geometria'),

        cultivoPrincipal: document.getElementById('cultivo-principal'),
        btnAgregarSector: document.getElementById('btn-agregar-sector'),
        listaSectores: document.getElementById('lista-sectores'),

        tipoFranja: document.getElementById('tipo-franja'),
        porcentajeSlider: document.getElementById('porcentaje-slider'),
        porcentajeInput: document.getElementById('porcentaje-area'),
        porcentajeLabel: document.getElementById('valor-porcentaje-label'),

        controlesTransversal: document.getElementById('controles-transversal'),
        numCorredores: document.getElementById('num-corredores'),
        numCorredoresLabel: document.getElementById('valor-corredores-label'),
        anguloCorredores: document.getElementById('angulo-corredores'),
        anguloCorredoresLabel: document.getElementById('valor-angulo-label'),
        chipsOrientacion: document.querySelectorAll('.chip[data-angulo]'),

        controlesIslas: document.getElementById('controles-islas'),
        densidadIslas: document.getElementById('densidad-islas'),
        densidadIslasLabel: document.getElementById('valor-islas-label'),

        fichaPlantas: document.getElementById('ficha-plantas'),
        textoPlantasSugeridas: document.getElementById('texto-plantas-sugeridas'),

        diagnosticoBanner: document.getElementById('diagnostico-banner'),
        areaTotal: document.getElementById('area-total'),
        areaTotalM2: document.getElementById('area-total-m2'),
        perimetroTotal: document.getElementById('perimetro-total'),
        anchoBanda: document.getElementById('ancho-banda'),
        areaProductiva: document.getElementById('area-productiva'),
        pctProductiva: document.getElementById('pct-productiva'),
        areaFranja: document.getElementById('area-franja'),
        pctFranja: document.getElementById('pct-franja'),

        btnGuardar: document.getElementById('btn-guardar'),
        btnDescargarGeoJSON: document.getElementById('btn-descargar-geojson'),
        btnVerJSON: document.getElementById('btn-ver-json'),

        inputParcela: document.getElementById('django-parcela-geojson'),
        inputPropuesta: document.getElementById('django-propuesta-geojson'),
        inputSectores: document.getElementById('django-sectores-geojson'),
        inputResumen: document.getElementById('django-resumen-json'),

        mapToast: document.getElementById('map-toast'),
        toggleParcela: document.getElementById('toggle-capa-parcela'),
        toggleSectores: document.getElementById('toggle-capa-sectores'),
        togglePropuesta: document.getElementById('toggle-capa-propuesta'),
        legendCultivoLabel: document.getElementById('legend-cultivo-label'),

        modalJson: document.getElementById('modal-json'),
        previewJsonCode: document.getElementById('preview-json-code'),
        btnCerrarModal: document.getElementById('btn-cerrar-modal'),
        btnCerrarModal2: document.getElementById('btn-cerrar-modal-2'),
        btnCopiarJson: document.getElementById('btn-copiar-json'),

        modalSector: document.getElementById('modal-sector'),
        sectorNombre: document.getElementById('sector-nombre'),
        sectorCultivo: document.getElementById('sector-cultivo'),
        btnCancelarSector: document.getElementById('btn-cancelar-sector'),
        btnCancelarSector2: document.getElementById('btn-cancelar-sector-2'),
        btnConfirmarSector: document.getElementById('btn-confirmar-sector')
    };

    // =========================================================================
    // 4. INICIALIZACIÓN DEL MAPA LEAFLET Y CAPAS BASE
    // =========================================================================
    // [Integración] Si el template define POLICAMPO_CENTRO_INICIAL (la ubicación cargada en el mapa
    // geográfico de Sol), el mapa arranca ahí. Si no, usa el centro original (San Salvador de Jujuy).
    const centroInicial = window.POLICAMPO_CENTRO_INICIAL;
    const map = L.map('mapa', {
        center: centroInicial ? [centroInicial.lat, centroInicial.lng] : [-24.1858, -65.2995],
        zoom: centroInicial ? centroInicial.zoom : 13,
        zoomControl: true
    });

    // Capas base: Satélite, Híbrido (Satélite + Etiquetas) y Callejero (OSM)
    const capaSatelite = L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        { attribution: 'Imágenes &copy; Esri', maxZoom: 19 }
    );

    const capaEtiquetas = L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
        { attribution: '&copy; Esri', maxZoom: 19 }
    );

    const capaHibrido = L.layerGroup([
        L.tileLayer(
            'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            { attribution: 'Imágenes &copy; Esri', maxZoom: 19 }
        ),
        capaEtiquetas
    ]);

    const capaCalles = L.tileLayer(
        'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        { attribution: '&copy; OpenStreetMap contributors', maxZoom: 19 }
    );

    // Iniciamos en Híbrido (satélite + nombres de localidades/rutas para ubicar fincas fácilmente)
    capaHibrido.addTo(map);

    L.control.layers(
        {
            '🛰️ Satélite + Etiquetas': capaHibrido,
            '🌍 Satélite puro': capaSatelite,
            '🗺️ Mapa de calles (OSM)': capaCalles
        },
        null,
        { position: 'topright' }
    ).addTo(map);

    L.control.scale({ metric: true, imperial: false, position: 'bottomleft' }).addTo(map);

    // Grupos de capas vectoriales
    const capaPoligonos = L.featureGroup().addTo(map);
    const capaSectores = L.featureGroup().addTo(map);
    const capaPropuesta = L.featureGroup().addTo(map);

    // Configuración de Leaflet-Geoman en español
    map.pm.setLang('es');
    map.pm.addControls({
        position: 'topleft',
        drawMarker: false,
        drawCircleMarker: false,
        drawPolyline: false,
        drawCircle: false,
        drawText: false,
        cutPolygon: false,
        rotateMode: false,
        drawPolygon: true,
        drawRectangle: true,
        editMode: true,
        dragMode: true,
        removalMode: true
    });

    // =========================================================================
    // 5. UTILIDADES DE INTERFAZ (TOASTS, ALERTAS, FORMATO)
    // =========================================================================
    let toastTimer = null;
    function mostrarToast(mensaje, duracionMs = 3800) {
        dom.mapToast.textContent = mensaje;
        dom.mapToast.classList.remove('oculto');
        clearTimeout(toastTimer);
        if (duracionMs > 0) {
            toastTimer = setTimeout(() => {
                dom.mapToast.classList.add('oculto');
            }, duracionMs);
        }
    }

    function ocultarToast() {
        clearTimeout(toastTimer);
        dom.mapToast.classList.add('oculto');
    }

    function mostrarAlertaGeometria(mensaje) {
        if (!mensaje) {
            dom.alertaGeometria.classList.add('oculto');
            dom.alertaGeometria.textContent = '';
            return;
        }
        dom.alertaGeometria.textContent = mensaje;
        dom.alertaGeometria.classList.remove('oculto');
    }

    function formatearNumero(valor, decimales = 2) {
        return Number(valor || 0).toLocaleString('es-AR', {
            minimumFractionDigits: decimales,
            maximumFractionDigits: decimales
        });
    }

    function describirAngulo(grados) {
        const g = Number(grados);
        if (g === 0 || g === 180) return `${g}° (N-S)`;
        if (g === 90) return `${g}° (E-O)`;
        if (g === 45) return `${g}° (NE-SO)`;
        if (g === 135) return `${g}° (NO-SE)`;
        return `${g}°`;
    }

    // =========================================================================
    // 6. VALIDACIÓN Y GESTIÓN DE LA PARCELA PRINCIPAL
    // =========================================================================
    function establecerControlesHabilitados(habilitado) {
        const elementos = [
            dom.btnLimpiarTodo,
            dom.cultivoPrincipal,
            dom.btnAgregarSector,
            dom.tipoFranja,
            dom.porcentajeSlider,
            dom.porcentajeInput,
            dom.numCorredores,
            dom.anguloCorredores,
            dom.densidadIslas,
            dom.btnGuardar,
            dom.btnDescargarGeoJSON,
            dom.btnVerJSON
        ];
        elementos.forEach((el) => {
            if (el) el.disabled = !habilitado;
        });
    }

    function obtenerEstiloParcela() {
        const cultivo = CATALOGO_CULTIVOS[dom.cultivoPrincipal.value] || CATALOGO_CULTIVOS.horticolas;
        return {
            color: cultivo.color,
            weight: 3,
            fillColor: cultivo.fillColor,
            fillOpacity: 0.24
        };
    }

    function validarPoligono(geojson) {
        try {
            const limpio = turf.cleanCoords(geojson);
            const area = turf.area(limpio);
            if (!area || area < 50) {
                return {
                    valido: false,
                    error: 'El polígono dibujado es demasiado pequeño (mínimo 50 m²).'
                };
            }
            const kinks = turf.kinks(limpio);
            if (kinks && kinks.features && kinks.features.length > 0) {
                return {
                    valido: false,
                    error: 'El contorno se cruza consigo mismo. Editá los vértices para eliminar cruces.'
                };
            }
            return { valido: true, geojson: limpio };
        } catch (err) {
            return {
                valido: false,
                error: 'No se pudo procesar la geometría del terreno. Probá dibujarlo nuevamente.'
            };
        }
    }

    function vincularEventosParcela(layer) {
        layer.on('pm:edit', () => {
            actualizarDesdeLayerBase();
        });
        layer.on('pm:dragend', () => {
            actualizarDesdeLayerBase();
        });
    }

    function actualizarDesdeLayerBase() {
        if (!state.poligonoBaseLayer) return;
        const rawGeoJSON = state.poligonoBaseLayer.toGeoJSON();
        const validacion = validarPoligono(rawGeoJSON);

        if (!validacion.valido) {
            mostrarAlertaGeometria(validacion.error);
            capaPropuesta.clearLayers();
            state.propuestaGeoJSON = null;
            return;
        }

        mostrarAlertaGeometria(null);
        state.poligonoBaseGeoJSON = validacion.geojson;

        // Re-recortar sectores internos si la parcela cambió de forma
        reRecortarSectores();
        generarDiseno();
    }

    function cargarParcelaBase(layer, ajustarVista = false) {
        capaPoligonos.clearLayers();
        capaPropuesta.clearLayers();
        capaSectores.clearLayers();
        state.sectores = [];

        layer.setStyle(obtenerEstiloParcela());
        capaPoligonos.addLayer(layer);
        state.poligonoBaseLayer = layer;
        vincularEventosParcela(layer);

        establecerControlesHabilitados(true);
        actualizarControlesDinamicos();
        actualizarListaSectores();
        actualizarFichaCultivo();

        actualizarDesdeLayerBase();

        if (ajustarVista) {
            map.fitBounds(layer.getBounds(), { padding: [45, 45] });
        }
    }

    function limpiarTodo() {
        map.pm.disableDraw();
        map.pm.disableGlobalEditMode();
        map.pm.disableGlobalDragMode();
        map.pm.disableGlobalRemovalMode();

        capaPoligonos.clearLayers();
        capaSectores.clearLayers();
        capaPropuesta.clearLayers();

        state.poligonoBaseLayer = null;
        state.poligonoBaseGeoJSON = null;
        state.propuestaGeoJSON = null;
        state.sectores = [];
        state.ultimoPayload = null;
        state.anchoBandaEstimadoM = null;
        state.modoDibujo = 'parcela';

        establecerControlesHabilitados(false);
        mostrarAlertaGeometria(null);
        dom.fichaPlantas.classList.add('oculto');
        actualizarListaSectores();

        // Resetear métricas y diagnóstico
        dom.areaTotal.textContent = '0.00 ha';
        dom.areaTotalM2.textContent = '0 m²';
        dom.perimetroTotal.textContent = '0 m';
        dom.anchoBanda.textContent = 'Ancho banda: —';
        dom.areaProductiva.textContent = '0.00 ha';
        dom.pctProductiva.textContent = '0.0%';
        dom.areaFranja.textContent = '0.00 ha';
        dom.pctFranja.textContent = '0.0%';

        dom.diagnosticoBanner.className = 'diagnostico-banner neutro';
        dom.diagnosticoBanner.textContent = 'Dibujá tu parcela en el mapa para calcular el diagnóstico espacial.';

        dom.inputParcela.value = '';
        dom.inputPropuesta.value = '';
        dom.inputSectores.value = '';
        dom.inputResumen.value = '';

        mostrarToast('Mapa reiniciado. Dibujá un nuevo terreno para comenzar.');
    }

    // =========================================================================
    // 7. ALGORITMOS GEOESPACIALES DE CORREDORES FLORALES (Turf.js v6)
    // =========================================================================

    /**
     * Calcula una banda perimetral de ancho uniforme mediante buffer negativo
     * calibrado por búsqueda binaria para coincidir con la proporción objetivo.
     */
    function calcularPerimetral(poligono, proporcion) {
        const areaTotal = turf.area(poligono);
        const areaInternaObjetivo = areaTotal * (1 - proporcion);

        const bbox = turf.bbox(poligono);
        const anchoM = turf.distance([bbox[0], bbox[1]], [bbox[2], bbox[1]], { units: 'meters' });
        const altoM = turf.distance([bbox[0], bbox[1]], [bbox[0], bbox[3]], { units: 'meters' });
        const maxRadio = Math.max(Math.min(anchoM, altoM) * 0.55, 5);

        let lo = 0;
        let hi = maxRadio;
        let mejorInner = null;
        let mejorDist = 0;
        let mejorError = Infinity;

        for (let i = 0; i < 16; i++) {
            const mid = (lo + hi) / 2;
            let inner = null;
            let areaInner = 0;

            try {
                inner = turf.buffer(poligono, -mid, { units: 'meters' });
                if (inner && inner.geometry && inner.geometry.coordinates && inner.geometry.coordinates.length > 0) {
                    areaInner = turf.area(inner);
                }
            } catch (e) {
                areaInner = 0;
            }

            const error = Math.abs(areaInner - areaInternaObjetivo);
            if (areaInner > 1 && error < mejorError) {
                mejorError = error;
                mejorInner = inner;
                mejorDist = mid;
            }

            if (areaInner > areaInternaObjetivo) {
                lo = mid;
            } else {
                hi = mid;
            }
        }

        // Si el buffer interno es válido, restamos para obtener la franja perimetral
        if (mejorInner) {
            try {
                const franja = turf.difference(poligono, mejorInner);
                if (franja && turf.area(franja) > 1) {
                    franja.properties = {
                        subtipo: 'perimetral',
                        etiqueta: 'Cerco Perimetral Floral',
                        ancho_estimado_m: Number(mejorDist.toFixed(1))
                    };
                    return {
                        features: [franja],
                        innerPolygon: mejorInner,
                        anchoEstimadoM: mejorDist
                    };
                }
            } catch (e) {
                // Continúa al fallback
            }
        }

        // Fallback por escalado si la parcela tiene una geometría muy delgada
        const factorEscala = Math.sqrt(Math.max(1 - proporcion, 0.05));
        const reducido = turf.transformScale(poligono, factorEscala);
        const franjaFallback = turf.difference(poligono, reducido);
        if (franjaFallback) {
            franjaFallback.properties = {
                subtipo: 'perimetral',
                etiqueta: 'Cerco Perimetral Floral'
            };
        }
        return {
            features: franjaFallback ? [franjaFallback] : [],
            innerPolygon: reducido,
            anchoEstimadoM: null
        };
    }

    /**
     * Genera N corredores paralelos con orientación personalizable (0° - 165°)
     * calibrando el ancho para aproximar con precisión el porcentaje objetivo.
     */
    function calcularTransversales(poligono, proporcion, numCorredores, angulo) {
        const areaTotal = turf.area(poligono);
        const areaObjetivo = areaTotal * proporcion;
        const centro = turf.centerOfMass(poligono);

        // Rotamos el polígono para cortar verticalmente y luego devolvemos al ángulo original
        const rotado = angulo !== 0
            ? turf.transformRotate(poligono, -angulo, { pivot: centro })
            : poligono;

        const bbox = turf.bbox(rotado);
        const minX = bbox[0];
        const minY = bbox[1];
        const maxX = bbox[2];
        const maxY = bbox[3];
        const anchoDeg = maxX - minX;
        const margenY = (maxY - minY) * 0.1;
        const anchoSeccionDeg = anchoDeg / numCorredores;

        const anchoTotalM = turf.distance(
            [minX, (minY + maxY) / 2],
            [maxX, (minY + maxY) / 2],
            { units: 'meters' }
        );

        function construirFranjas(ratio) {
            const anchoFranja = anchoSeccionDeg * ratio;
            const lista = [];
            let areaAcumulada = 0;

            for (let i = 0; i < numCorredores; i++) {
                const centroX = minX + (i + 0.5) * anchoSeccionDeg;
                const x1 = centroX - anchoFranja / 2;
                const x2 = centroX + anchoFranja / 2;

                const mascara = turf.polygon([[
                    [x1, minY - margenY],
                    [x2, minY - margenY],
                    [x2, maxY + margenY],
                    [x1, maxY + margenY],
                    [x1, minY - margenY]
                ]]);

                try {
                    const inter = turf.intersect(rotado, mascara);
                    if (inter) {
                        const a = turf.area(inter);
                        if (a > 1) {
                            areaAcumulada += a;
                            lista.push({ feature: inter, indice: i + 1 });
                        }
                    }
                } catch (e) {
                    // Ignora intersección degenerada
                }
            }
            return { lista, areaAcumulada };
        }

        // Búsqueda binaria del ratio de ancho de franja para alcanzar el % exacto
        let lo = 0.01;
        let hi = 0.96;
        let mejor = construirFranjas(proporcion);
        let mejorRatio = proporcion;
        let mejorError = Math.abs(mejor.areaAcumulada - areaObjetivo);

        for (let iter = 0; iter < 10; iter++) {
            const mid = (lo + hi) / 2;
            const res = construirFranjas(mid);
            const err = Math.abs(res.areaAcumulada - areaObjetivo);
            if (err < mejorError) {
                mejorError = err;
                mejor = res;
                mejorRatio = mid;
            }
            if (res.areaAcumulada < areaObjetivo) {
                lo = mid;
            } else {
                hi = mid;
            }
        }

        const anchoEstimadoM = (anchoTotalM / numCorredores) * mejorRatio;

        const features = mejor.lista.map(({ feature, indice }) => {
            const finalFeat = angulo !== 0
                ? turf.transformRotate(feature, angulo, { pivot: centro })
                : feature;
            finalFeat.properties = {
                subtipo: 'transversal',
                etiqueta: `Corredor Transversal #${indice}`,
                orientacion_grados: angulo,
                ancho_estimado_m: Number(anchoEstimadoM.toFixed(1))
            };
            return finalFeat;
        });

        return { features, anchoEstimadoM };
    }

    /**
     * Genera islas de biodiversidad distribuidas en cuadrícula adaptada
     * dinámicamente a las dimensiones reales del lote (funciona desde 0.1 ha hasta >50 ha).
     */
    function calcularIslas(poligono, proporcion, divisiones) {
        const bbox = turf.bbox(poligono);
        const minX = bbox[0];
        const minY = bbox[1];
        const maxX = bbox[2];
        const maxY = bbox[3];

        const anchoM = turf.distance([minX, minY], [maxX, minY], { units: 'meters' });
        const altoM = turf.distance([minX, minY], [minX, maxY], { units: 'meters' });

        // Ajustar filas/columnas según la relación de aspecto del terreno
        const cols = divisiones;
        const rows = Math.max(1, Math.round(divisiones * (altoM / Math.max(anchoM, 1))));
        const stepX = (maxX - minX) / cols;
        const stepY = (maxY - minY) / rows;

        const celdasRecortadas = [];
        for (let r = 0; r < rows; r++) {
            for (let c = 0; c < cols; c++) {
                const x1 = minX + c * stepX;
                const x2 = x1 + stepX;
                const y1 = minY + r * stepY;
                const y2 = y1 + stepY;

                const celda = turf.polygon([[
                    [x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1, y1]
                ]]);

                try {
                    const inter = turf.intersect(poligono, celda);
                    if (inter && turf.area(inter) > 10) {
                        celdasRecortadas.push(inter);
                    }
                } catch (e) {
                    // Ignora celda degenerada
                }
            }
        }

        const escala = Math.sqrt(proporcion);
        const islas = [];
        let contador = 1;

        celdasRecortadas.forEach((celda) => {
            try {
                const pivote = turf.centerOfMass(celda);
                const escalada = turf.transformScale(celda, escala, { origin: pivote });
                // Asegurar que ninguna isla sobresalga en terrenos cóncavos
                const segura = turf.intersect(poligono, escalada);
                if (segura && turf.area(segura) > 4) {
                    segura.properties = {
                        subtipo: 'isla',
                        etiqueta: `Isla de Biodiversidad #${contador++}`
                    };
                    islas.push(segura);
                }
            } catch (e) {
                // Continúa con siguiente celda
            }
        });

        return { features: islas, anchoEstimadoM: null };
    }

    /**
     * Diseño en Matriz (mencionado en relevamiento PoliCampo):
     * Combina 50% en cerco perimetral + 50% en franjas internas sin solapamientos.
     */
    function calcularMatriz(poligono, proporcion, numCorredores, angulo) {
        const resPerimetro = calcularPerimetral(poligono, proporcion * 0.5);
        const features = [...resPerimetro.features];

        // Sobre el polígono interno restante calculamos las franjas para evitar solapamiento
        if (resPerimetro.innerPolygon && turf.area(resPerimetro.innerPolygon) > 20) {
            const areaTotal = turf.area(poligono);
            const areaInterna = turf.area(resPerimetro.innerPolygon);
            const propSobreInterna = Math.min((areaTotal * proporcion * 0.5) / areaInterna, 0.85);

            const resInternas = calcularTransversales(
                resPerimetro.innerPolygon,
                propSobreInterna,
                numCorredores,
                angulo
            );
            resInternas.features.forEach((f) => {
                f.properties.subtipo = 'matriz_corredor';
                features.push(f);
            });
        }

        return {
            features,
            anchoEstimadoM: resPerimetro.anchoEstimadoM
        };
    }

    // =========================================================================
    // 8. GENERACIÓN DEL REDISEÑO, MÉTRICAS Y DIAGNÓSTICO
    // =========================================================================
    function generarDiseno() {
        if (!state.poligonoBaseGeoJSON) return;

        const poligono = state.poligonoBaseGeoJSON;
        const tipo = dom.tipoFranja.value;
        let porcentaje = parseFloat(dom.porcentajeInput.value);
        if (Number.isNaN(porcentaje)) porcentaje = 20;
        porcentaje = Math.min(Math.max(porcentaje, 1), 60);

        const proporcion = porcentaje / 100;
        const numCorredores = parseInt(dom.numCorredores.value, 10) || 3;
        const angulo = parseInt(dom.anguloCorredores.value, 10) || 0;
        const divisionesIslas = parseInt(dom.densidadIslas.value, 10) || 3;

        let resultado = { features: [], anchoEstimadoM: null };

        try {
            if (tipo === 'perimetral') {
                resultado = calcularPerimetral(poligono, proporcion);
            } else if (tipo === 'transversal') {
                resultado = calcularTransversales(poligono, proporcion, numCorredores, angulo);
            } else if (tipo === 'central') {
                resultado = calcularIslas(poligono, proporcion, divisionesIslas);
            } else if (tipo === 'matriz') {
                resultado = calcularMatriz(poligono, proporcion, numCorredores, angulo);
            }
        } catch (err) {
            console.error('Error al calcular corredores florales:', err);
            mostrarAlertaGeometria('Ocurrió un problema calculando el rediseño. Probá simplificar el contorno del terreno.');
            return;
        }

        state.anchoBandaEstimadoM = resultado.anchoEstimadoM;

        const featureCollection = turf.featureCollection(resultado.features);
        state.propuestaGeoJSON = featureCollection;

        // Cálculos reales a partir de la geometría generada
        const areaTotalM2 = turf.area(poligono);
        const areaTotalHa = areaTotalM2 / 10000;
        const perimetroM = turf.length(turf.polygonToLine(poligono), { units: 'kilometers' }) * 1000;

        const areaFranjaM2 = featureCollection.features.reduce((acc, f) => acc + turf.area(f), 0);
        const areaFranjaHa = areaFranjaM2 / 10000;
        const pctRealFloral = areaTotalM2 > 0 ? (areaFranjaM2 / areaTotalM2) * 100 : 0;

        const areaProductivaM2 = Math.max(areaTotalM2 - areaFranjaM2, 0);
        const areaProductivaHa = areaProductivaM2 / 10000;
        const pctRealProductiva = Math.max(100 - pctRealFloral, 0);

        // Actualizar métricas en UI
        dom.areaTotal.textContent = `${formatearNumero(areaTotalHa, 2)} ha`;
        dom.areaTotalM2.textContent = `${formatearNumero(areaTotalM2, 0)} m²`;
        dom.perimetroTotal.textContent = `${formatearNumero(perimetroM, 0)} m`;
        dom.anchoBanda.textContent = resultado.anchoEstimadoM
            ? `Ancho banda: ~${formatearNumero(resultado.anchoEstimadoM, 1)} m`
            : `Zonas florales: ${featureCollection.features.length}`;

        dom.areaProductiva.textContent = `${formatearNumero(areaProductivaHa, 2)} ha`;
        dom.pctProductiva.textContent = `${formatearNumero(pctRealProductiva, 1)}%`;

        dom.areaFranja.textContent = `${formatearNumero(areaFranjaHa, 2)} ha`;
        dom.pctFranja.textContent = `${formatearNumero(pctRealFloral, 1)}%`;

        // Diagnóstico según regla del 20% (Garibaldi et al.)
        const diagnostico = evaluarDiagnostico(pctRealFloral);
        dom.diagnosticoBanner.className = `diagnostico-banner ${diagnostico.clase}`;
        dom.diagnosticoBanner.textContent = diagnostico.mensaje;

        // Dibujar capa de corredores florales con popups informativos
        renderizarPropuesta(featureCollection);

        // Preparar payload estructurado e inyectar en inputs ocultos para Django
        actualizarPayloadDjango({
            areaTotalM2,
            areaTotalHa,
            perimetroM,
            areaFranjaM2,
            areaFranjaHa,
            pctRealFloral,
            areaProductivaHa,
            pctRealProductiva,
            porcentajeObjetivo: porcentaje,
            tipo,
            numCorredores,
            angulo,
            divisionesIslas,
            anchoEstimadoM: resultado.anchoEstimadoM,
            diagnostico
        });
    }

    function evaluarDiagnostico(pctReal) {
        if (pctReal >= 19.5) {
            return {
                estado: 'OPTIMO',
                clase: 'optimo',
                mensaje: `✅ Óptimo (${formatearNumero(pctReal, 1)}%): cumple con la recomendación agroecológica de al menos 20% para polinizadores y control biológico.`
            };
        }
        if (pctReal >= 10) {
            return {
                estado: 'PARCIAL',
                clase: 'alerta',
                mensaje: `⚠️ Por debajo del mínimo (${formatearNumero(pctReal, 1)}%): se recomienda alcanzar el 20% para maximizar visitas de polinizadores.`
            };
        }
        return {
            estado: 'DEFICIT',
            clase: 'critico',
            mensaje: `🚨 Déficit crítico de biodiversidad (${formatearNumero(pctReal, 1)}%): la superficie floral es insuficiente para sostener fauna benéfica.`
        };
    }

    function renderizarPropuesta(featureCollection) {
        capaPropuesta.clearLayers();
        const cultivo = CATALOGO_CULTIVOS[dom.cultivoPrincipal.value] || CATALOGO_CULTIVOS.horticolas;

        L.geoJSON(featureCollection, {
            pmIgnore: true,
            style: (feature) => {
                const esBorde = feature.properties && feature.properties.subtipo === 'perimetral';
                return {
                    pmIgnore: true,
                    color: '#be185d',
                    weight: esBorde ? 2.5 : 2,
                    fillColor: '#ec4899',
                    fillOpacity: 0.52,
                    dashArray: esBorde ? '6, 4' : '4, 5'
                };
            },
            onEachFeature: (feature, layer) => {
                layer.options.pmIgnore = true;
                const areaM2 = turf.area(feature);
                const areaHa = areaM2 / 10000;
                const titulo = (feature.properties && feature.properties.etiqueta) || 'Corredor Floral';
                const anchoInfo = feature.properties && feature.properties.ancho_estimado_m
                    ? `<br><strong>Ancho aprox.:</strong> ${feature.properties.ancho_estimado_m} m`
                    : '';

                layer.bindPopup(`
                    <div style="font-family: Inter, sans-serif; font-size: 12.5px; line-height: 1.4;">
                        <strong style="color:#9d174d;">🌼 ${titulo}</strong><br>
                        <strong>Superficie:</strong> ${formatearNumero(areaHa, 3)} ha (${formatearNumero(areaM2, 0)} m²)${anchoInfo}<br>
                        <strong>Sugerencia floral:</strong> ${cultivo.plantasServicio}
                    </div>
                `);
            }
        }).addTo(capaPropuesta);

        // Asegurar que la capa de propuesta quede arriba de parcela y sectores
        capaPropuesta.bringToFront();
    }

    // =========================================================================
    // 9. SECTORES INTERNOS DE CULTIVO
    // =========================================================================
    function reRecortarSectores() {
        if (!state.poligonoBaseGeoJSON || state.sectores.length === 0) return;

        const actualizados = [];
        state.sectores.forEach((sec) => {
            try {
                const recortado = turf.intersect(state.poligonoBaseGeoJSON, sec.geojson);
                if (recortado && turf.area(recortado) > 20) {
                    actualizados.push({
                        ...sec,
                        geojson: recortado,
                        areaM2: turf.area(recortado)
                    });
                }
            } catch (e) {
                // Si el sector quedó fuera tras editar la parcela, se omite
            }
        });

        state.sectores = actualizados;
        renderizarSectores();
        actualizarListaSectores();
    }

    function renderizarSectores() {
        capaSectores.clearLayers();

        state.sectores.forEach((sec) => {
            const infoCultivo = CATALOGO_CULTIVOS[sec.cultivoKey] || CATALOGO_CULTIVOS.horticolas;
            const geoLayer = L.geoJSON(sec.geojson, {
                pmIgnore: true,
                style: {
                    pmIgnore: true,
                    color: infoCultivo.color,
                    weight: 2,
                    fillColor: infoCultivo.fillColor,
                    fillOpacity: 0.42
                },
                onEachFeature: (feature, layer) => {
                    layer.options.pmIgnore = true;
                }
            });

            geoLayer.bindPopup(`
                <div style="font-family: Inter, sans-serif; font-size: 12.5px;">
                    <strong>🌱 ${sec.nombre}</strong><br>
                    <strong>Cultivo:</strong> ${infoCultivo.nombre}<br>
                    <strong>Superficie:</strong> ${formatearNumero(sec.areaM2 / 10000, 2)} ha (${formatearNumero(sec.areaM2, 0)} m²)
                </div>
            `);

            geoLayer.addTo(capaSectores);
        });

        capaPropuesta.bringToFront();
    }

    function actualizarListaSectores() {
        dom.listaSectores.innerHTML = '';

        if (state.sectores.length === 0) {
            dom.listaSectores.innerHTML = '<li class="lista-vacia">Sin sectores divididos (100% cultivo principal)</li>';
            return;
        }

        state.sectores.forEach((sec) => {
            const cultivo = CATALOGO_CULTIVOS[sec.cultivoKey] || CATALOGO_CULTIVOS.horticolas;
            const li = document.createElement('li');
            li.className = 'sector-item';
            li.innerHTML = `
                <div class="sector-info">
                    <span class="sector-dot" style="background:${cultivo.color};"></span>
                    <div>
                        <strong>${sec.nombre}</strong> · ${cultivo.nombre}
                        <span style="color:#64748b;">(${formatearNumero(sec.areaM2 / 10000, 2)} ha)</span>
                    </div>
                </div>
                <button type="button" class="btn-del-sector" title="Eliminar sector" data-id="${sec.id}">&times;</button>
            `;
            dom.listaSectores.appendChild(li);
        });
    }

    function abrirModalSector(geojsonRecortado) {
        state.sectorPendienteGeoJSON = geojsonRecortado;
        dom.sectorNombre.value = `Sector ${state.sectores.length + 1}`;
        dom.sectorCultivo.value = dom.cultivoPrincipal.value;
        dom.modalSector.classList.remove('oculto');
        dom.sectorNombre.focus();
    }

    function cerrarModalSector() {
        state.sectorPendienteGeoJSON = null;
        dom.modalSector.classList.add('oculto');
        state.modoDibujo = 'parcela';
    }

    // =========================================================================
    // 10. EXPORTACIÓN E INTEGRACIÓN CON DJANGO
    // =========================================================================
    function actualizarPayloadDjango(metricas) {
        const centroide = turf.centerOfMass(state.poligonoBaseGeoJSON);
        const cultivoKey = dom.cultivoPrincipal.value;
        const cultivoInfo = CATALOGO_CULTIVOS[cultivoKey] || CATALOGO_CULTIVOS.horticolas;

        const sectoresFC = turf.featureCollection(
            state.sectores.map((s) => ({
                ...s.geojson,
                properties: {
                    id: s.id,
                    nombre: s.nombre,
                    cultivo: s.cultivoKey,
                    cultivo_nombre: (CATALOGO_CULTIVOS[s.cultivoKey] || {}).nombre || s.cultivoKey,
                    area_ha: Number((s.areaM2 / 10000).toFixed(4))
                }
            }))
        );

        const payload = {
            version: '1.0',
            timestamp: new Date().toISOString(),
            ubicacion: {
                lat: Number(centroide.geometry.coordinates[1].toFixed(6)),
                lng: Number(centroide.geometry.coordinates[0].toFixed(6)),
                zona_seleccionada: dom.selectorZona.options[dom.selectorZona.selectedIndex].text
            },
            cultivo_principal: {
                codigo: cultivoKey,
                nombre: cultivoInfo.nombre
            },
            diseno: {
                tipo: metricas.tipo,
                tipo_nombre: NOMBRES_DISPOSICION[metricas.tipo],
                porcentaje_objetivo: metricas.porcentajeObjetivo,
                porcentaje_real: Number(metricas.pctRealFloral.toFixed(2)),
                cantidad_corredores: metricas.tipo === 'transversal' || metricas.tipo === 'matriz' ? metricas.numCorredores : null,
                orientacion_grados: metricas.tipo === 'transversal' || metricas.tipo === 'matriz' ? metricas.angulo : null,
                divisiones_islas: metricas.tipo === 'central' ? metricas.divisionesIslas : null,
                ancho_banda_estimado_m: metricas.anchoEstimadoM ? Number(metricas.anchoEstimadoM.toFixed(2)) : null
            },
            metricas: {
                area_total_ha: Number(metricas.areaTotalHa.toFixed(4)),
                area_total_m2: Math.round(metricas.areaTotalM2),
                perimetro_m: Math.round(metricas.perimetroM),
                area_productiva_ha: Number(metricas.areaProductivaHa.toFixed(4)),
                area_corredores_ha: Number(metricas.areaFranjaHa.toFixed(4)),
                area_corredores_m2: Math.round(metricas.areaFranjaM2)
            },
            diagnostico_espacial: {
                estado: metricas.diagnostico.estado,
                cumple_minimo_20_pct: metricas.pctRealFloral >= 19.5,
                mensaje: metricas.diagnostico.mensaje
            },
            geometrias: {
                parcela: state.poligonoBaseGeoJSON,
                sectores_cultivo: sectoresFC,
                corredores_florales: state.propuestaGeoJSON
            }
        };

        state.ultimoPayload = payload;

        // Completar inputs ocultos para formularios Django
        dom.inputParcela.value = JSON.stringify(payload.geometrias.parcela);
        dom.inputPropuesta.value = JSON.stringify(payload.geometrias.corredores_florales);
        dom.inputSectores.value = JSON.stringify(payload.geometrias.sectores_cultivo);
        dom.inputResumen.value = JSON.stringify({
            ubicacion: payload.ubicacion,
            cultivo_principal: payload.cultivo_principal,
            diseno: payload.diseno,
            metricas: payload.metricas,
            diagnostico_espacial: payload.diagnostico_espacial
        });
    }

    /**
     * Helper estándar para leer la cookie CSRF de Django si deciden enviar
     * el diseño vía fetch() POST a una vista de Django.
     */
    function obtenerCookieCSRF(name = 'csrftoken') {
        const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
        return match ? decodeURIComponent(match[2]) : '';
    }

    async function guardarDiseno() {
        if (!state.ultimoPayload) {
            mostrarToast('Primero delimitá un terreno en el mapa.');
            return;
        }

        // 1. Guardar en localStorage para que otros módulos del prototipo (Recomendaciones / Informe) lo consuman
        try {
            localStorage.setItem('policampo_ultimo_diseno', JSON.stringify(state.ultimoPayload));
        } catch (e) {
            console.warn('No se pudo guardar en localStorage:', e);
        }

        // 2. Emitir evento global para integración modular dentro de una vista Django
        window.dispatchEvent(new CustomEvent('policampo:disenoGuardado', {
            detail: state.ultimoPayload
        }));

        // 3. Opcional: si definen `window.POLICAMPO_API_GUARDAR_URL` en el template Django, hace POST automático
        if (window.POLICAMPO_API_GUARDAR_URL) {
            try {
                const resp = await fetch(window.POLICAMPO_API_GUARDAR_URL, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': obtenerCookieCSRF()
                    },
                    body: JSON.stringify(state.ultimoPayload)
                });
                if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
                mostrarToast('✅ Diseño guardado correctamente en el servidor Django.');
                return;
            } catch (err) {
                console.error('Error enviando diseño a Django:', err);
                mostrarToast('⚠️ Guardado localmente, pero falló el envío al servidor.');
                return;
            }
        }

        console.log('PoliCampo - Payload de diseño listo para Django:', state.ultimoPayload);
        mostrarToast('✅ ¡Diseño guardado! Datos listos para el formulario, recomendaciones e informe.');
    }

    function descargarGeoJSON() {
        if (!state.ultimoPayload) return;

        // Unificamos parcela, sectores y corredores en un único FeatureCollection estándar descargable
        const features = [];

        const parcelaExport = JSON.parse(JSON.stringify(state.ultimoPayload.geometrias.parcela));
        parcelaExport.properties = {
            capa: 'parcela_principal',
            cultivo: state.ultimoPayload.cultivo_principal.nombre,
            area_ha: state.ultimoPayload.metricas.area_total_ha
        };
        features.push(parcelaExport);

        state.ultimoPayload.geometrias.sectores_cultivo.features.forEach((f) => {
            const copy = JSON.parse(JSON.stringify(f));
            copy.properties.capa = 'sector_cultivo';
            features.push(copy);
        });

        state.ultimoPayload.geometrias.corredores_florales.features.forEach((f) => {
            const copy = JSON.parse(JSON.stringify(f));
            copy.properties.capa = 'corredor_floral';
            copy.properties.diseno = state.ultimoPayload.diseno.tipo;
            features.push(copy);
        });

        const fc = turf.featureCollection(features);
        const blob = new Blob([JSON.stringify(fc, null, 2)], { type: 'application/geo+json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `policampo_diseno_${state.ultimoPayload.cultivo_principal.codigo}.geojson`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);

        mostrarToast('⬇️ Archivo GeoJSON descargado.');
    }

    // =========================================================================
    // 11. ACTUALIZACIÓN DE CONTROLES DINÁMICOS Y FICHA DE CULTIVO
    // =========================================================================
    function actualizarControlesDinamicos() {
        const tipo = dom.tipoFranja.value;
        const mostrarTransversal = tipo === 'transversal' || tipo === 'matriz';
        const mostrarIslas = tipo === 'central';

        dom.controlesTransversal.classList.toggle('oculto', !mostrarTransversal);
        dom.controlesIslas.classList.toggle('oculto', !mostrarIslas);
    }

    function actualizarFichaCultivo() {
        const cultivo = CATALOGO_CULTIVOS[dom.cultivoPrincipal.value] || CATALOGO_CULTIVOS.horticolas;
        dom.legendCultivoLabel.textContent = `Parcela (${cultivo.nombre})`;
        dom.textoPlantasSugeridas.textContent = cultivo.plantasServicio;
        dom.fichaPlantas.classList.remove('oculto');

        if (state.poligonoBaseLayer) {
            state.poligonoBaseLayer.setStyle(obtenerEstiloParcela());
        }
    }

    function sincronizarPorcentaje(valor) {
        const limpio = Math.min(Math.max(parseInt(valor, 10) || 20, 1), 60);
        dom.porcentajeInput.value = limpio;
        dom.porcentajeSlider.value = Math.min(Math.max(limpio, 5), 40);
        dom.porcentajeLabel.textContent = `${limpio}%`;
        if (state.poligonoBaseGeoJSON) generarDiseno();
    }

    // =========================================================================
    // 12. EVENTOS DE LEAFLET-GEOMAN
    // =========================================================================
    map.on('pm:create', (e) => {
        ocultarToast();

        if (state.modoDibujo === 'sector' && state.poligonoBaseGeoJSON) {
            const rawSector = e.layer.toGeoJSON();
            // Quitamos la capa temporal que creó Geoman; nosotros dibujaremos la versión recortada
            map.removeLayer(e.layer);

            try {
                const limpio = turf.cleanCoords(rawSector);
                const recortado = turf.intersect(state.poligonoBaseGeoJSON, limpio);
                if (!recortado || turf.area(recortado) < 20) {
                    mostrarToast('⚠️ El sector debe estar dentro del contorno de la parcela principal.');
                    state.modoDibujo = 'parcela';
                    return;
                }
                abrirModalSector(recortado);
            } catch (err) {
                mostrarToast('⚠️ No se pudo recortar el sector. Intentá dibujarlo sin cruces.');
                state.modoDibujo = 'parcela';
            }
            return;
        }

        // Modo parcela principal
        cargarParcelaBase(e.layer, false);
        mostrarToast('✅ Terreno delimitado. Podés ajustar el % floral o arrastrar los vértices.');
    });

    map.on('pm:remove', (e) => {
        if (e.layer === state.poligonoBaseLayer) {
            limpiarTodo();
        }
    });

    // Si el usuario cancela el modo dibujo (ej. con Esc o botón Cancelar de Geoman),
    // restauramos el modo por defecto para que no quede trabado en "sector".
    map.on('pm:drawend', () => {
        setTimeout(() => {
            if (!state.sectorPendienteGeoJSON) {
                state.modoDibujo = 'parcela';
            }
        }, 50);
    });

    // =========================================================================
    // 13. EVENTOS DE BOTONES Y CONTROLES DE UI
    // =========================================================================

    // Navegación por zonas productivas de Jujuy
    dom.selectorZona.addEventListener('change', () => {
        const [lat, lng, zoom] = dom.selectorZona.value.split(',').map(Number);
        map.flyTo([lat, lng], zoom, { duration: 0.9 });
    });

    // Geolocalización GPS
    dom.btnMiUbicacion.addEventListener('click', () => {
        if (!navigator.geolocation) {
            mostrarToast('Tu navegador no soporta geolocalización GPS.');
            return;
        }
        mostrarToast('Buscando tu ubicación GPS...', 0);
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const { latitude, longitude } = pos.coords;
                map.flyTo([latitude, longitude], 16, { duration: 1 });
                L.circleMarker([latitude, longitude], {
                    radius: 7,
                    color: '#1d4ed8',
                    fillColor: '#60a5fa',
                    fillOpacity: 0.8,
                    pmIgnore: true
                }).addTo(map).bindPopup('📍 Tu ubicación actual').openPopup();
                mostrarToast('📍 Mapa centrado en tu ubicación.');
            },
            () => {
                mostrarToast('No se pudo obtener la ubicación. Verificá los permisos del navegador.');
            },
            { enableHighAccuracy: true, timeout: 8000 }
        );
    });

    // Buscador de localidades en Jujuy (Nominatim)
    async function buscarLugar() {
        const query = dom.buscadorLugar.value.trim();
        if (!query) return;
        dom.estadoBusqueda.textContent = 'Buscando...';
        try {
            const url = `https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(query + ', Jujuy, Argentina')}`;
            const resp = await fetch(url, { headers: { 'Accept-Language': 'es' } });
            const data = await resp.json();
            if (data && data.length > 0) {
                const { lat, lon, display_name } = data[0];
                map.flyTo([parseFloat(lat), parseFloat(lon)], 15, { duration: 1 });
                dom.estadoBusqueda.textContent = `Encontrado: ${display_name.split(',').slice(0, 2).join(',')}`;
            } else {
                dom.estadoBusqueda.textContent = 'No se encontraron resultados en Jujuy.';
            }
        } catch (err) {
            dom.estadoBusqueda.textContent = 'Sin conexión al buscador. Usá el selector de zonas.';
        }
    }

    dom.btnBuscar.addEventListener('click', buscarLugar);
    dom.buscadorLugar.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            buscarLugar();
        }
    });

    // Botón principal para iniciar dibujo de parcela
    dom.btnDibujarParcela.addEventListener('click', () => {
        state.modoDibujo = 'parcela';
        map.pm.enableDraw('Polygon', {
            snappable: true,
            snapDistance: 15,
            finishOn: 'dblclick'
        });
        mostrarToast('✏️ Hacé clic en los vértices del terreno y cerrá el polígono en el primer punto.', 0);
    });

    // Botón limpiar
    dom.btnLimpiarTodo.addEventListener('click', limpiarTodo);

    // Cargar finca de ejemplo en Perico
    dom.btnCargarDemo.addEventListener('click', () => {
        dom.selectorZona.value = '-24.3833,-65.1167,14';
        dom.cultivoPrincipal.value = 'frutilla';
        const coordsLatLng = PARCELA_DEMO_PERICO.geometry.coordinates[0].map(([lng, lat]) => [lat, lng]);
        const polyLayer = L.polygon(coordsLatLng);
        cargarParcelaBase(polyLayer, true);
        mostrarToast('📍 Finca de ejemplo en Perico cargada. Probá cambiar disposición, ángulo y %.');
    });

    // Vista de impresión para módulo Informe
    dom.btnImprimir.addEventListener('click', () => window.print());

    // Cambio de cultivo principal
    dom.cultivoPrincipal.addEventListener('change', () => {
        actualizarFichaCultivo();
        if (state.poligonoBaseGeoJSON) generarDiseno();
    });

    // Sectores internos
    dom.btnAgregarSector.addEventListener('click', () => {
        if (!state.poligonoBaseGeoJSON) return;
        state.modoDibujo = 'sector';
        map.pm.enableDraw('Polygon', { snappable: true, snapDistance: 12 });
        mostrarToast('🌱 Dibujá un sector interno dentro de tu parcela (se recortará automáticamente).', 0);
    });

    dom.listaSectores.addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-del-sector');
        if (!btn) return;
        const id = btn.getAttribute('data-id');
        state.sectores = state.sectores.filter((s) => s.id !== id);
        renderizarSectores();
        actualizarListaSectores();
        if (state.poligonoBaseGeoJSON) generarDiseno();
    });

    dom.btnConfirmarSector.addEventListener('click', () => {
        if (!state.sectorPendienteGeoJSON) return;
        const nombre = dom.sectorNombre.value.trim() || `Sector ${state.sectores.length + 1}`;
        const cultivoKey = dom.sectorCultivo.value;

        state.sectores.push({
            id: `sec_${Date.now()}`,
            nombre,
            cultivoKey,
            geojson: state.sectorPendienteGeoJSON,
            areaM2: turf.area(state.sectorPendienteGeoJSON)
        });

        cerrarModalSector();
        renderizarSectores();
        actualizarListaSectores();
        generarDiseno();
        mostrarToast(`🌱 Sector "${nombre}" agregado al mapa.`);
    });

    dom.btnCancelarSector.addEventListener('click', cerrarModalSector);
    dom.btnCancelarSector2.addEventListener('click', cerrarModalSector);

    // Controles de disposición floral
    dom.tipoFranja.addEventListener('change', () => {
        actualizarControlesDinamicos();
        if (state.poligonoBaseGeoJSON) generarDiseno();
    });

    dom.porcentajeSlider.addEventListener('input', (e) => sincronizarPorcentaje(e.target.value));
    dom.porcentajeInput.addEventListener('input', (e) => sincronizarPorcentaje(e.target.value));

    dom.numCorredores.addEventListener('input', (e) => {
        dom.numCorredoresLabel.textContent = e.target.value;
        if (state.poligonoBaseGeoJSON) generarDiseno();
    });

    function actualizarAngulo(valor) {
        dom.anguloCorredores.value = valor;
        dom.anguloCorredoresLabel.textContent = describirAngulo(valor);
        dom.chipsOrientacion.forEach((chip) => {
            chip.classList.toggle('activo', chip.getAttribute('data-angulo') === String(valor));
        });
        if (state.poligonoBaseGeoJSON) generarDiseno();
    }

    dom.anguloCorredores.addEventListener('input', (e) => actualizarAngulo(e.target.value));
    dom.chipsOrientacion.forEach((chip) => {
        chip.addEventListener('click', () => {
            if (dom.anguloCorredores.disabled) return;
            actualizarAngulo(chip.getAttribute('data-angulo'));
        });
    });

    dom.densidadIslas.addEventListener('input', (e) => {
        const n = e.target.value;
        dom.densidadIslasLabel.textContent = `${n} × ${n}`;
        if (state.poligonoBaseGeoJSON) generarDiseno();
    });

    // Leyenda interactiva (prender / apagar capas)
    dom.toggleParcela.addEventListener('change', (e) => {
        if (e.target.checked) map.addLayer(capaPoligonos);
        else map.removeLayer(capaPoligonos);
    });
    dom.toggleSectores.addEventListener('change', (e) => {
        if (e.target.checked) map.addLayer(capaSectores);
        else map.removeLayer(capaSectores);
    });
    dom.togglePropuesta.addEventListener('change', (e) => {
        if (e.target.checked) map.addLayer(capaPropuesta);
        else map.removeLayer(capaPropuesta);
    });

    // Guardado y exportación
    dom.btnGuardar.addEventListener('click', guardarDiseno);
    dom.btnDescargarGeoJSON.addEventListener('click', descargarGeoJSON);

    dom.btnVerJSON.addEventListener('click', () => {
        if (!state.ultimoPayload) return;
        dom.previewJsonCode.textContent = JSON.stringify(state.ultimoPayload, null, 2);
        dom.modalJson.classList.remove('oculto');
    });

    function cerrarModalJson() {
        dom.modalJson.classList.add('oculto');
    }
    dom.btnCerrarModal.addEventListener('click', cerrarModalJson);
    dom.btnCerrarModal2.addEventListener('click', cerrarModalJson);

    dom.btnCopiarJson.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(dom.previewJsonCode.textContent);
            mostrarToast('📋 JSON copiado al portapapeles.');
        } catch (e) {
            mostrarToast('No se pudo copiar automáticamente.');
        }
    });

    // Cerrar modales con Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            cerrarModalJson();
            cerrarModalSector();
        }
    });

    // Exponer API pública limpia para otros scripts de Django si lo necesitan
    window.PoliCampoMapa = {
        getPayload: () => state.ultimoPayload,
        cargarGeoJSONParcela: (geojsonFeature) => {
            const layer = L.geoJSON(geojsonFeature).getLayers()[0];
            if (layer) cargarParcelaBase(layer, true);
        },
        limpiar: limpiarTodo
    };
})();