/**
 * PoliCampo - Utilidades y Catálogos Compartidos (Entrada y Salida)
 * ------------------------------------------------------------------
 * Centraliza los cultivos, departamentos/localidades/ecorregiones de Jujuy,
 * datos de demostración y helpers comunes para ambos módulos de mapa.
 */

(function (global) {
    'use strict';

    // [Unificación] Un borrador distinto POR FINCA: la plantilla de Django define
    // window.POLICAMPO_ID_FINCA y se agrega al nombre de la clave
    // (ej.: "policampo_terreno_entrada_25"). Antes la clave era la misma para todas
    // las fincas y al abrir una nueva aparecía el dibujo de la anterior.
    const ID_FINCA = global.POLICAMPO_ID_FINCA;
    const SUFIJO_FINCA = ID_FINCA ? `_${ID_FINCA}` : '';
    const STORAGE_KEY_ENTRADA = `policampo_terreno_entrada${SUFIJO_FINCA}`;
    const STORAGE_KEY_SALIDA = `policampo_propuesta_salida${SUFIJO_FINCA}`;

    // Se borran los borradores viejos (compartidos por todas las fincas) para que no reaparezcan
    if (ID_FINCA) {
        try {
            global.localStorage.removeItem('policampo_terreno_entrada');
            global.localStorage.removeItem('policampo_propuesta_salida');
        } catch (e) {
            /* localStorage puede no estar disponible (modo privado): no pasa nada */
        }
    }

    const CATALOGO_CULTIVOS = {
        frutilla: {
            nombre: 'Frutilla',
            icono: '🍓',
            color: '#e11d48',
            fillColor: '#fb7185'
        },
        arandano: {
            nombre: 'Arándano',
            icono: '🫐',
            color: '#4f46e5',
            fillColor: '#818cf8'
        },
        durazno: {
            nombre: 'Durazno',
            icono: '🍑',
            color: '#ea580c',
            fillColor: '#fb923c'
        },
        tomate: {
            nombre: 'Tomate',
            icono: '🍅',
            color: '#dc2626',
            fillColor: '#f87171'
        },
        pimiento: {
            nombre: 'Pimiento',
            icono: '🫑',
            color: '#16a34a',
            fillColor: '#4ade80'
        },
        palta: {
            nombre: 'Palta',
            icono: '🥑',
            color: '#15803d',
            fillColor: '#86efac'
        },
        horticolas: {
            nombre: 'Hortícolas mixtas',
            icono: '🥬',
            color: '#0d9488',
            fillColor: '#5eead4'
        },
        zapallo: {
            nombre: 'Zapallo / Cucurbitáceas',
            icono: '🎃',
            color: '#d97706',
            fillColor: '#fbbf24'
        },
        citricos: {
            nombre: 'Cítricos',
            icono: '🍊',
            color: '#ca8a04',
            fillColor: '#fde047'
        },
        otro: {
            nombre: 'Otro cultivo',
            icono: '🌱',
            color: '#475569',
            fillColor: '#94a3b8'
        }
    };

    const CATALOGO_ZONAS_FLORALES = {
        flora_espontanea: {
            nombre: 'Flora espontánea nativa',
            icono: '🌿',
            color: '#7c3aed',
            fillColor: '#a78bfa'
        },
        borde_silvestre: {
            nombre: 'Borde / cerco con flores silvestres',
            icono: '🌸',
            color: '#9333ea',
            fillColor: '#c084fc'
        },
        banda_implantada: {
            nombre: 'Banda floral ya implantada',
            icono: '🌼',
            color: '#6d28d9',
            fillColor: '#8b5cf6'
        },
        monte_cortina: {
            nombre: 'Cortina forestal / vegetación natural',
            icono: '🌳',
            color: '#5b21b6',
            fillColor: '#a78bfa'
        },
        otro: {
            nombre: 'Otra vegetación benéfica',
            icono: '✨',
            color: '#7e22ce',
            fillColor: '#d8b4fe'
        }
    };

    const ECORREGIONES = [
        { id: 'valles_templados', nombre: 'Valles Templados' },
        { id: 'yungas', nombre: 'Yungas (Selva de Montaña)' },
        { id: 'quebrada', nombre: 'Quebrada' },
        { id: 'puna', nombre: 'Puna' },
        { id: 'chaco_seco', nombre: 'Chaco Seco' }
    ];

    // Los 16 departamentos de Jujuy con localidades principales, coordenadas y ecorregión sugerida
    const JUJUY_DEPARTAMENTOS = {
        'El Carmen': {
            ecorregion: 'valles_templados',
            localidades: [
                { nombre: 'Perico', lat: -24.3833, lng: -65.1167, zoom: 14 },
                { nombre: 'Monterrico', lat: -24.4397, lng: -65.1619, zoom: 14 },
                { nombre: 'El Carmen', lat: -24.3878, lng: -65.2603, zoom: 14 },
                { nombre: 'Pampa Blanca', lat: -24.5333, lng: -65.0667, zoom: 14 },
                { nombre: 'Aguas Calientes', lat: -24.5975, lng: -65.1583, zoom: 14 },
                { nombre: 'Puesto Viejo', lat: -24.4833, lng: -65.0167, zoom: 14 }
            ]
        },
        'Dr. Manuel Belgrano': {
            ecorregion: 'valles_templados',
            localidades: [
                { nombre: 'San Salvador de Jujuy', lat: -24.1858, lng: -65.2995, zoom: 13 },
                { nombre: 'Yala', lat: -24.1200, lng: -65.4050, zoom: 14 },
                { nombre: 'Lozano', lat: -24.0800, lng: -65.4100, zoom: 14 },
                { nombre: 'Reyes', lat: -24.1550, lng: -65.3750, zoom: 14 },
                { nombre: 'Guerrero', lat: -24.1900, lng: -65.4500, zoom: 14 }
            ]
        },
        'Palpalá': {
            ecorregion: 'valles_templados',
            localidades: [
                { nombre: 'Palpalá', lat: -24.2567, lng: -65.2116, zoom: 14 },
                { nombre: 'Río Blanco', lat: -24.2280, lng: -65.2350, zoom: 14 },
                { nombre: 'Forestal', lat: -24.3050, lng: -65.1800, zoom: 14 },
                { nombre: 'Carahunco', lat: -24.3167, lng: -65.1167, zoom: 14 }
            ]
        },
        'San Antonio': {
            ecorregion: 'valles_templados',
            localidades: [
                { nombre: 'San Antonio', lat: -24.3667, lng: -65.3333, zoom: 14 },
                { nombre: 'Los Alisos', lat: -24.2833, lng: -65.3000, zoom: 14 }
            ]
        },
        'San Pedro': {
            ecorregion: 'yungas',
            localidades: [
                { nombre: 'San Pedro de Jujuy', lat: -24.2314, lng: -64.8661, zoom: 14 },
                { nombre: 'La Esperanza', lat: -24.2250, lng: -64.8380, zoom: 14 },
                { nombre: 'La Mendieta', lat: -24.3167, lng: -64.9667, zoom: 14 },
                { nombre: 'Arrayanal', lat: -24.1667, lng: -64.8667, zoom: 14 },
                { nombre: 'Rodeíto', lat: -24.2833, lng: -64.7833, zoom: 14 }
            ]
        },
        'Ledesma': {
            ecorregion: 'yungas',
            localidades: [
                { nombre: 'Libertador Gral. San Martín', lat: -23.8064, lng: -64.7875, zoom: 14 },
                { nombre: 'Fraile Pintado', lat: -23.9408, lng: -64.7994, zoom: 14 },
                { nombre: 'Calilegua', lat: -23.7736, lng: -64.7697, zoom: 14 },
                { nombre: 'Yuto', lat: -23.6431, lng: -64.4719, zoom: 14 },
                { nombre: 'Caimancito', lat: -23.7417, lng: -64.5950, zoom: 14 }
            ]
        },
        'Santa Bárbara': {
            ecorregion: 'yungas',
            localidades: [
                { nombre: 'Palma Sola', lat: -23.9750, lng: -64.3033, zoom: 14 },
                { nombre: 'Santa Clara', lat: -24.3086, lng: -64.6617, zoom: 14 },
                { nombre: 'El Talar', lat: -23.5467, lng: -64.3550, zoom: 14 },
                { nombre: 'Vinalito', lat: -23.7583, lng: -64.4250, zoom: 14 }
            ]
        },
        'Tilcara': {
            ecorregion: 'quebrada',
            localidades: [
                { nombre: 'Tilcara', lat: -23.5776, lng: -65.3940, zoom: 14 },
                { nombre: 'Maimará', lat: -23.6236, lng: -65.4050, zoom: 14 },
                { nombre: 'Huacalera', lat: -23.4375, lng: -65.3514, zoom: 14 }
            ]
        },
        'Tumbaya': {
            ecorregion: 'quebrada',
            localidades: [
                { nombre: 'Volcán', lat: -23.9167, lng: -65.4667, zoom: 14 },
                { nombre: 'Tumbaya', lat: -23.8583, lng: -65.4667, zoom: 14 },
                { nombre: 'Purmamarca', lat: -23.7469, lng: -65.4994, zoom: 14 }
            ]
        },
        'Humahuaca': {
            ecorregion: 'quebrada',
            localidades: [
                { nombre: 'Humahuaca', lat: -23.2054, lng: -65.3505, zoom: 14 },
                { nombre: 'Uquía', lat: -23.3056, lng: -65.3592, zoom: 14 },
                { nombre: 'Tres Cruces', lat: -22.9186, lng: -65.5819, zoom: 14 }
            ]
        },
        'Valle Grande': {
            ecorregion: 'yungas',
            localidades: [
                { nombre: 'Valle Grande', lat: -23.4750, lng: -64.9500, zoom: 14 },
                { nombre: 'San Francisco', lat: -23.6214, lng: -64.9469, zoom: 14 },
                { nombre: 'Pampichuela', lat: -23.5431, lng: -65.0303, zoom: 14 }
            ]
        },
        'Cochinoca': {
            ecorregion: 'puna',
            localidades: [
                { nombre: 'Abra Pampa', lat: -22.7205, lng: -65.6970, zoom: 14 },
                { nombre: 'Abdón Castro Tolay', lat: -23.3683, lng: -66.0914, zoom: 14 }
            ]
        },
        'Yavi': {
            ecorregion: 'puna',
            localidades: [
                { nombre: 'La Quiaca', lat: -22.1024, lng: -65.5930, zoom: 14 },
                { nombre: 'Yavi', lat: -22.1306, lng: -65.4633, zoom: 14 }
            ]
        },
        'Susques': {
            ecorregion: 'puna',
            localidades: [
                { nombre: 'Susques', lat: -23.4000, lng: -66.3667, zoom: 14 }
            ]
        },
        'Rinconada': {
            ecorregion: 'puna',
            localidades: [
                { nombre: 'Rinconada', lat: -22.4408, lng: -66.1678, zoom: 14 }
            ]
        },
        'Santa Catalina': {
            ecorregion: 'puna',
            localidades: [
                { nombre: 'Santa Catalina', lat: -21.9461, lng: -66.0519, zoom: 14 }
            ]
        }
    };

    // Datos de demostración completos (Finca en Perico con 2 sectores de cultivo)
    const DEMO_TERRENO = {
        establecimiento: {
            nombre: 'Finca Los Lapachos',
            direccion: 'Ruta Provincial 47 km 4,5',
            departamento: 'El Carmen',
            localidad: 'Perico',
            ecorregion: 'valles_templados',
            ecorregion_nombre: 'Valles Templados'
        },
        parcela: {
            type: 'Feature',
            properties: { nombre: 'Finca Los Lapachos' },
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
        },
        sectores_demo: [
            {
                nombre: 'Lote Norte',
                cultivoKey: 'frutilla',
                geometry: {
                    type: 'Polygon',
                    coordinates: [[
                        [-65.1258, -24.3872],
                        [-65.1235, -24.3870],
                        [-65.1233, -24.3880],
                        [-65.12585, -24.3880],
                        [-65.1258, -24.3872]
                    ]]
                }
            },
            {
                nombre: 'Lote Sur',
                cultivoKey: 'tomate',
                geometry: {
                    type: 'Polygon',
                    coordinates: [[
                        [-65.12585, -24.3880],
                        [-65.1233, -24.3880],
                        [-65.1232, -24.3883],
                        [-65.1243, -24.3885],
                        [-65.1242, -24.3891],
                        [-65.1259, -24.3889],
                        [-65.12585, -24.3880]
                    ]]
                }
            }
        ],
        zonas_florales_demo: [
            {
                nombre: 'Borde Oeste con flora espontánea',
                tipoKey: 'flora_espontanea',
                especies: 'Hinojo, vicia y chilca silvestre',
                geometry: {
                    type: 'Polygon',
                    coordinates: [[
                        [-65.1259, -24.3872],
                        [-65.12562, -24.3872],
                        [-65.12568, -24.3889],
                        [-65.12592, -24.3889],
                        [-65.1259, -24.3872]
                    ]]
                }
            }
        ]
    };

    function formatearNumero(valor, decimales = 2) {
        return Number(valor || 0).toLocaleString('es-AR', {
            minimumFractionDigits: decimales,
            maximumFractionDigits: decimales
        });
    }

    function obtenerCookieCSRF(name = 'csrftoken') {
        const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
        return match ? decodeURIComponent(match[2]) : '';
    }

    function crearCapasBaseLeaflet() {
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

        return {
            predeterminada: capaHibrido,
            control: {
                '🛰️ Satélite + Etiquetas': capaHibrido,
                '🌍 Satélite puro': capaSatelite,
                '🗺️ Mapa de calles (OSM)': capaCalles
            }
        };
    }

    function obtenerNombreEcorregion(id) {
        const encontrada = ECORREGIONES.find((e) => e.id === id);
        return encontrada ? encontrada.nombre : id;
    }

    function poblarSelectCultivos(selectEl) {
        if (!selectEl) return;
        selectEl.innerHTML = '';
        Object.entries(CATALOGO_CULTIVOS).forEach(([key, info]) => {
            const opt = document.createElement('option');
            opt.value = key;
            opt.textContent = `${info.icono} ${info.nombre}`;
            selectEl.appendChild(opt);
        });
    }

    function poblarSelectZonasFlorales(selectEl) {
        if (!selectEl) return;
        selectEl.innerHTML = '';
        Object.entries(CATALOGO_ZONAS_FLORALES).forEach(([key, info]) => {
            const opt = document.createElement('option');
            opt.value = key;
            opt.textContent = `${info.icono} ${info.nombre}`;
            selectEl.appendChild(opt);
        });
    }

    function poblarSelectEcorregiones(selectEl) {
        if (!selectEl) return;
        selectEl.innerHTML = '';
        ECORREGIONES.forEach((eco) => {
            const opt = document.createElement('option');
            opt.value = eco.id;
            opt.textContent = eco.nombre;
            selectEl.appendChild(opt);
        });
    }

    global.PoliCampoCommon = {
        STORAGE_KEY_ENTRADA,
        STORAGE_KEY_SALIDA,
        CATALOGO_CULTIVOS,
        CATALOGO_ZONAS_FLORALES,
        ECORREGIONES,
        JUJUY_DEPARTAMENTOS,
        DEMO_TERRENO,
        formatearNumero,
        obtenerCookieCSRF,
        crearCapasBaseLeaflet,
        obtenerNombreEcorregion,
        poblarSelectCultivos,
        poblarSelectZonasFlorales,
        poblarSelectEcorregiones
    };
})(window);
