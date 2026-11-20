/**
 * PoliCampo - Página 2: Salida (Diagnóstico + Mapa de Corredores + Calendario/Plantas)
 * ------------------------------------------------------------------------------------
 * Carga los datos del establecimiento y sectores registrados en la Página 1
 * (desde window.POLICAMPO_TERRENO_INICIAL en Django o localStorage en el prototipo),
 * genera los diseños espaciales de corredores florales con Turf.js y emite eventos
 * en vivo para que los módulos superior (Diagnóstico) e inferior (Plantas/Calendario)
 * de los compañeros puedan consumir los datos al instante.
 */

(function () {
    'use strict';

    const C = window.PoliCampoCommon;

    const NOMBRES_DISPOSICION = {
        perimetral: 'Cerco Perimetral (Bordes)',
        transversal: 'Corredores Transversales (Franjas)',
        central: 'Islas de Biodiversidad (Grupos aislados)',
        matriz: 'Diseño en Matriz (Perimetral + Franjas)'
    };

    // =========================================================================
    // 1. ESTADO
    // =========================================================================
    const state = {
        entrada: null,
        parcelaGeoJSON: null,
        zonasExistentesFC: null,
        unionExistentesGeoJSON: null,
        propuestaGeoJSON: null,
        ultimoPayloadSalida: null
    };

    // =========================================================================
    // 2. REFERENCIAS DOM
    // =========================================================================
    const dom = {
        alertaSinDatos: document.getElementById('alerta-sin-datos'),
        resumenFincaBar: document.getElementById('resumen-finca-bar'),
        outNombreFinca: document.getElementById('out-nombre-finca'),
        outUbicacionFinca: document.getElementById('out-ubicacion-finca'),
        outEcorregionFinca: document.getElementById('out-ecorregion-finca'),
        outSuperficieFinca: document.getElementById('out-superficie-finca'),
        outCultivosFinca: document.getElementById('out-cultivos-finca'),

        btnCargarDemo: document.getElementById('btn-cargar-demo-salida'),
        btnDemoBanner: document.getElementById('btn-demo-banner'),
        btnImprimir: document.getElementById('btn-imprimir'),

        // Sincronización con bloque superior (Diagnóstico)
        diagnosticoPill: document.getElementById('diagnostico-estado-pill'),
        diagnosticoSyncBar: document.getElementById('diagnostico-sync-bar'),
        diagnosticoSyncTexto: document.getElementById('diagnostico-sync-texto'),
        diagnosticoSyncPct: document.getElementById('diagnostico-sync-pct'),

        // Sincronización con bloque inferior (Plantas / Calendario)
        contextoPlantasChips: document.getElementById('contexto-plantas-chips'),

        // Controles del mapa de salida
        tipoFranja: document.getElementById('tipo-franja'),
        porcentajeSlider: document.getElementById('porcentaje-slider'),
        porcentajeInput: document.getElementById('porcentaje-area'),
        porcentajeLabel: document.getElementById('valor-porcentaje-label'),

        boxExistentesControl: document.getElementById('box-existentes-control'),
        descontarExistentes: document.getElementById('descontar-existentes'),
        avisoExistentes: document.getElementById('aviso-existentes'),

        controlesTransversal: document.getElementById('controles-transversal'),
        numCorredores: document.getElementById('num-corredores'),
        numCorredoresLabel: document.getElementById('valor-corredores-label'),
        anguloCorredores: document.getElementById('angulo-corredores'),
        anguloCorredoresLabel: document.getElementById('valor-angulo-label'),
        chipsOrientacion: document.querySelectorAll('.chip[data-angulo]'),

        controlesIslas: document.getElementById('controles-islas'),
        densidadIslas: document.getElementById('densidad-islas'),
        densidadIslasLabel: document.getElementById('valor-islas-label'),

        areaTotal: document.getElementById('area-total'),
        areaTotalSub: document.getElementById('area-total-sub'),
        perimetroTotal: document.getElementById('perimetro-total'),
        anchoBanda: document.getElementById('ancho-banda'),
        areaProductiva: document.getElementById('area-productiva'),
        pctProductiva: document.getElementById('pct-productiva'),
        areaFranja: document.getElementById('area-franja'),
        pctFranja: document.getElementById('pct-franja'),

        listaSectoresSalida: document.getElementById('lista-sectores-salida'),
        bloqueExistentesSalida: document.getElementById('bloque-existentes-salida'),
        listaExistentesSalida: document.getElementById('lista-existentes-salida'),

        btnGuardarPropuesta: document.getElementById('btn-guardar-propuesta'),
        btnDescargarGeoJSON: document.getElementById('btn-descargar-geojson'),
        btnVerJSON: document.getElementById('btn-ver-json'),

        inputPropuestaGeo: document.getElementById('django-propuesta-geojson'),
        inputPropuestaJson: document.getElementById('django-propuesta-json'),

        mapToast: document.getElementById('map-toast'),
        toggleParcela: document.getElementById('toggle-capa-parcela'),
        toggleSectores: document.getElementById('toggle-capa-sectores'),
        toggleExistentes: document.getElementById('toggle-capa-existentes'),
        togglePropuesta: document.getElementById('toggle-capa-propuesta'),

        modalJson: document.getElementById('modal-json'),
        previewJsonCode: document.getElementById('preview-json-code'),
        btnCerrarModal: document.getElementById('btn-cerrar-modal'),
        btnCerrarModal2: document.getElementById('btn-cerrar-modal-2'),
        btnCopiarJson: document.getElementById('btn-copiar-json')
    };

    // =========================================================================
    // 3. INICIALIZACIÓN DEL MAPA LEAFLET (SALIDA)
    // =========================================================================
    const map = L.map('mapa-salida', {
        center: [-24.3833, -65.1167],
        zoom: 13
    });

    const bases = C.crearCapasBaseLeaflet();
    bases.predeterminada.addTo(map);
    L.control.layers(bases.control, null, { position: 'topright' }).addTo(map);
    L.control.scale({ metric: true, imperial: false, position: 'bottomleft' }).addTo(map);

    const capaParcela = L.featureGroup().addTo(map);
    const capaSectores = L.featureGroup().addTo(map);
    const capaExistentes = L.featureGroup().addTo(map);
    const capaPropuesta = L.featureGroup().addTo(map);

    // =========================================================================
    // 4. HELPERS DE INTERFAZ
    // =========================================================================
    let toastTimer = null;
    function mostrarToast(msg, duracionMs = 3500) {
        dom.mapToast.textContent = msg;
        dom.mapToast.classList.remove('oculto');
        clearTimeout(toastTimer);
        if (duracionMs > 0) {
            toastTimer = setTimeout(() => dom.mapToast.classList.add('oculto'), duracionMs);
        }
    }

    function describirAngulo(grados) {
        const g = Number(grados);
        if (g === 0 || g === 180) return `${g}° (N-S)`;
        if (g === 90) return `${g}° (E-O)`;
        if (g === 45) return `${g}° (NE-SO)`;
        if (g === 135) return `${g}° (NO-SE)`;
        return `${g}°`;
    }

    function habilitarControlesSalida(habilitado) {
        [
            dom.tipoFranja,
            dom.porcentajeSlider,
            dom.porcentajeInput,
            dom.numCorredores,
            dom.anguloCorredores,
            dom.densidadIslas,
            dom.btnGuardarPropuesta,
            dom.btnDescargarGeoJSON,
            dom.btnVerJSON
        ].forEach((el) => {
            if (el) el.disabled = !habilitado;
        });
    }

    function actualizarControlesDinamicos() {
        const tipo = dom.tipoFranja.value;
        dom.controlesTransversal.classList.toggle('oculto', tipo !== 'transversal' && tipo !== 'matriz');
        dom.controlesIslas.classList.toggle('oculto', tipo !== 'central');
    }

    // =========================================================================
    // 5. ALGORITMOS GEOESPACIALES DE CORREDORES FLORALES (Turf.js v6)
    // =========================================================================
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

            if (areaInner > areaInternaObjetivo) lo = mid;
            else hi = mid;
        }

        if (mejorInner) {
            try {
                const franja = turf.difference(poligono, mejorInner);
                if (franja && turf.area(franja) > 1) {
                    franja.properties = {
                        subtipo: 'perimetral',
                        etiqueta: 'Cerco Perimetral Floral',
                        ancho_estimado_m: Number(mejorDist.toFixed(1))
                    };
                    return { features: [franja], innerPolygon: mejorInner, anchoEstimadoM: mejorDist };
                }
            } catch (e) {
                // Fallback abajo
            }
        }

        const factorEscala = Math.sqrt(Math.max(1 - proporcion, 0.05));
        const reducido = turf.transformScale(poligono, factorEscala);
        const franjaFallback = turf.difference(poligono, reducido);
        if (franjaFallback) {
            franjaFallback.properties = { subtipo: 'perimetral', etiqueta: 'Cerco Perimetral Floral' };
        }
        return {
            features: franjaFallback ? [franjaFallback] : [],
            innerPolygon: reducido,
            anchoEstimadoM: null
        };
    }

    function calcularTransversales(poligono, proporcion, numCorredores, angulo) {
        const areaTotal = turf.area(poligono);
        const areaObjetivo = areaTotal * proporcion;
        const centro = turf.centerOfMass(poligono);

        const rotado = angulo !== 0
            ? turf.transformRotate(poligono, -angulo, { pivot: centro })
            : poligono;

        const bbox = turf.bbox(rotado);
        const [minX, minY, maxX, maxY] = bbox;
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
            if (res.areaAcumulada < areaObjetivo) lo = mid;
            else hi = mid;
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

    function calcularIslas(poligono, proporcion, divisiones) {
        const bbox = turf.bbox(poligono);
        const [minX, minY, maxX, maxY] = bbox;

        const anchoM = turf.distance([minX, minY], [maxX, minY], { units: 'meters' });
        const altoM = turf.distance([minX, minY], [minX, maxY], { units: 'meters' });

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
                const segura = turf.intersect(poligono, escalada);
                if (segura && turf.area(segura) > 4) {
                    segura.properties = {
                        subtipo: 'isla',
                        etiqueta: `Isla de Biodiversidad #${contador++}`
                    };
                    islas.push(segura);
                }
            } catch (e) {
                // Continúa
            }
        });

        return { features: islas, anchoEstimadoM: null };
    }

    function calcularMatriz(poligono, proporcion, numCorredores, angulo) {
        const resPerimetro = calcularPerimetral(poligono, proporcion * 0.5);
        const features = [...resPerimetro.features];

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

        return { features, anchoEstimadoM: resPerimetro.anchoEstimadoM };
    }

    // =========================================================================
    // 6. CARGA DEL TERRENO DESDE LA PÁGINA DE ENTRADA
    // =========================================================================
    function construirPayloadDemo() {
        const demo = C.DEMO_TERRENO;
        const areaM2 = turf.area(demo.parcela);
        const areaHa = areaM2 / 10000;
        const perimetroM = turf.length(turf.polygonToLine(demo.parcela), { units: 'kilometers' }) * 1000;
        const centro = turf.centerOfMass(demo.parcela);

        const sectoresFeatures = demo.sectores_demo.map((s, idx) => {
            const feat = { type: 'Feature', properties: {}, geometry: s.geometry };
            const recortado = turf.intersect(demo.parcela, feat) || feat;
            const sAreaM2 = turf.area(recortado);
            const pct = (sAreaM2 / areaM2) * 100;
            const info = C.CATALOGO_CULTIVOS[s.cultivoKey] || C.CATALOGO_CULTIVOS.otro;
            return {
                type: 'Feature',
                geometry: recortado.geometry,
                properties: {
                    id: `sec_demo_${idx + 1}`,
                    nombre: s.nombre,
                    cultivo: s.cultivoKey,
                    cultivo_nombre: info.nombre,
                    color: info.color,
                    fillColor: info.fillColor,
                    porcentaje_parcela: Number(pct.toFixed(2)),
                    area_ha: Number((sAreaM2 / 10000).toFixed(4))
                }
            };
        });

        const floralesFeatures = (demo.zonas_florales_demo || []).map((z, idx) => {
            const feat = { type: 'Feature', properties: {}, geometry: z.geometry };
            const recortado = turf.intersect(demo.parcela, feat) || feat;
            const zAreaM2 = turf.area(recortado);
            const pct = (zAreaM2 / areaM2) * 100;
            const info = C.CATALOGO_ZONAS_FLORALES[z.tipoKey] || C.CATALOGO_ZONAS_FLORALES.otro;
            return {
                type: 'Feature',
                geometry: recortado.geometry,
                properties: {
                    id: `zf_demo_${idx + 1}`,
                    nombre: z.nombre,
                    tipo: z.tipoKey,
                    tipo_nombre: info.nombre,
                    especies: z.especies || '',
                    color: info.color,
                    fillColor: info.fillColor,
                    porcentaje_parcela: Number(pct.toFixed(2)),
                    area_ha: Number((zAreaM2 / 10000).toFixed(4))
                }
            };
        });

        const totalFloralDemoHa = floralesFeatures.reduce((acc, f) => acc + f.properties.area_ha, 0);
        const totalFloralDemoPct = floralesFeatures.reduce((acc, f) => acc + f.properties.porcentaje_parcela, 0);

        return {
            version: '2.1',
            timestamp: new Date().toISOString(),
            establecimiento: demo.establecimiento,
            ubicacion_centroide: {
                lat: Number(centro.geometry.coordinates[1].toFixed(6)),
                lng: Number(centro.geometry.coordinates[0].toFixed(6))
            },
            superficie: {
                total_ha: Number(areaHa.toFixed(4)),
                calculada_mapa_ha: Number(areaHa.toFixed(4)),
                calculada_mapa_m2: Math.round(areaM2),
                perimetro_m: Math.round(perimetroM),
                editada_manualmente: false
            },
            cultivos_resumen: sectoresFeatures.map((f) => ({
                nombre_sector: f.properties.nombre,
                cultivo: f.properties.cultivo,
                cultivo_nombre: f.properties.cultivo_nombre,
                area_ha: f.properties.area_ha,
                porcentaje_parcela: f.properties.porcentaje_parcela
            })),
            zonas_florales_existentes_resumen: {
                cantidad: floralesFeatures.length,
                area_total_ha: Number(totalFloralDemoHa.toFixed(4)),
                porcentaje_parcela: Number(totalFloralDemoPct.toFixed(2)),
                detalle: floralesFeatures.map((f) => ({
                    nombre: f.properties.nombre,
                    tipo: f.properties.tipo,
                    tipo_nombre: f.properties.tipo_nombre,
                    especies: f.properties.especies,
                    area_ha: f.properties.area_ha,
                    porcentaje_parcela: f.properties.porcentaje_parcela
                }))
            },
            geometrias: {
                parcela: demo.parcela,
                sectores_cultivo: turf.featureCollection(sectoresFeatures),
                zonas_florales_existentes: turf.featureCollection(floralesFeatures)
            }
        };
    }

    function calcularUnionFeatures(features) {
        if (!features || features.length === 0) return null;
        let acc = features[0];
        for (let i = 1; i < features.length; i++) {
            try {
                acc = turf.union(acc, features[i]) || acc;
            } catch (e) {
                // Mantiene acumulado válido
            }
        }
        return acc;
    }

    function cargarTerrenoEnSalida(datosEntrada) {
        if (!datosEntrada || !datosEntrada.geometrias || !datosEntrada.geometrias.parcela) {
            dom.alertaSinDatos.classList.remove('oculto');
            dom.resumenFincaBar.classList.add('oculto');
            habilitarControlesSalida(false);
            return;
        }

        state.entrada = datosEntrada;
        state.parcelaGeoJSON = datosEntrada.geometrias.parcela;

        dom.alertaSinDatos.classList.add('oculto');
        dom.resumenFincaBar.classList.remove('oculto');
        habilitarControlesSalida(true);

        // 1. Poblar barra resumen del establecimiento
        const est = datosEntrada.establecimiento || {};
        const sup = datosEntrada.superficie || {};
        const cultivosLista = (datosEntrada.cultivos_resumen || []).map((c) => c.cultivo_nombre);
        const cultivosUnicos = [...new Set(cultivosLista)];

        dom.outNombreFinca.textContent = est.nombre || 'Establecimiento sin nombre';
        dom.outUbicacionFinca.textContent = [est.localidad, est.departamento].filter(Boolean).join(', ') || 'Jujuy';
        dom.outEcorregionFinca.textContent = est.ecorregion_nombre || C.obtenerNombreEcorregion(est.ecorregion) || '—';
        dom.outSuperficieFinca.textContent = `${C.formatearNumero(sup.total_ha || 0, 2)} ha${sup.editada_manualmente ? ' (editada)' : ''}`;
        dom.outCultivosFinca.textContent = cultivosUnicos.length > 0 ? cultivosUnicos.join(', ') : 'Sin cultivos declarados';

        // 2. Renderizar parcela, sectores y zonas florales existentes
        capaParcela.clearLayers();
        capaSectores.clearLayers();
        capaExistentes.clearLayers();

        const layerParcela = L.geoJSON(state.parcelaGeoJSON, {
            style: {
                color: '#1b4332',
                weight: 3,
                fillColor: '#40916c',
                fillOpacity: 0.14
            }
        }).addTo(capaParcela);

        const sectoresFC = datosEntrada.geometrias.sectores_cultivo;
        dom.listaSectoresSalida.innerHTML = '';

        if (sectoresFC && sectoresFC.features && sectoresFC.features.length > 0) {
            sectoresFC.features.forEach((feat) => {
                const p = feat.properties || {};
                const info = C.CATALOGO_CULTIVOS[p.cultivo] || C.CATALOGO_CULTIVOS.otro;
                const color = p.color || info.color;
                const fillColor = p.fillColor || info.fillColor;

                L.geoJSON(feat, {
                    style: {
                        color,
                        weight: 2,
                        fillColor,
                        fillOpacity: 0.34
                    },
                    onEachFeature: (_f, layer) => {
                        layer.bindPopup(`
                            <div style="font-family: Inter, sans-serif; font-size: 12.5px; line-height: 1.4;">
                                <strong>${info.icono} ${p.nombre || 'Sector'}</strong><br>
                                <strong>Cultivo:</strong> ${p.cultivo_nombre || info.nombre}<br>
                                <strong>Superficie:</strong> ${C.formatearNumero(p.area_ha || 0, 2)} ha (${C.formatearNumero(p.porcentaje_parcela || 0, 1)}%)
                            </div>
                        `);
                    }
                }).addTo(capaSectores);

                const li = document.createElement('li');
                li.className = 'sector-item';
                li.innerHTML = `
                    <div class="sector-info">
                        <span class="sector-dot" style="background:${color};"></span>
                        <div>
                            <strong>${p.nombre || 'Sector'}</strong> · ${p.cultivo_nombre || info.nombre}
                            <span style="color:#64748b;">(${C.formatearNumero(p.area_ha || 0, 2)} ha)</span>
                        </div>
                    </div>
                `;
                dom.listaSectoresSalida.appendChild(li);
            });
        } else {
            dom.listaSectoresSalida.innerHTML = '<li class="lista-vacia">Sin sectores divididos</li>';
        }

        // 3. Zonas florales existentes (conservadas)
        const existentesFC = datosEntrada.geometrias.zonas_florales_existentes;
        const featsExistentes = (existentesFC && existentesFC.features) ? existentesFC.features : [];
        state.zonasExistentesFC = turf.featureCollection(featsExistentes);
        state.unionExistentesGeoJSON = calcularUnionFeatures(featsExistentes);

        dom.listaExistentesSalida.innerHTML = '';
        if (featsExistentes.length > 0) {
            dom.boxExistentesControl.classList.remove('oculto');
            dom.bloqueExistentesSalida.classList.remove('oculto');

            featsExistentes.forEach((feat) => {
                const p = feat.properties || {};
                const info = C.CATALOGO_ZONAS_FLORALES[p.tipo] || C.CATALOGO_ZONAS_FLORALES.otro;
                const color = p.color || info.color;
                const fillColor = p.fillColor || info.fillColor;

                L.geoJSON(feat, {
                    style: {
                        color,
                        weight: 2.5,
                        fillColor,
                        fillOpacity: 0.52,
                        dashArray: '5, 4'
                    },
                    onEachFeature: (_f, layer) => {
                        const esp = p.especies ? `<br><strong>Especies:</strong> ${p.especies}` : '';
                        layer.bindPopup(`
                            <div style="font-family: Inter, sans-serif; font-size: 12.5px; line-height: 1.4;">
                                <strong style="color:${color};">${info.icono} ${p.nombre || 'Zona floral existente'}</strong><br>
                                <strong>Tipo:</strong> ${p.tipo_nombre || info.nombre}${esp}<br>
                                <strong>Aporte conservado:</strong> ${C.formatearNumero(p.area_ha || 0, 2)} ha (${C.formatearNumero(p.porcentaje_parcela || 0, 1)}%)
                            </div>
                        `);
                    }
                }).addTo(capaExistentes);

                const li = document.createElement('li');
                li.className = 'sector-item sector-item-floral';
                li.innerHTML = `
                    <div class="sector-info">
                        <span class="sector-dot" style="background:${color};"></span>
                        <div>
                            <strong>${p.nombre || 'Zona floral'}</strong> · ${p.tipo_nombre || info.nombre}
                            <span style="color:#64748b;">(${C.formatearNumero(p.area_ha || 0, 2)} ha)</span>
                        </div>
                    </div>
                `;
                dom.listaExistentesSalida.appendChild(li);
            });
        } else {
            dom.boxExistentesControl.classList.add('oculto');
            dom.bloqueExistentesSalida.classList.add('oculto');
        }

        // Ajustar vista del mapa a la parcela
        map.invalidateSize();
        map.fitBounds(layerParcela.getBounds(), { padding: [45, 45] });

        actualizarControlesDinamicos();
        generarDisenoSalida();
    }

    // =========================================================================
    // 7. GENERACIÓN DEL REDISEÑO Y SINCRONIZACIÓN CON SECCIONES SUPERIOR/INFERIOR
    // =========================================================================
    function ejecutarAlgoritmo(tipo, poligono, proporcion, numCorredores, angulo, divisionesIslas) {
        if (tipo === 'perimetral') return calcularPerimetral(poligono, proporcion);
        if (tipo === 'transversal') return calcularTransversales(poligono, proporcion, numCorredores, angulo);
        if (tipo === 'central') return calcularIslas(poligono, proporcion, divisionesIslas);
        if (tipo === 'matriz') return calcularMatriz(poligono, proporcion, numCorredores, angulo);
        return { features: [], anchoEstimadoM: null };
    }

    function restarExistentes(features, unionExistentes) {
        if (!unionExistentes) return features;
        const limpias = [];
        features.forEach((f) => {
            try {
                const diff = turf.difference(f, unionExistentes);
                if (diff && turf.area(diff) > 2) {
                    diff.properties = { ...(f.properties || {}) };
                    limpias.push(diff);
                }
            } catch (e) {
                limpias.push(f);
            }
        });
        return limpias;
    }

    function generarDisenoSalida() {
        if (!state.parcelaGeoJSON || !state.entrada) return;

        const poligono = state.parcelaGeoJSON;
        const areaGeoTotalM2 = turf.area(poligono);
        const tipo = dom.tipoFranja.value;
        let porcentaje = parseFloat(dom.porcentajeInput.value);
        if (Number.isNaN(porcentaje)) porcentaje = 20;
        porcentaje = Math.min(Math.max(porcentaje, 1), 60);

        const proporcionObjetivo = porcentaje / 100;
        const numCorredores = parseInt(dom.numCorredores.value, 10) || 3;
        const angulo = parseInt(dom.anguloCorredores.value, 10) || 0;
        const divisionesIslas = parseInt(dom.densidadIslas.value, 10) || 3;

        // Evaluar aporte de zonas florales existentes
        const unionExistentes = state.unionExistentesGeoJSON;
        const areaGeoExistenteM2 = unionExistentes ? Math.min(turf.area(unionExistentes), areaGeoTotalM2) : 0;
        const propExistente = areaGeoTotalM2 > 0 ? (areaGeoExistenteM2 / areaGeoTotalM2) : 0;
        const pctExistente = propExistente * 100;
        const descontar = Boolean(unionExistentes && dom.descontarExistentes && dom.descontarExistentes.checked);

        let resultado = { features: [], anchoEstimadoM: null };

        try {
            if (descontar) {
                const propFaltante = Math.max(0, proporcionObjetivo - propExistente);

                if (propFaltante < 0.005) {
                    // Las zonas existentes ya alcanzan o superan el objetivo
                    resultado = { features: [], anchoEstimadoM: null };
                } else {
                    // Pasada 1: generamos para la proporción faltante y recortamos superposición con existentes
                    let res = ejecutarAlgoritmo(tipo, poligono, propFaltante, numCorredores, angulo, divisionesIslas);
                    let nuevas = restarExistentes(res.features, unionExistentes);
                    let areaNuevasM2 = nuevas.reduce((acc, f) => acc + turf.area(f), 0);
                    const objetivoNuevasM2 = areaGeoTotalM2 * propFaltante;

                    // Pasada 2 de compensación si el recorte contra existentes quitó parte del área nueva
                    if (areaNuevasM2 > 1 && areaNuevasM2 < objetivoNuevasM2 * 0.92) {
                        const factorComp = Math.min(objetivoNuevasM2 / areaNuevasM2, 2.2);
                        const propAjustada = Math.min(propFaltante * factorComp, 0.75);
                        const res2 = ejecutarAlgoritmo(tipo, poligono, propAjustada, numCorredores, angulo, divisionesIslas);
                        const nuevas2 = restarExistentes(res2.features, unionExistentes);
                        const areaNuevas2M2 = nuevas2.reduce((acc, f) => acc + turf.area(f), 0);
                        if (Math.abs(areaNuevas2M2 - objetivoNuevasM2) < Math.abs(areaNuevasM2 - objetivoNuevasM2)) {
                            res = res2;
                            nuevas = nuevas2;
                        }
                    }

                    resultado = { features: nuevas, anchoEstimadoM: res.anchoEstimadoM };
                }
            } else {
                const res = ejecutarAlgoritmo(tipo, poligono, proporcionObjetivo, numCorredores, angulo, divisionesIslas);
                // Evitar superposición visual sobre flores existentes aunque no se descuenten del objetivo
                const nuevas = unionExistentes ? restarExistentes(res.features, unionExistentes) : res.features;
                resultado = { features: nuevas, anchoEstimadoM: res.anchoEstimadoM };
            }
        } catch (err) {
            console.error('Error generando diseño:', err);
            mostrarToast('⚠️ No se pudo generar esta configuración para la geometría actual.');
            return;
        }

        const fc = turf.featureCollection(resultado.features);
        state.propuestaGeoJSON = fc;

        // Cálculos proporcionales respetando la superficie total oficial (editable)
        const areaGeoNuevasM2 = fc.features.reduce((acc, f) => acc + turf.area(f), 0);
        const areaGeoTotalFloralM2 = Math.min(areaGeoExistenteM2 + areaGeoNuevasM2, areaGeoTotalM2);

        const pctRealExistente = pctExistente;
        const pctRealNuevas = areaGeoTotalM2 > 0 ? (areaGeoNuevasM2 / areaGeoTotalM2) * 100 : 0;
        const pctRealTotalFloral = areaGeoTotalM2 > 0 ? (areaGeoTotalFloralM2 / areaGeoTotalM2) * 100 : 0;
        const pctRealProductiva = Math.max(100 - pctRealTotalFloral, 0);

        const supOficialHa = (state.entrada.superficie && state.entrada.superficie.total_ha)
            ? state.entrada.superficie.total_ha
            : (areaGeoTotalM2 / 10000);
        const perimetroM = (state.entrada.superficie && state.entrada.superficie.perimetro_m)
            ? state.entrada.superficie.perimetro_m
            : turf.length(turf.polygonToLine(poligono), { units: 'kilometers' }) * 1000;

        const areaExistenteHa = supOficialHa * (pctRealExistente / 100);
        const areaNuevasHa = supOficialHa * (pctRealNuevas / 100);
        const areaTotalFloralHa = supOficialHa * (pctRealTotalFloral / 100);
        const areaProductivaHa = Math.max(supOficialHa - areaTotalFloralHa, 0);

        // Actualizar texto explicativo de zonas florales existentes
        if (unionExistentes && dom.avisoExistentes) {
            if (descontar && pctRealExistente >= porcentaje - 0.3) {
                dom.avisoExistentes.textContent = `¡Excelente! Tus zonas existentes ya aportan ${C.formatearNumero(pctRealExistente, 1)}%, alcanzando el objetivo del ${porcentaje}%. No hacen falta franjas nuevas.`;
            } else if (descontar) {
                dom.avisoExistentes.textContent = `Aporte existente: ${C.formatearNumero(pctRealExistente, 1)}% (${C.formatearNumero(areaExistenteHa, 2)} ha) → Se proponen franjas nuevas por ~${C.formatearNumero(pctRealNuevas, 1)}% sin superponerse.`;
            } else {
                dom.avisoExistentes.textContent = `Se conservan ${C.formatearNumero(pctRealExistente, 1)}% existentes + ${C.formatearNumero(pctRealNuevas, 1)}% de franjas nuevas (${C.formatearNumero(pctRealTotalFloral, 1)}% total).`;
            }
        }

        // Actualizar métricas en el panel del mapa
        dom.areaTotal.textContent = `${C.formatearNumero(supOficialHa, 2)} ha`;
        dom.areaTotalSub.textContent = state.entrada.superficie && state.entrada.superficie.editada_manualmente
            ? `Mapa: ${C.formatearNumero(areaGeoTotalM2 / 10000, 2)} ha`
            : `${C.formatearNumero(areaGeoTotalM2, 0)} m²`;

        dom.perimetroTotal.textContent = `${C.formatearNumero(perimetroM, 0)} m`;
        dom.anchoBanda.textContent = resultado.anchoEstimadoM
            ? `Ancho banda: ~${C.formatearNumero(resultado.anchoEstimadoM, 1)} m`
            : `Franjas nuevas: ${fc.features.length}`;

        dom.areaProductiva.textContent = `${C.formatearNumero(areaProductivaHa, 2)} ha`;
        dom.pctProductiva.textContent = `${C.formatearNumero(pctRealProductiva, 1)}%`;

        dom.areaFranja.textContent = `${C.formatearNumero(areaTotalFloralHa, 2)} ha`;
        dom.pctFranja.textContent = pctRealExistente > 0
            ? `${C.formatearNumero(pctRealTotalFloral, 1)}% (Exist: ${C.formatearNumero(pctRealExistente, 1)}% + Nuev: ${C.formatearNumero(pctRealNuevas, 1)}%)`
            : `${C.formatearNumero(pctRealTotalFloral, 1)}%`;

        // Renderizar capa de corredores nuevos
        renderizarPropuesta(fc, supOficialHa, areaGeoTotalM2);

        // Evaluar referencia espacial para sección superior (Diagnóstico) e inferior (Plantas/Calendario)
        const refEspacial = evaluarReferenciaBiodiversidad(pctRealTotalFloral, pctRealExistente);
        actualizarSlotsCompaneros({
            refEspacial,
            pctRealTotalFloral,
            pctRealExistente,
            pctRealNuevas,
            areaExistenteHa,
            areaNuevasHa,
            areaTotalFloralHa,
            tipo
        });

        // Armar payload completo de salida
        const payloadSalida = {
            version: '2.1',
            timestamp: new Date().toISOString(),
            establecimiento: state.entrada.establecimiento,
            ubicacion_centroide: state.entrada.ubicacion_centroide,
            superficie: state.entrada.superficie,
            cultivos_resumen: state.entrada.cultivos_resumen,
            zonas_florales_existentes_resumen: state.entrada.zonas_florales_existentes_resumen || {
                cantidad: 0,
                area_total_ha: 0,
                porcentaje_parcela: 0,
                detalle: []
            },
            diseno_corredores: {
                tipo,
                tipo_nombre: NOMBRES_DISPOSICION[tipo],
                porcentaje_objetivo: porcentaje,
                descontar_existentes: descontar,
                porcentaje_existente: Number(pctRealExistente.toFixed(2)),
                porcentaje_corredores_nuevos: Number(pctRealNuevas.toFixed(2)),
                porcentaje_total_biodiversidad: Number(pctRealTotalFloral.toFixed(2)),
                cantidad_corredores: (tipo === 'transversal' || tipo === 'matriz') ? numCorredores : null,
                orientacion_grados: (tipo === 'transversal' || tipo === 'matriz') ? angulo : null,
                divisiones_islas: tipo === 'central' ? divisionesIslas : null,
                ancho_banda_estimado_m: resultado.anchoEstimadoM ? Number(resultado.anchoEstimadoM.toFixed(2)) : null,
                area_floral_existente_ha: Number(areaExistenteHa.toFixed(4)),
                area_corredores_nuevos_ha: Number(areaNuevasHa.toFixed(4)),
                area_total_biodiversidad_ha: Number(areaTotalFloralHa.toFixed(4)),
                area_productiva_ha: Number(areaProductivaHa.toFixed(4)),
                cumple_minimo_20_pct: pctRealTotalFloral >= 19.5,
                estado_referencia: refEspacial.estado
            },
            geometrias: {
                parcela: state.parcelaGeoJSON,
                sectores_cultivo: state.entrada.geometrias.sectores_cultivo,
                zonas_florales_existentes: state.zonasExistentesFC || turf.featureCollection([]),
                corredores_florales_nuevos: fc
            }
        };

        state.ultimoPayloadSalida = payloadSalida;

        // Inputs ocultos de Django
        dom.inputPropuestaGeo.value = JSON.stringify(fc);
        dom.inputPropuestaJson.value = JSON.stringify({
            establecimiento: payloadSalida.establecimiento,
            superficie: payloadSalida.superficie,
            cultivos_resumen: payloadSalida.cultivos_resumen,
            zonas_florales_existentes_resumen: payloadSalida.zonas_florales_existentes_resumen,
            diseno_corredores: payloadSalida.diseno_corredores
        });

        // Emitir evento en tiempo real para que los scripts de Diagnóstico y Calendario/Plantas puedan reaccionar
        window.dispatchEvent(new CustomEvent('policampo:propuestaActualizada', {
            detail: payloadSalida
        }));
    }

    function evaluarReferenciaBiodiversidad(pctTotal, pctExistente) {
        const prefijo = pctExistente > 0
            ? `Base floral existente: ${C.formatearNumero(pctExistente, 1)}% → Con rediseño: ${C.formatearNumero(pctTotal, 1)}%. `
            : '';

        if (pctTotal >= 19.5) {
            return {
                estado: 'OPTIMO',
                clase: 'optimo',
                pill: '✅ Cobertura óptima (≥20%)',
                texto: `${prefijo}El predio alcanza ${C.formatearNumero(pctTotal, 1)}% de cobertura floral, cumpliendo el umbral agroecológico recomendado.`
            };
        }
        if (pctTotal >= 10) {
            return {
                estado: 'PARCIAL',
                clase: 'alerta',
                pill: '⚠️ Debajo del 20% recomendado',
                texto: `${prefijo}Cobertura proyectada de ${C.formatearNumero(pctTotal, 1)}%. Se sugiere elevar al 20% para sostener polinizadores.`
            };
        }
        return {
            estado: 'DEFICIT',
            clase: 'critico',
            pill: '🚨 Déficit crítico (<10%)',
            texto: `${prefijo}La superficie floral proyectada (${C.formatearNumero(pctTotal, 1)}%) es muy baja para favorecer la biodiversidad.`
        };
    }

    function actualizarSlotsCompaneros({
        refEspacial,
        pctRealTotalFloral,
        pctRealExistente,
        areaExistenteHa,
        areaNuevasHa,
        areaTotalFloralHa,
        tipo
    }) {
        // Bloque superior: Diagnóstico
        dom.diagnosticoPill.textContent = refEspacial.pill;
        dom.diagnosticoPill.className = `slot-status-pill ${refEspacial.clase}`;
        dom.diagnosticoSyncBar.className = `diagnostico-sync-bar ${refEspacial.clase}`;
        dom.diagnosticoSyncTexto.textContent = refEspacial.texto;
        dom.diagnosticoSyncPct.textContent = `${C.formatearNumero(pctRealTotalFloral, 1)}%`;

        // Bloque inferior: Chips de contexto para Plantas y Calendario
        const est = state.entrada.establecimiento || {};
        const cultivos = [...new Set((state.entrada.cultivos_resumen || []).map((c) => c.cultivo_nombre))];
        const chips = [
            `🌎 Ecorregión: ${est.ecorregion_nombre || '—'}`,
            `🌱 Cultivos: ${cultivos.length ? cultivos.join(', ') : 'Sin definir'}`,
            `🌼 Diseño: ${NOMBRES_DISPOSICION[tipo]}`
        ];

        if (pctRealExistente > 0) {
            chips.push(`🌸 Conservado: ${C.formatearNumero(areaExistenteHa, 2)} ha (${C.formatearNumero(pctRealExistente, 1)}%)`);
            chips.push(`➕ A implantar: ${C.formatearNumero(areaNuevasHa, 2)} ha`);
        } else {
            chips.push(`📐 Área floral: ${C.formatearNumero(areaTotalFloralHa, 2)} ha (${C.formatearNumero(pctRealTotalFloral, 1)}%)`);
        }

        dom.contextoPlantasChips.innerHTML = chips
            .map((texto) => `<span class="context-chip">${texto}</span>`)
            .join('');
    }

    function renderizarPropuesta(fc, supOficialHa, areaGeoTotalM2) {
        capaPropuesta.clearLayers();

        L.geoJSON(fc, {
            style: (feature) => {
                const esBorde = feature.properties && feature.properties.subtipo === 'perimetral';
                return {
                    color: '#be185d',
                    weight: esBorde ? 2.5 : 2,
                    fillColor: '#ec4899',
                    fillOpacity: 0.55,
                    dashArray: esBorde ? '6, 4' : '4, 5'
                };
            },
            onEachFeature: (feature, layer) => {
                const areaGeoM2 = turf.area(feature);
                const pct = areaGeoTotalM2 > 0 ? (areaGeoM2 / areaGeoTotalM2) * 100 : 0;
                const areaHaEscalada = supOficialHa * (pct / 100);
                const titulo = (feature.properties && feature.properties.etiqueta) || 'Corredor Floral';
                const anchoInfo = feature.properties && feature.properties.ancho_estimado_m
                    ? `<br><strong>Ancho aprox.:</strong> ${feature.properties.ancho_estimado_m} m`
                    : '';

                layer.bindPopup(`
                    <div style="font-family: Inter, sans-serif; font-size: 12.5px; line-height: 1.4;">
                        <strong style="color:#9d174d;">🌼 ${titulo}</strong><br>
                        <strong>Superficie:</strong> ${C.formatearNumero(areaHaEscalada, 3)} ha (${C.formatearNumero(pct, 1)}%)${anchoInfo}
                    </div>
                `);
            }
        }).addTo(capaPropuesta);

        capaPropuesta.bringToFront();
    }

    // =========================================================================
    // 8. GUARDADO Y EXPORTACIÓN DE LA PROPUESTA
    // =========================================================================
    async function guardarPropuesta() {
        if (!state.ultimoPayloadSalida) return;

        try {
            localStorage.setItem(C.STORAGE_KEY_SALIDA, JSON.stringify(state.ultimoPayloadSalida));
        } catch (e) {
            console.warn('No se pudo guardar en localStorage:', e);
        }

        window.dispatchEvent(new CustomEvent('policampo:propuestaGuardada', {
            detail: state.ultimoPayloadSalida
        }));

        if (window.POLICAMPO_API_GUARDAR_PROPUESTA_URL) {
            try {
                const resp = await fetch(window.POLICAMPO_API_GUARDAR_PROPUESTA_URL, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': C.obtenerCookieCSRF()
                    },
                    body: JSON.stringify(state.ultimoPayloadSalida)
                });
                if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
                mostrarToast('✅ Propuesta de rediseño guardada en el servidor Django.');
                return;
            } catch (err) {
                console.error('Error guardando propuesta en Django:', err);
                mostrarToast('⚠️ Guardado localmente, pero falló el envío al servidor.');
                return;
            }
        }

        console.log('PoliCampo - Propuesta de salida lista:', state.ultimoPayloadSalida);
        mostrarToast('✅ Propuesta de rediseño guardada correctamente.');
    }

    function descargarGeoJSON() {
        if (!state.ultimoPayloadSalida) return;
        const p = state.ultimoPayloadSalida;
        const features = [];

        const parcelaExp = JSON.parse(JSON.stringify(p.geometrias.parcela));
        parcelaExp.properties = {
            capa: 'parcela',
            establecimiento: p.establecimiento.nombre,
            ecorregion: p.establecimiento.ecorregion_nombre,
            superficie_total_ha: p.superficie.total_ha
        };
        features.push(parcelaExp);

        if (p.geometrias.sectores_cultivo && p.geometrias.sectores_cultivo.features) {
            p.geometrias.sectores_cultivo.features.forEach((f) => {
                const copy = JSON.parse(JSON.stringify(f));
                copy.properties = { ...(copy.properties || {}), capa: 'sector_cultivo' };
                features.push(copy);
            });
        }

        if (p.geometrias.zonas_florales_existentes && p.geometrias.zonas_florales_existentes.features) {
            p.geometrias.zonas_florales_existentes.features.forEach((f) => {
                const copy = JSON.parse(JSON.stringify(f));
                copy.properties = { ...(copy.properties || {}), capa: 'zona_floral_existente' };
                features.push(copy);
            });
        }

        const corredoresNuevos = p.geometrias.corredores_florales_nuevos || p.geometrias.corredores_florales;
        if (corredoresNuevos && corredoresNuevos.features) {
            corredoresNuevos.features.forEach((f) => {
                const copy = JSON.parse(JSON.stringify(f));
                copy.properties = {
                    ...(copy.properties || {}),
                    capa: 'corredor_floral_nuevo',
                    diseno: p.diseno_corredores.tipo
                };
                features.push(copy);
            });
        }

        const fc = turf.featureCollection(features);
        const blob = new Blob([JSON.stringify(fc, null, 2)], { type: 'application/geo+json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        const slug = (p.establecimiento.nombre || 'establecimiento').toLowerCase().replace(/[^a-z0-9]+/g, '_');
        a.href = url;
        a.download = `policampo_redisenio_${slug}.geojson`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
        mostrarToast('⬇️ Archivo GeoJSON descargado.');
    }

    // =========================================================================
    // 9. EVENTOS DE CONTROLES
    // =========================================================================
    function sincronizarPorcentaje(valor) {
        const limpio = Math.min(Math.max(parseInt(valor, 10) || 20, 1), 60);
        dom.porcentajeInput.value = limpio;
        dom.porcentajeSlider.value = Math.min(Math.max(limpio, 5), 40);
        dom.porcentajeLabel.textContent = `${limpio}%`;
        if (state.parcelaGeoJSON) generarDisenoSalida();
    }

    dom.tipoFranja.addEventListener('change', () => {
        actualizarControlesDinamicos();
        if (state.parcelaGeoJSON) generarDisenoSalida();
    });

    dom.porcentajeSlider.addEventListener('input', (e) => sincronizarPorcentaje(e.target.value));
    dom.porcentajeInput.addEventListener('input', (e) => sincronizarPorcentaje(e.target.value));

    dom.numCorredores.addEventListener('input', (e) => {
        dom.numCorredoresLabel.textContent = e.target.value;
        if (state.parcelaGeoJSON) generarDisenoSalida();
    });

    function actualizarAngulo(valor) {
        dom.anguloCorredores.value = valor;
        dom.anguloCorredoresLabel.textContent = describirAngulo(valor);
        dom.chipsOrientacion.forEach((chip) => {
            chip.classList.toggle('activo', chip.getAttribute('data-angulo') === String(valor));
        });
        if (state.parcelaGeoJSON) generarDisenoSalida();
    }

    dom.anguloCorredores.addEventListener('input', (e) => actualizarAngulo(e.target.value));
    dom.chipsOrientacion.forEach((chip) => {
        chip.addEventListener('click', () => {
            if (dom.anguloCorredores.disabled) return;
            actualizarAngulo(chip.getAttribute('data-angulo'));
        });
    });

    dom.densidadIslas.addEventListener('input', (e) => {
        dom.densidadIslasLabel.textContent = `${e.target.value} × ${e.target.value}`;
        if (state.parcelaGeoJSON) generarDisenoSalida();
    });

    dom.descontarExistentes.addEventListener('change', () => {
        if (state.parcelaGeoJSON) generarDisenoSalida();
    });

    // Capas de leyenda
    dom.toggleParcela.addEventListener('change', (e) => {
        if (e.target.checked) map.addLayer(capaParcela);
        else map.removeLayer(capaParcela);
    });
    dom.toggleSectores.addEventListener('change', (e) => {
        if (e.target.checked) map.addLayer(capaSectores);
        else map.removeLayer(capaSectores);
    });
    dom.toggleExistentes.addEventListener('change', (e) => {
        if (e.target.checked) map.addLayer(capaExistentes);
        else map.removeLayer(capaExistentes);
    });
    dom.togglePropuesta.addEventListener('change', (e) => {
        if (e.target.checked) map.addLayer(capaPropuesta);
        else map.removeLayer(capaPropuesta);
    });

    // Botones principales
    function cargarDemo() {
        const demoPayload = construirPayloadDemo();
        try {
            localStorage.setItem(C.STORAGE_KEY_ENTRADA, JSON.stringify(demoPayload));
        } catch (e) { /* noop */ }
        cargarTerrenoEnSalida(demoPayload);
        mostrarToast('📍 Finca de ejemplo en Perico cargada. Probá las distintas disposiciones florales.');
    }

    //dom.btnCargarDemo.addEventListener('click', cargarDemo);
    //dom.btnDemoBanner.addEventListener('click', cargarDemo);
    //dom.btnImprimir.addEventListener('click', () => window.print());
    dom.btnGuardarPropuesta.addEventListener('click', guardarPropuesta);
    dom.btnDescargarGeoJSON.addEventListener('click', descargarGeoJSON);

    dom.btnVerJSON.addEventListener('click', () => {
        if (!state.ultimoPayloadSalida) return;
        dom.previewJsonCode.textContent = JSON.stringify(state.ultimoPayloadSalida, null, 2);
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

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') cerrarModalJson();
    });

    // =========================================================================
    // 10. INICIO AUTOMÁTICO (Django context o localStorage)
    // =========================================================================
    function iniciar() {
        if (window.POLICAMPO_TERRENO_INICIAL) {
            cargarTerrenoEnSalida(window.POLICAMPO_TERRENO_INICIAL);
            return;
        }

        try {
            const raw = localStorage.getItem(C.STORAGE_KEY_ENTRADA);
            if (raw) {
                const parsed = JSON.parse(raw);
                cargarTerrenoEnSalida(parsed);
                return;
            }
        } catch (e) {
            console.warn('Error leyendo terreno desde localStorage:', e);
        }

        cargarTerrenoEnSalida(null);
    }

    iniciar();

    // API pública para los compañeros de Diagnóstico, Plantas y Calendario
    window.PoliCampoSalida = {
        getTerrenoEntrada: () => state.entrada,
        getPropuestaActual: () => state.ultimoPayloadSalida,
        cargarTerreno: (datos) => cargarTerrenoEnSalida(datos)
    };
})();
