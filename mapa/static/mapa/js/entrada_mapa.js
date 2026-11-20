/**
 * PoliCampo - Página 1: Entrada de Datos y Delimitación de Terreno
 * -----------------------------------------------------------------
 * Gestiona:
 *  - Datos del establecimiento (nombre, dirección, departamento, localidad, ecorregión)
 *  - Dibujo y edición del contorno de la parcela en Leaflet + Geoman
 *  - Cálculo automático de superficie total (ha) editable manualmente
 *  - Carga directa de múltiples sectores de cultivo recortados a la parcela
 *  - Persistencia en localStorage + inputs ocultos + POST opcional a Django
 */

(function () {
    'use strict';

    const C = window.PoliCampoCommon;

    // =========================================================================
    // 1. ESTADO
    // =========================================================================
    const state = {
        poligonoBaseLayer: null,
        poligonoBaseGeoJSON: null,
        areaMapaM2: 0,
        areaMapaHa: 0,
        perimetroM: 0,
        superficieEditadaManualmente: false,
        sectores: [], // [{ id, nombre, cultivoKey, cultivoPersonalizado, geojson, areaMapaM2 }]
        zonasFlorales: [], // [{ id, nombre, tipoKey, especies, geojson, areaMapaM2 }]
        modoDibujo: 'parcela', // 'parcela' | 'sector' | 'zona_floral'
        sectorPendienteGeoJSON: null,
        floralPendienteGeoJSON: null,
        ultimoPayload: null
    };

    // =========================================================================
    // 2. REFERENCIAS DOM
    // =========================================================================
    const dom = {
        nombreEstablecimiento: document.getElementById('nombre-establecimiento'),
        departamento: document.getElementById('departamento'),
        localidad: document.getElementById('localidad'),
        direccion: document.getElementById('direccion-establecimiento'),
        ecorregion: document.getElementById('ecorregion'),
        btnBuscarDireccion: document.getElementById('btn-buscar-direccion'),
        btnMiUbicacion: document.getElementById('btn-mi-ubicacion'),
        estadoBusqueda: document.getElementById('estado-busqueda'),

        btnCargarDemo: document.getElementById('btn-cargar-demo'),
        btnDibujarParcela: document.getElementById('btn-dibujar-parcela'),
        btnLimpiarTodo: document.getElementById('btn-limpiar-todo'),
        alertaGeometria: document.getElementById('alerta-geometria'),

        superficieInput: document.getElementById('superficie-total-ha'),
        btnSincronizarArea: document.getElementById('btn-sincronizar-area'),
        metaSuperficieMapa: document.getElementById('meta-superficie-mapa'),
        metaPerimetro: document.getElementById('meta-perimetro'),

        btnAgregarSector: document.getElementById('btn-agregar-sector'),
        btnSectorCompleto: document.getElementById('btn-sector-completo'),
        listaSectores: document.getElementById('lista-sectores'),
        resumenCobertura: document.getElementById('resumen-cobertura'),
        coberturaPct: document.getElementById('cobertura-pct'),
        coberturaLibre: document.getElementById('cobertura-libre'),

        btnAgregarZonaFloral: document.getElementById('btn-agregar-zona-floral'),
        listaZonasFlorales: document.getElementById('lista-zonas-florales'),
        resumenFloralExistente: document.getElementById('resumen-floral-existente'),
        floralExistentePct: document.getElementById('floral-existente-pct'),
        floralExistenteHa: document.getElementById('floral-existente-ha'),

        btnContinuarPropuesta: document.getElementById('btn-continuar-propuesta'),
        btnGuardarBorrador: document.getElementById('btn-guardar-borrador'),
        btnVerJSON: document.getElementById('btn-ver-json'),

        inputParcela: document.getElementById('django-parcela-geojson'),
        inputSectores: document.getElementById('django-sectores-geojson'),
        inputZonasFlorales: document.getElementById('django-zonas-florales-geojson'),
        inputEntradaJson: document.getElementById('django-entrada-json'),

        mapToast: document.getElementById('map-toast'),
        toggleParcela: document.getElementById('toggle-capa-parcela'),
        toggleSectores: document.getElementById('toggle-capa-sectores'),
        toggleFlorales: document.getElementById('toggle-capa-florales'),

        modalSector: document.getElementById('modal-sector'),
        sectorNombre: document.getElementById('sector-nombre'),
        sectorCultivo: document.getElementById('sector-cultivo'),
        grupoCultivoOtro: document.getElementById('grupo-cultivo-otro'),
        sectorCultivoOtro: document.getElementById('sector-cultivo-otro'),
        btnCancelarSector: document.getElementById('btn-cancelar-sector'),
        btnCancelarSector2: document.getElementById('btn-cancelar-sector-2'),
        btnConfirmarSector: document.getElementById('btn-confirmar-sector'),

        modalZonaFloral: document.getElementById('modal-zona-floral'),
        floralNombre: document.getElementById('floral-nombre'),
        floralTipo: document.getElementById('floral-tipo'),
        floralEspecies: document.getElementById('floral-especies'),
        btnCancelarFloral: document.getElementById('btn-cancelar-floral'),
        btnCancelarFloral2: document.getElementById('btn-cancelar-floral-2'),
        btnConfirmarFloral: document.getElementById('btn-confirmar-floral'),

        modalJson: document.getElementById('modal-json'),
        previewJsonCode: document.getElementById('preview-json-code'),
        btnCerrarModal: document.getElementById('btn-cerrar-modal'),
        btnCerrarModal2: document.getElementById('btn-cerrar-modal-2'),
        btnCopiarJson: document.getElementById('btn-copiar-json')
    };

    // =========================================================================
    // 3. INICIALIZACIÓN DE SELECTORES (JUJUY, ECORREGIONES, CULTIVOS)
    // =========================================================================
    C.poblarSelectEcorregiones(dom.ecorregion);
    C.poblarSelectCultivos(dom.sectorCultivo);
    C.poblarSelectZonasFlorales(dom.floralTipo);

    Object.keys(C.JUJUY_DEPARTAMENTOS).forEach((depto) => {
        const opt = document.createElement('option');
        opt.value = depto;
        opt.textContent = depto;
        dom.departamento.appendChild(opt);
    });

    function poblarLocalidades(depto, seleccionarLocalidad = null) {
        const info = C.JUJUY_DEPARTAMENTOS[depto];
        dom.localidad.innerHTML = '';
        if (!info) return;

        info.localidades.forEach((loc) => {
            const opt = document.createElement('option');
            opt.value = loc.nombre;
            opt.textContent = loc.nombre;
            opt.dataset.lat = loc.lat;
            opt.dataset.lng = loc.lng;
            opt.dataset.zoom = loc.zoom;
            dom.localidad.appendChild(opt);
        });

        if (seleccionarLocalidad) {
            dom.localidad.value = seleccionarLocalidad;
        }
    }

    // Valor inicial: El Carmen - Perico (Valles Templados)
    dom.departamento.value = 'El Carmen';
    poblarLocalidades('El Carmen', 'Perico');
    dom.ecorregion.value = C.JUJUY_DEPARTAMENTOS['El Carmen'].ecorregion;

    // =========================================================================
    // 4. INICIALIZACIÓN DEL MAPA LEAFLET + GEOMAN
    // =========================================================================
    const map = L.map('mapa', {
        center: [-24.3833, -65.1167],
        zoom: 14
    });

    const bases = C.crearCapasBaseLeaflet();
    bases.predeterminada.addTo(map);
    L.control.layers(bases.control, null, { position: 'topright' }).addTo(map);
    L.control.scale({ metric: true, imperial: false, position: 'bottomleft' }).addTo(map);

    const capaPoligonos = L.featureGroup().addTo(map);
    const capaSectores = L.featureGroup().addTo(map);
    const capaFloralesExistentes = L.featureGroup().addTo(map);

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
    // 5. HELPERS DE INTERFAZ
    // =========================================================================
    let toastTimer = null;
    function mostrarToast(msg, duracionMs = 3800) {
        dom.mapToast.textContent = msg;
        dom.mapToast.classList.remove('oculto');
        clearTimeout(toastTimer);
        if (duracionMs > 0) {
            toastTimer = setTimeout(() => dom.mapToast.classList.add('oculto'), duracionMs);
        }
    }

    function ocultarToast() {
        clearTimeout(toastTimer);
        dom.mapToast.classList.add('oculto');
    }

    function mostrarAlertaGeometria(msg) {
        if (!msg) {
            dom.alertaGeometria.classList.add('oculto');
            dom.alertaGeometria.textContent = '';
        } else {
            dom.alertaGeometria.textContent = msg;
            dom.alertaGeometria.classList.remove('oculto');
        }
    }

    function habilitarControlesTerreno(habilitado) {
        dom.btnLimpiarTodo.disabled = !habilitado;
        dom.superficieInput.disabled = !habilitado;
        dom.btnAgregarSector.disabled = !habilitado;
        dom.btnSectorCompleto.disabled = !habilitado;
        dom.btnAgregarZonaFloral.disabled = !habilitado;
        dom.btnContinuarPropuesta.disabled = !habilitado;
        dom.btnGuardarBorrador.disabled = !habilitado;
        dom.btnVerJSON.disabled = !habilitado;
    }

    function obtenerSuperficieOficialHa() {
        const val = parseFloat(dom.superficieInput.value);
        if (!Number.isNaN(val) && val > 0) return val;
        return state.areaMapaHa;
    }

    function centrarEnLocalidadSeleccionada() {
        const opt = dom.localidad.options[dom.localidad.selectedIndex];
        if (!opt || !opt.dataset.lat) return;
        map.flyTo(
            [parseFloat(opt.dataset.lat), parseFloat(opt.dataset.lng)],
            parseInt(opt.dataset.zoom, 10) || 14,
            { duration: 0.9 }
        );
    }

    // =========================================================================
    // 6. VALIDACIÓN Y GESTIÓN DE LA PARCELA
    // =========================================================================
    const ESTILO_PARCELA = {
        color: '#1b4332',
        weight: 3,
        fillColor: '#40916c',
        fillOpacity: 0.18
    };

    function validarPoligono(geojson) {
        try {
            const limpio = turf.cleanCoords(geojson);
            const area = turf.area(limpio);
            if (!area || area < 50) {
                return { valido: false, error: 'El polígono dibujado es demasiado pequeño (mínimo 50 m²).' };
            }
            const kinks = turf.kinks(limpio);
            if (kinks && kinks.features && kinks.features.length > 0) {
                return { valido: false, error: 'El contorno se cruza consigo mismo. Editá los vértices para eliminar cruces.' };
            }
            return { valido: true, geojson: limpio };
        } catch (err) {
            return { valido: false, error: 'No se pudo procesar la geometría del terreno.' };
        }
    }

    function actualizarUISuperficie() {
        if (!state.poligonoBaseGeoJSON) {
            dom.superficieInput.value = '';
            dom.metaSuperficieMapa.textContent = 'Dibujá el terreno para calcular el área';
            dom.metaPerimetro.textContent = 'Perímetro: —';
            dom.btnSincronizarArea.classList.add('oculto');
            return;
        }

        if (!state.superficieEditadaManualmente) {
            dom.superficieInput.value = state.areaMapaHa.toFixed(2);
            dom.metaSuperficieMapa.textContent = `Calculada del mapa: ${C.formatearNumero(state.areaMapaM2, 0)} m²`;
            dom.btnSincronizarArea.classList.add('oculto');
        } else {
            dom.metaSuperficieMapa.textContent = `Editada manualmente (mapa: ${C.formatearNumero(state.areaMapaHa, 2)} ha)`;
            dom.btnSincronizarArea.classList.remove('oculto');
        }

        dom.metaPerimetro.textContent = `Perímetro: ${C.formatearNumero(state.perimetroM, 0)} m`;
    }

    function actualizarDesdeLayerBase() {
        if (!state.poligonoBaseLayer) return;
        const validacion = validarPoligono(state.poligonoBaseLayer.toGeoJSON());

        if (!validacion.valido) {
            mostrarAlertaGeometria(validacion.error);
            return;
        }

        mostrarAlertaGeometria(null);
        state.poligonoBaseGeoJSON = validacion.geojson;
        state.areaMapaM2 = turf.area(validacion.geojson);
        state.areaMapaHa = state.areaMapaM2 / 10000;
        state.perimetroM = turf.length(turf.polygonToLine(validacion.geojson), { units: 'kilometers' }) * 1000;

        actualizarUISuperficie();
        reRecortarSectores();
        reRecortarZonasFlorales();
        actualizarListaSectores();
        actualizarListaZonasFlorales();
        actualizarPayloadEntrada();
    }

    function cargarParcelaBase(layer, ajustarVista = false, conservarSectores = false) {
        capaPoligonos.clearLayers();
        if (!conservarSectores) {
            capaSectores.clearLayers();
            capaFloralesExistentes.clearLayers();
            state.sectores = [];
            state.zonasFlorales = [];
        }

        layer.setStyle(ESTILO_PARCELA);
        capaPoligonos.addLayer(layer);
        state.poligonoBaseLayer = layer;

        layer.on('pm:edit', actualizarDesdeLayerBase);
        layer.on('pm:dragend', actualizarDesdeLayerBase);

        habilitarControlesTerreno(true);
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
        capaFloralesExistentes.clearLayers();

        state.poligonoBaseLayer = null;
        state.poligonoBaseGeoJSON = null;
        state.areaMapaM2 = 0;
        state.areaMapaHa = 0;
        state.perimetroM = 0;
        state.superficieEditadaManualmente = false;
        state.sectores = [];
        state.zonasFlorales = [];
        state.modoDibujo = 'parcela';
        state.ultimoPayload = null;

        habilitarControlesTerreno(false);
        mostrarAlertaGeometria(null);
        actualizarUISuperficie();
        actualizarListaSectores();
        actualizarListaZonasFlorales();

        dom.inputParcela.value = '';
        dom.inputSectores.value = '';
        dom.inputZonasFlorales.value = '';
        dom.inputEntradaJson.value = '';

        mostrarToast('Mapa limpiado. Delimitá un nuevo terreno cuando quieras.');
    }

    // =========================================================================
    // 7. SECTORES DE CULTIVO
    // =========================================================================
    function obtenerNombreCultivo(sector) {
        if (sector.cultivoKey === 'otro' && sector.cultivoPersonalizado) {
            return sector.cultivoPersonalizado;
        }
        return (C.CATALOGO_CULTIVOS[sector.cultivoKey] || C.CATALOGO_CULTIVOS.otro).nombre;
    }

    function reRecortarSectores() {
        if (!state.poligonoBaseGeoJSON || state.sectores.length === 0) return;

        const vigentes = [];
        state.sectores.forEach((sec) => {
            try {
                const recortado = turf.intersect(state.poligonoBaseGeoJSON, sec.geojson);
                if (recortado && turf.area(recortado) > 20) {
                    vigentes.push({
                        ...sec,
                        geojson: recortado,
                        areaMapaM2: turf.area(recortado)
                    });
                }
            } catch (e) {
                // Omitir sector que quedó fuera
            }
        });

        state.sectores = vigentes;
        renderizarSectores();
    }

    function renderizarSectores() {
        capaSectores.clearLayers();
        const supOficial = obtenerSuperficieOficialHa();

        state.sectores.forEach((sec) => {
            const info = C.CATALOGO_CULTIVOS[sec.cultivoKey] || C.CATALOGO_CULTIVOS.otro;
            const pct = state.areaMapaM2 > 0 ? (sec.areaMapaM2 / state.areaMapaM2) * 100 : 0;
            const areaEscalHa = supOficial * (pct / 100);

            const geoLayer = L.geoJSON(sec.geojson, {
                pmIgnore: true,
                style: {
                    pmIgnore: true,
                    color: info.color,
                    weight: 2.2,
                    fillColor: info.fillColor,
                    fillOpacity: 0.45
                },
                onEachFeature: (_feat, layer) => {
                    layer.options.pmIgnore = true;
                }
            });

            geoLayer.bindPopup(`
                <div style="font-family: Inter, sans-serif; font-size: 12.5px; line-height: 1.4;">
                    <strong>${info.icono} ${sec.nombre}</strong><br>
                    <strong>Cultivo:</strong> ${obtenerNombreCultivo(sec)}<br>
                    <strong>Superficie:</strong> ${C.formatearNumero(areaEscalHa, 2)} ha (${C.formatearNumero(pct, 1)}%)
                </div>
            `);

            geoLayer.addTo(capaSectores);
        });
    }

    function calcularAreaCubiertaSectoresM2() {
        if (state.sectores.length === 0) return 0;
        try {
            let unionGeo = state.sectores[0].geojson;
            for (let i = 1; i < state.sectores.length; i++) {
                unionGeo = turf.union(unionGeo, state.sectores[i].geojson) || unionGeo;
            }
            return Math.min(turf.area(unionGeo), state.areaMapaM2);
        } catch (e) {
            const suma = state.sectores.reduce((acc, s) => acc + s.areaMapaM2, 0);
            return Math.min(suma, state.areaMapaM2);
        }
    }

    function actualizarListaSectores() {
        dom.listaSectores.innerHTML = '';

        if (state.sectores.length === 0) {
            dom.listaSectores.innerHTML = '<li class="lista-vacia">Todavía no agregaste sectores de cultivo.</li>';
            dom.resumenCobertura.classList.add('oculto');
            return;
        }

        const supOficial = obtenerSuperficieOficialHa();

        state.sectores.forEach((sec) => {
            const info = C.CATALOGO_CULTIVOS[sec.cultivoKey] || C.CATALOGO_CULTIVOS.otro;
            const pct = state.areaMapaM2 > 0 ? (sec.areaMapaM2 / state.areaMapaM2) * 100 : 0;
            const areaHa = supOficial * (pct / 100);

            const li = document.createElement('li');
            li.className = 'sector-item';
            li.innerHTML = `
                <div class="sector-info">
                    <span class="sector-dot" style="background:${info.color};"></span>
                    <div>
                        <strong>${sec.nombre}</strong> · ${obtenerNombreCultivo(sec)}
                        <div class="sector-submeta">${C.formatearNumero(areaHa, 2)} ha (${C.formatearNumero(pct, 1)}%)</div>
                    </div>
                </div>
                <button type="button" class="btn-del-sector" title="Eliminar sector" data-id="${sec.id}">&times;</button>
            `;
            dom.listaSectores.appendChild(li);
        });

        const cubiertaM2 = calcularAreaCubiertaSectoresM2();
        const pctCubierto = state.areaMapaM2 > 0 ? Math.min((cubiertaM2 / state.areaMapaM2) * 100, 100) : 0;
        const libreHa = Math.max(supOficial * (1 - pctCubierto / 100), 0);

        dom.coberturaPct.textContent = `${C.formatearNumero(pctCubierto, 1)}%`;
        dom.coberturaLibre.textContent = libreHa < 0.01
            ? '100% asignado'
            : `Sin asignar: ${C.formatearNumero(libreHa, 2)} ha`;
        dom.resumenCobertura.classList.remove('oculto');
    }

    function abrirModalSector(geojsonSector, nombreSugerido = null) {
        state.sectorPendienteGeoJSON = geojsonSector;
        dom.sectorNombre.value = nombreSugerido || `Sector ${state.sectores.length + 1}`;
        dom.sectorCultivo.value = 'frutilla';
        dom.sectorCultivoOtro.value = '';
        dom.grupoCultivoOtro.classList.add('oculto');
        dom.modalSector.classList.remove('oculto');
        dom.sectorNombre.focus();
    }

    function cerrarModalSector() {
        state.sectorPendienteGeoJSON = null;
        dom.modalSector.classList.add('oculto');
        state.modoDibujo = 'parcela';
    }

    // =========================================================================
    // 7B. ZONAS FLORALES EXISTENTES (CONTRIBUYEN A LAS FRANJAS FLORALES)
    // =========================================================================
    function reRecortarZonasFlorales() {
        if (!state.poligonoBaseGeoJSON || state.zonasFlorales.length === 0) return;

        const vigentes = [];
        state.zonasFlorales.forEach((zf) => {
            try {
                const recortado = turf.intersect(state.poligonoBaseGeoJSON, zf.geojson);
                if (recortado && turf.area(recortado) > 10) {
                    vigentes.push({
                        ...zf,
                        geojson: recortado,
                        areaMapaM2: turf.area(recortado)
                    });
                }
            } catch (e) {
                // Omitir si quedó fuera tras editar la parcela
            }
        });

        state.zonasFlorales = vigentes;
        renderizarZonasFlorales();
    }

    function calcularAreaCubiertaFloralesM2() {
        if (state.zonasFlorales.length === 0) return 0;
        try {
            let unionGeo = state.zonasFlorales[0].geojson;
            for (let i = 1; i < state.zonasFlorales.length; i++) {
                unionGeo = turf.union(unionGeo, state.zonasFlorales[i].geojson) || unionGeo;
            }
            return Math.min(turf.area(unionGeo), state.areaMapaM2);
        } catch (e) {
            const suma = state.zonasFlorales.reduce((acc, z) => acc + z.areaMapaM2, 0);
            return Math.min(suma, state.areaMapaM2);
        }
    }

    function renderizarZonasFlorales() {
        capaFloralesExistentes.clearLayers();
        const supOficial = obtenerSuperficieOficialHa();

        state.zonasFlorales.forEach((zf) => {
            const info = C.CATALOGO_ZONAS_FLORALES[zf.tipoKey] || C.CATALOGO_ZONAS_FLORALES.otro;
            const pct = state.areaMapaM2 > 0 ? (zf.areaMapaM2 / state.areaMapaM2) * 100 : 0;
            const areaHa = supOficial * (pct / 100);

            const geoLayer = L.geoJSON(zf.geojson, {
                pmIgnore: true,
                style: {
                    pmIgnore: true,
                    color: info.color,
                    weight: 2.5,
                    fillColor: info.fillColor,
                    fillOpacity: 0.52,
                    dashArray: '5, 4'
                },
                onEachFeature: (_feat, layer) => {
                    layer.options.pmIgnore = true;
                }
            });

            const especiesHtml = zf.especies
                ? `<br><strong>Especies:</strong> ${zf.especies}`
                : '';

            geoLayer.bindPopup(`
                <div style="font-family: Inter, sans-serif; font-size: 12.5px; line-height: 1.4;">
                    <strong style="color:${info.color};">${info.icono} ${zf.nombre}</strong><br>
                    <strong>Tipo:</strong> ${info.nombre}${especiesHtml}<br>
                    <strong>Aporte actual:</strong> ${C.formatearNumero(areaHa, 3)} ha (${C.formatearNumero(pct, 1)}%)
                </div>
            `);

            geoLayer.addTo(capaFloralesExistentes);
        });

        capaFloralesExistentes.bringToFront();
    }

    function actualizarListaZonasFlorales() {
        dom.listaZonasFlorales.innerHTML = '';

        if (state.zonasFlorales.length === 0) {
            dom.listaZonasFlorales.innerHTML = '<li class="lista-vacia">Sin zonas florales existentes marcadas.</li>';
            dom.resumenFloralExistente.classList.add('oculto');
            return;
        }

        const supOficial = obtenerSuperficieOficialHa();

        state.zonasFlorales.forEach((zf) => {
            const info = C.CATALOGO_ZONAS_FLORALES[zf.tipoKey] || C.CATALOGO_ZONAS_FLORALES.otro;
            const pct = state.areaMapaM2 > 0 ? (zf.areaMapaM2 / state.areaMapaM2) * 100 : 0;
            const areaHa = supOficial * (pct / 100);
            const detalleEspecies = zf.especies ? ` · ${zf.especies}` : '';

            const li = document.createElement('li');
            li.className = 'sector-item sector-item-floral';
            li.innerHTML = `
                <div class="sector-info">
                    <span class="sector-dot" style="background:${info.color};"></span>
                    <div>
                        <strong>${zf.nombre}</strong> · ${info.nombre}
                        <div class="sector-submeta">${C.formatearNumero(areaHa, 2)} ha (${C.formatearNumero(pct, 1)}%)${detalleEspecies}</div>
                    </div>
                </div>
                <button type="button" class="btn-del-floral" title="Eliminar zona floral" data-id="${zf.id}">&times;</button>
            `;
            dom.listaZonasFlorales.appendChild(li);
        });

        const cubiertaM2 = calcularAreaCubiertaFloralesM2();
        const pctTotal = state.areaMapaM2 > 0 ? Math.min((cubiertaM2 / state.areaMapaM2) * 100, 100) : 0;
        const areaTotalHa = supOficial * (pctTotal / 100);

        dom.floralExistentePct.textContent = `${C.formatearNumero(pctTotal, 1)}%`;
        dom.floralExistenteHa.textContent = `${C.formatearNumero(areaTotalHa, 2)} ha`;
        dom.resumenFloralExistente.classList.remove('oculto');
    }

    function abrirModalFloral(geojsonRecortado) {
        state.floralPendienteGeoJSON = geojsonRecortado;
        dom.floralNombre.value = `Zona floral ${state.zonasFlorales.length + 1}`;
        dom.floralTipo.value = 'flora_espontanea';
        dom.floralEspecies.value = '';
        dom.modalZonaFloral.classList.remove('oculto');
        dom.floralNombre.focus();
    }

    function cerrarModalFloral() {
        state.floralPendienteGeoJSON = null;
        dom.modalZonaFloral.classList.add('oculto');
        state.modoDibujo = 'parcela';
    }

    // =========================================================================
    // 8. PAYLOAD E INTEGRACIÓN CON DJANGO + PÁGINA 2
    // =========================================================================
    function actualizarPayloadEntrada() {
        if (!state.poligonoBaseGeoJSON) return null;

        const centroide = turf.centerOfMass(state.poligonoBaseGeoJSON);
        const supOficialHa = obtenerSuperficieOficialHa();
        const ecorregionId = dom.ecorregion.value;

        const sectoresFeatures = state.sectores.map((s) => {
            const pct = state.areaMapaM2 > 0 ? (s.areaMapaM2 / state.areaMapaM2) * 100 : 0;
            const areaHa = supOficialHa * (pct / 100);
            const info = C.CATALOGO_CULTIVOS[s.cultivoKey] || C.CATALOGO_CULTIVOS.otro;
            return {
                type: 'Feature',
                geometry: s.geojson.geometry,
                properties: {
                    id: s.id,
                    nombre: s.nombre,
                    cultivo: s.cultivoKey,
                    cultivo_nombre: obtenerNombreCultivo(s),
                    color: info.color,
                    fillColor: info.fillColor,
                    porcentaje_parcela: Number(pct.toFixed(2)),
                    area_ha: Number(areaHa.toFixed(4))
                }
            };
        });

        const sectoresFC = turf.featureCollection(sectoresFeatures);

        const floralesFeatures = state.zonasFlorales.map((zf) => {
            const pct = state.areaMapaM2 > 0 ? (zf.areaMapaM2 / state.areaMapaM2) * 100 : 0;
            const areaHa = supOficialHa * (pct / 100);
            const info = C.CATALOGO_ZONAS_FLORALES[zf.tipoKey] || C.CATALOGO_ZONAS_FLORALES.otro;
            return {
                type: 'Feature',
                geometry: zf.geojson.geometry,
                properties: {
                    id: zf.id,
                    nombre: zf.nombre,
                    tipo: zf.tipoKey,
                    tipo_nombre: info.nombre,
                    especies: zf.especies || '',
                    color: info.color,
                    fillColor: info.fillColor,
                    porcentaje_parcela: Number(pct.toFixed(2)),
                    area_ha: Number(areaHa.toFixed(4))
                }
            };
        });
        const floralesFC = turf.featureCollection(floralesFeatures);

        const areaFloralesUnionM2 = calcularAreaCubiertaFloralesM2();
        const pctFloralesTotal = state.areaMapaM2 > 0
            ? Math.min((areaFloralesUnionM2 / state.areaMapaM2) * 100, 100)
            : 0;
        const areaFloralesTotalHa = supOficialHa * (pctFloralesTotal / 100);

        const payload = {
            version: '2.1',
            timestamp: new Date().toISOString(),
            establecimiento: {
                nombre: dom.nombreEstablecimiento.value.trim(),
                direccion: dom.direccion.value.trim(),
                departamento: dom.departamento.value,
                localidad: dom.localidad.value,
                ecorregion: ecorregionId,
                ecorregion_nombre: C.obtenerNombreEcorregion(ecorregionId)
            },
            ubicacion_centroide: {
                lat: Number(centroide.geometry.coordinates[1].toFixed(6)),
                lng: Number(centroide.geometry.coordinates[0].toFixed(6))
            },
            superficie: {
                total_ha: Number(supOficialHa.toFixed(4)),
                calculada_mapa_ha: Number(state.areaMapaHa.toFixed(4)),
                calculada_mapa_m2: Math.round(state.areaMapaM2),
                perimetro_m: Math.round(state.perimetroM),
                editada_manualmente: state.superficieEditadaManualmente
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
                area_total_ha: Number(areaFloralesTotalHa.toFixed(4)),
                porcentaje_parcela: Number(pctFloralesTotal.toFixed(2)),
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
                parcela: state.poligonoBaseGeoJSON,
                sectores_cultivo: sectoresFC,
                zonas_florales_existentes: floralesFC
            }
        };

        state.ultimoPayload = payload;

        // Actualizar inputs ocultos de Django
        dom.inputParcela.value = JSON.stringify(payload.geometrias.parcela);
        dom.inputSectores.value = JSON.stringify(payload.geometrias.sectores_cultivo);
        dom.inputZonasFlorales.value = JSON.stringify(payload.geometrias.zonas_florales_existentes);
        dom.inputEntradaJson.value = JSON.stringify({
            establecimiento: payload.establecimiento,
            ubicacion_centroide: payload.ubicacion_centroide,
            superficie: payload.superficie,
            cultivos_resumen: payload.cultivos_resumen,
            zonas_florales_existentes_resumen: payload.zonas_florales_existentes_resumen
        });

        return payload;
    }

    async function guardarEntrada(irAPropuesta = false) {
        const nombre = dom.nombreEstablecimiento.value.trim();
        if (!nombre) {
            dom.nombreEstablecimiento.focus();
            mostrarToast('⚠️ Ingresá el nombre del establecimiento antes de continuar.');
            return;
        }

        if (!state.poligonoBaseGeoJSON) {
            mostrarToast('⚠️ Primero delimitá el contorno del terreno en el mapa.');
            return;
        }

        if (state.sectores.length === 0) {
            mostrarToast('⚠️ Agregá al menos un sector de cultivo (o usá "Asignar 100% del terreno").');
            return;
        }

        const payload = actualizarPayloadEntrada();

        try {
            localStorage.setItem(C.STORAGE_KEY_ENTRADA, JSON.stringify(payload));
        } catch (e) {
            console.warn('No se pudo guardar en localStorage:', e);
        }

        window.dispatchEvent(new CustomEvent('policampo:entradaGuardada', { detail: payload }));

        // Si en Django definís window.POLICAMPO_API_GUARDAR_ENTRADA_URL, envía POST automático
        if (window.POLICAMPO_API_GUARDAR_ENTRADA_URL) {
            try {
                const resp = await fetch(window.POLICAMPO_API_GUARDAR_ENTRADA_URL, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': C.obtenerCookieCSRF()
                    },
                    body: JSON.stringify(payload)
                });
                if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            } catch (err) {
                console.error('Error al guardar en Django:', err);
                mostrarToast('⚠️ Se guardó localmente, pero hubo un error enviando al servidor.');
                return;
            }
        }

        if (irAPropuesta) {
            window.location.href = window.POLICAMPO_URL_PROPUESTA || 'propuesta_redisenio.html';
        } else {
            mostrarToast('✅ Datos del establecimiento y sectores guardados correctamente.');
        }
    }

    // =========================================================================
    // 9. CARGA DE EJEMPLO Y RESTAURACIÓN DESDE LOCALSTORAGE
    // =========================================================================
    function cargarEjemploPerico() {
        const demo = C.DEMO_TERRENO;
        dom.nombreEstablecimiento.value = demo.establecimiento.nombre;
        dom.direccion.value = demo.establecimiento.direccion;
        dom.departamento.value = demo.establecimiento.departamento;
        poblarLocalidades(demo.establecimiento.departamento, demo.establecimiento.localidad);
        dom.ecorregion.value = demo.establecimiento.ecorregion;

        state.superficieEditadaManualmente = false;

        const coordsLatLng = demo.parcela.geometry.coordinates[0].map(([lng, lat]) => [lat, lng]);
        const layer = L.polygon(coordsLatLng);
        cargarParcelaBase(layer, true, false);

        state.sectores = demo.sectores_demo.map((s, idx) => {
            const feat = { type: 'Feature', properties: {}, geometry: s.geometry };
            const recortado = turf.intersect(state.poligonoBaseGeoJSON, feat) || feat;
            return {
                id: `sec_demo_${idx + 1}`,
                nombre: s.nombre,
                cultivoKey: s.cultivoKey,
                cultivoPersonalizado: '',
                geojson: recortado,
                areaMapaM2: turf.area(recortado)
            };
        });

        state.zonasFlorales = (demo.zonas_florales_demo || []).map((z, idx) => {
            const feat = { type: 'Feature', properties: {}, geometry: z.geometry };
            const recortado = turf.intersect(state.poligonoBaseGeoJSON, feat) || feat;
            return {
                id: `zf_demo_${idx + 1}`,
                nombre: z.nombre,
                tipoKey: z.tipoKey,
                especies: z.especies || '',
                geojson: recortado,
                areaMapaM2: turf.area(recortado)
            };
        });

        renderizarSectores();
        renderizarZonasFlorales();
        actualizarListaSectores();
        actualizarListaZonasFlorales();
        actualizarPayloadEntrada();
        mostrarToast('📍 Ejemplo cargado (Finca Los Lapachos, Perico) con 2 sectores y 1 zona floral existente.');
    }

    function restaurarSiExiste() {
        let guardado = null;
        try {
            const raw = localStorage.getItem(C.STORAGE_KEY_ENTRADA);
            if (raw) guardado = JSON.parse(raw);
        } catch (e) {
            return;
        }
        if (!guardado || !guardado.geometrias || !guardado.geometrias.parcela) return;

        // Restaurar campos del establecimiento
        if (guardado.establecimiento) {
            dom.nombreEstablecimiento.value = guardado.establecimiento.nombre || '';
            dom.direccion.value = guardado.establecimiento.direccion || '';
            if (guardado.establecimiento.departamento && C.JUJUY_DEPARTAMENTOS[guardado.establecimiento.departamento]) {
                dom.departamento.value = guardado.establecimiento.departamento;
                poblarLocalidades(guardado.establecimiento.departamento, guardado.establecimiento.localidad);
            }
            if (guardado.establecimiento.ecorregion) {
                dom.ecorregion.value = guardado.establecimiento.ecorregion;
            }
        }

        // Restaurar bandera de superficie editada
        if (guardado.superficie && guardado.superficie.editada_manualmente) {
            state.superficieEditadaManualmente = true;
            dom.superficieInput.value = Number(guardado.superficie.total_ha).toFixed(2);
        }

        // Restaurar parcela
        const layer = L.geoJSON(guardado.geometrias.parcela).getLayers()[0];
        if (!layer) return;
        cargarParcelaBase(layer, true, false);

        // Restaurar sectores de cultivo
        if (guardado.geometrias.sectores_cultivo && guardado.geometrias.sectores_cultivo.features) {
            state.sectores = guardado.geometrias.sectores_cultivo.features.map((f, idx) => ({
                id: (f.properties && f.properties.id) || `sec_${idx + 1}`,
                nombre: (f.properties && f.properties.nombre) || `Sector ${idx + 1}`,
                cultivoKey: (f.properties && f.properties.cultivo) || 'horticolas',
                cultivoPersonalizado: (f.properties && f.properties.cultivo === 'otro')
                    ? (f.properties.cultivo_nombre || '')
                    : '',
                geojson: f,
                areaMapaM2: turf.area(f)
            }));
            renderizarSectores();
            actualizarListaSectores();
        }

        // Restaurar zonas florales existentes
        if (guardado.geometrias.zonas_florales_existentes && guardado.geometrias.zonas_florales_existentes.features) {
            state.zonasFlorales = guardado.geometrias.zonas_florales_existentes.features.map((f, idx) => ({
                id: (f.properties && f.properties.id) || `zf_${idx + 1}`,
                nombre: (f.properties && f.properties.nombre) || `Zona floral ${idx + 1}`,
                tipoKey: (f.properties && f.properties.tipo) || 'flora_espontanea',
                especies: (f.properties && f.properties.especies) || '',
                geojson: f,
                areaMapaM2: turf.area(f)
            }));
            renderizarZonasFlorales();
            actualizarListaZonasFlorales();
        }

        actualizarPayloadEntrada();
    }

    // =========================================================================
    // 10. EVENTOS DE GEOMAN Y UI
    // =========================================================================
    map.on('pm:create', (e) => {
        ocultarToast();

        if (state.modoDibujo === 'sector' && state.poligonoBaseGeoJSON) {
            const rawSector = e.layer.toGeoJSON();
            map.removeLayer(e.layer);

            try {
                const limpio = turf.cleanCoords(rawSector);
                const recortado = turf.intersect(state.poligonoBaseGeoJSON, limpio);
                if (!recortado || turf.area(recortado) < 20) {
                    mostrarToast('⚠️ El sector debe estar dentro del contorno del terreno.');
                    state.modoDibujo = 'parcela';
                    return;
                }
                abrirModalSector(recortado);
            } catch (err) {
                mostrarToast('⚠️ No se pudo recortar el sector. Dibujalo sin cruces de líneas.');
                state.modoDibujo = 'parcela';
            }
            return;
        }

        if (state.modoDibujo === 'zona_floral' && state.poligonoBaseGeoJSON) {
            const rawFloral = e.layer.toGeoJSON();
            map.removeLayer(e.layer);

            try {
                const limpio = turf.cleanCoords(rawFloral);
                const recortado = turf.intersect(state.poligonoBaseGeoJSON, limpio);
                if (!recortado || turf.area(recortado) < 10) {
                    mostrarToast('⚠️ La zona floral debe estar dentro del contorno del terreno.');
                    state.modoDibujo = 'parcela';
                    return;
                }
                abrirModalFloral(recortado);
            } catch (err) {
                mostrarToast('⚠️ No se pudo recortar la zona floral. Dibujala sin cruces de líneas.');
                state.modoDibujo = 'parcela';
            }
            return;
        }

        state.superficieEditadaManualmente = false;
        cargarParcelaBase(e.layer, false, false);
        mostrarToast('✅ Terreno delimitado. Ahora agregá tus sectores de cultivo (y zonas con flores si ya tenés).');
    });

    map.on('pm:remove', (e) => {
        if (e.layer === state.poligonoBaseLayer) {
            limpiarTodo();
        }
    });

    map.on('pm:drawend', () => {
        setTimeout(() => {
            if (!state.sectorPendienteGeoJSON && !state.floralPendienteGeoJSON) {
                state.modoDibujo = 'parcela';
            }
        }, 50);
    });

    // Departamento -> actualiza localidades + sugiere ecorregión + mueve el mapa
    dom.departamento.addEventListener('change', () => {
        const depto = dom.departamento.value;
        poblarLocalidades(depto);
        const info = C.JUJUY_DEPARTAMENTOS[depto];
        if (info && info.ecorregion) {
            dom.ecorregion.value = info.ecorregion;
        }
        centrarEnLocalidadSeleccionada();
        actualizarPayloadEntrada();
    });

    dom.localidad.addEventListener('change', () => {
        centrarEnLocalidadSeleccionada();
        actualizarPayloadEntrada();
    });

    dom.nombreEstablecimiento.addEventListener('input', actualizarPayloadEntrada);
    dom.direccion.addEventListener('input', actualizarPayloadEntrada);
    dom.ecorregion.addEventListener('change', actualizarPayloadEntrada);

    // Buscar dirección
    async function buscarDireccion() {
        const dir = dom.direccion.value.trim();
        const loc = dom.localidad.value;
        const depto = dom.departamento.value;
        const query = [dir, loc, depto, 'Jujuy, Argentina'].filter(Boolean).join(', ');

        dom.estadoBusqueda.textContent = 'Buscando ubicación...';
        try {
            const url = `https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(query)}`;
            const resp = await fetch(url, { headers: { 'Accept-Language': 'es' } });
            const data = await resp.json();
            if (data && data.length > 0) {
                map.flyTo([parseFloat(data[0].lat), parseFloat(data[0].lon)], 15, { duration: 1 });
                dom.estadoBusqueda.textContent = `Ubicado: ${data[0].display_name.split(',').slice(0, 2).join(',')}`;
            } else {
                dom.estadoBusqueda.textContent = 'No se encontró esa dirección exacta; centrá manualmente en el mapa.';
            }
        } catch (err) {
            dom.estadoBusqueda.textContent = 'Sin conexión al buscador. Usá departamento y localidad.';
        }
    }

    dom.btnBuscarDireccion.addEventListener('click', buscarDireccion);
    dom.direccion.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            buscarDireccion();
        }
    });

    // GPS
    dom.btnMiUbicacion.addEventListener('click', () => {
        if (!navigator.geolocation) {
            mostrarToast('Tu navegador no soporta GPS.');
            return;
        }
        mostrarToast('Obteniendo ubicación GPS...', 0);
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
            () => mostrarToast('No se pudo obtener la ubicación. Verificá los permisos.'),
            { enableHighAccuracy: true, timeout: 8000 }
        );
    });

    // Botones de parcela
    dom.btnDibujarParcela.addEventListener('click', () => {
        state.modoDibujo = 'parcela';
        map.pm.enableDraw('Polygon', { snappable: true, snapDistance: 15, finishOn: 'dblclick' });
        mostrarToast('✏️ Marcá los vértices del terreno y cerrá el contorno en el primer punto.', 0);
    });

    dom.btnLimpiarTodo.addEventListener('click', limpiarTodo);
    //dom.btnCargarDemo.addEventListener('click', cargarEjemploPerico);

    // Edición manual de superficie
    dom.superficieInput.addEventListener('input', () => {
        if (!state.poligonoBaseGeoJSON) return;
        state.superficieEditadaManualmente = true;
        actualizarUISuperficie();
        renderizarSectores();
        renderizarZonasFlorales();
        actualizarListaSectores();
        actualizarListaZonasFlorales();
        actualizarPayloadEntrada();
    });

    dom.btnSincronizarArea.addEventListener('click', () => {
        state.superficieEditadaManualmente = false;
        actualizarUISuperficie();
        renderizarSectores();
        renderizarZonasFlorales();
        actualizarListaSectores();
        actualizarListaZonasFlorales();
        actualizarPayloadEntrada();
        mostrarToast('↺ Superficie sincronizada con el cálculo del mapa.');
    });

    // Sectores de cultivo
    dom.btnAgregarSector.addEventListener('click', () => {
        if (!state.poligonoBaseGeoJSON) return;
        state.modoDibujo = 'sector';
        map.pm.enableDraw('Polygon', { snappable: true, snapDistance: 12 });
        mostrarToast('🌱 Dibujá un sector de cultivo dentro del terreno (se recorta solo).', 0);
    });

    dom.btnSectorCompleto.addEventListener('click', () => {
        if (!state.poligonoBaseGeoJSON) return;
        abrirModalSector(JSON.parse(JSON.stringify(state.poligonoBaseGeoJSON)), 'Lote Completo');
    });

    dom.sectorCultivo.addEventListener('change', () => {
        const esOtro = dom.sectorCultivo.value === 'otro';
        dom.grupoCultivoOtro.classList.toggle('oculto', !esOtro);
        if (esOtro) dom.sectorCultivoOtro.focus();
    });

    dom.btnConfirmarSector.addEventListener('click', () => {
        if (!state.sectorPendienteGeoJSON) return;
        const nombre = dom.sectorNombre.value.trim() || `Sector ${state.sectores.length + 1}`;
        const cultivoKey = dom.sectorCultivo.value;
        const cultivoPersonalizado = dom.sectorCultivoOtro.value.trim();

        // Si se asigna Lote Completo, reemplazamos sectores previos para no duplicar 100%
        const esCompleto = turf.area(state.sectorPendienteGeoJSON) >= state.areaMapaM2 * 0.99;
        if (esCompleto && state.sectores.length > 0) {
            state.sectores = [];
        }

        state.sectores.push({
            id: `sec_${Date.now()}`,
            nombre,
            cultivoKey,
            cultivoPersonalizado,
            geojson: state.sectorPendienteGeoJSON,
            areaMapaM2: turf.area(state.sectorPendienteGeoJSON)
        });

        cerrarModalSector();
        renderizarSectores();
        actualizarListaSectores();
        actualizarPayloadEntrada();
        mostrarToast(`🌱 Sector "${nombre}" agregado.`);
    });

    dom.btnCancelarSector.addEventListener('click', cerrarModalSector);
    dom.btnCancelarSector2.addEventListener('click', cerrarModalSector);

    dom.listaSectores.addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-del-sector');
        if (!btn) return;
        const id = btn.getAttribute('data-id');
        state.sectores = state.sectores.filter((s) => s.id !== id);
        renderizarSectores();
        actualizarListaSectores();
        actualizarPayloadEntrada();
    });

    // Zonas florales existentes
    dom.btnAgregarZonaFloral.addEventListener('click', () => {
        if (!state.poligonoBaseGeoJSON) return;
        state.modoDibujo = 'zona_floral';
        map.pm.enableDraw('Polygon', { snappable: true, snapDistance: 12 });
        mostrarToast('🌼 Dibujá la zona que ya tiene flores o vegetación natural dentro del terreno.', 0);
    });

    dom.btnConfirmarFloral.addEventListener('click', () => {
        if (!state.floralPendienteGeoJSON) return;
        const nombre = dom.floralNombre.value.trim() || `Zona floral ${state.zonasFlorales.length + 1}`;
        const tipoKey = dom.floralTipo.value;
        const especies = dom.floralEspecies.value.trim();

        state.zonasFlorales.push({
            id: `zf_${Date.now()}`,
            nombre,
            tipoKey,
            especies,
            geojson: state.floralPendienteGeoJSON,
            areaMapaM2: turf.area(state.floralPendienteGeoJSON)
        });

        cerrarModalFloral();
        renderizarZonasFlorales();
        actualizarListaZonasFlorales();
        actualizarPayloadEntrada();
        mostrarToast(`🌼 Zona floral "${nombre}" registrada.`);
    });

    dom.btnCancelarFloral.addEventListener('click', cerrarModalFloral);
    dom.btnCancelarFloral2.addEventListener('click', cerrarModalFloral);

    dom.listaZonasFlorales.addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-del-floral');
        if (!btn) return;
        const id = btn.getAttribute('data-id');
        state.zonasFlorales = state.zonasFlorales.filter((z) => z.id !== id);
        renderizarZonasFlorales();
        actualizarListaZonasFlorales();
        actualizarPayloadEntrada();
    });

    // Capas de leyenda
    dom.toggleParcela.addEventListener('change', (e) => {
        if (e.target.checked) map.addLayer(capaPoligonos);
        else map.removeLayer(capaPoligonos);
    });
    dom.toggleSectores.addEventListener('change', (e) => {
        if (e.target.checked) map.addLayer(capaSectores);
        else map.removeLayer(capaSectores);
    });
    dom.toggleFlorales.addEventListener('change', (e) => {
        if (e.target.checked) map.addLayer(capaFloralesExistentes);
        else map.removeLayer(capaFloralesExistentes);
    });

    // Guardado y modales
    dom.btnContinuarPropuesta.addEventListener('click', () => guardarEntrada(true));
    dom.btnGuardarBorrador.addEventListener('click', () => guardarEntrada(false));

    dom.btnVerJSON.addEventListener('click', () => {
        const payload = actualizarPayloadEntrada();
        if (!payload) return;
        dom.previewJsonCode.textContent = JSON.stringify(payload, null, 2);
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
        if (e.key === 'Escape') {
            cerrarModalJson();
            cerrarModalSector();
            cerrarModalFloral();
        }
    });

    // Restaurar datos si el usuario volvió desde la página de Propuesta para editar
    restaurarSiExiste();

    window.PoliCampoEntrada = {
        getPayload: () => actualizarPayloadEntrada(),
        cargarEjemplo: cargarEjemploPerico,
        limpiar: limpiarTodo
    };
})();
