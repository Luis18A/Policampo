/**
 * POLICAMPO - Editor de Croquis Manual Interactivo
 * Permite dibujar parcelas arrastrando con el mouse o dedo,
 * muestra medidas en metros en tiempo real y asigna colores
 * predefinidos según el tipo de uso (con opción de cambiar color).
 */

// ─── Paleta predefinida por Tipo de Uso ──────────────────────────────────────
const POLICAMPO_COLORES_TIPO_USO = {
    cultivo_agricola: '#2b8a3e', // Verde fuerte
    pastura:          '#fcc419', // Amarillo
    agua:             '#339af0', // Celeste / Azul
    construccion:     '#ff922b', // Naranja
    camino:           '#d4a76a', // Marrón tierra
    sin_cultivar:     '#94a3b8', // Gris azulado
    otro:             '#845ef7', // Violeta
};

function getColorPorTipoUso(tipoUso) {
    return POLICAMPO_COLORES_TIPO_USO[tipoUso] || '#2b8a3e';
}

window.POLICAMPO_COLORES_TIPO_USO = POLICAMPO_COLORES_TIPO_USO;
window.getColorPorTipoUso = getColorPorTipoUso;

// ─── Clase principal del editor ──────────────────────────────────────────────
class CroquisManualLibre {
    constructor(canvasId, options = {}) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            console.error(`Canvas no encontrado: "${canvasId}"`);
            return;
        }
        this.ctx = this.canvas.getContext('2d');
        this.options = options;

        // Resolución interna fija del canvas
        this.CANVAS_W = 860;
        this.CANVAS_H = 540;
        this.canvas.width = this.CANVAS_W;
        this.canvas.height = this.CANVAS_H;

        // Dimensiones reales del establecimiento en metros
        this.supTotalHa = parseFloat(options.supTotalHa) || 1;
        this.supTotalM2 = this.supTotalHa * 10000;
        const ladoDefault = Math.sqrt(this.supTotalM2);
        this.largoTotalM = parseFloat(options.largoTotalM) || ladoDefault;
        this.anchoTotalM = parseFloat(options.anchoTotalM) || ladoDefault;

        // Perímetro visual del terreno dentro del canvas
        this.mg = 38;
        this.peri = {
            x: this.mg,
            y: this.mg + 18,
            w: this.CANVAS_W - this.mg * 2,
            h: this.CANVAS_H - this.mg * 2 - 18
        };

        // Estado inicial
        this.parcelas = Array.isArray(options.parcelas) ? options.parcelas : [];
        // Calcular medidas en metros para parcelas cargadas que no tengan largo_m/ancho_m
        this.parcelas.forEach(p => {
            if (p.w && p.h && (p.largo_m === undefined || p.ancho_m === undefined)) {
                const m = this._pxToM(p.w, p.h);
                p.largo_m = m.largo;
                p.ancho_m = m.ancho;
                if (p.superficie_m2 === undefined) {
                    p.superficie_m2 = p.superficie_ha ? Math.round(p.superficie_ha * 10000 * 10) / 10 : m.m2;
                }
            }
        });

        this.selectedParcela = null;
        this.activeHandle = null;
        this.mode = 'draw'; // 'draw' (lápiz) | 'select' (mover/redimensionar)

        this.activeCrop = options.defaultCrop || 'Cultivo agrícola';
        this.activeTipoUso = options.defaultTipoUso || 'cultivo_agricola';
        this.activeColor = getColorPorTipoUso(this.activeTipoUso);

        // Interacción
        this.isDrawing = false;
        this.isDragging = false;
        this.isResizing = false;
        this.startX = 0;
        this.startY = 0;
        this.curX = 0;
        this.curY = 0;

        this._bindEvents();
        this.render();
        this.updateResumen();
    }

    setActiveCrop(cropName, tipoUso, colorOpcional) {
        this.activeCrop = (cropName || '').trim();
        this.activeTipoUso = tipoUso || this.inferirTipoUso(this.activeCrop);
        this.activeColor = colorOpcional || getColorPorTipoUso(this.activeTipoUso);
        this.setMode('draw');
    }

    setActiveColor(color) {
        if (!color) return;
        this.activeColor = color;
        if (this.selectedParcela) {
            this.selectedParcela.color = color;
            this.render();
        }
    }

    setMode(m) {
        this.mode = m;
        if (m === 'draw') {
            this.selectedParcela = null;
            if (this.options.onSelectParcela) this.options.onSelectParcela(null);
        }
        this._updateCursor(this.curX, this.curY);
        this.render();
    }

    // ── Eventos de Mouse y Touch ─────────────────────────────────────────────
    _bindEvents() {
        this.canvas.addEventListener('mousedown', (e) => {
            e.preventDefault();
            this._onDown(this._pos(e));
        });
        window.addEventListener('mousemove', (e) => {
            if (this.isDrawing || this.isDragging || this.isResizing) {
                this._onMove(this._pos(e));
            }
        });
        this.canvas.addEventListener('mousemove', (e) => {
            if (!this.isDrawing && !this.isDragging && !this.isResizing) {
                const p = this._pos(e);
                this.curX = p.x;
                this.curY = p.y;
                this._updateCursor(p.x, p.y);
            }
        });
        window.addEventListener('mouseup', () => this._onUp());

        // Soporte táctil
        this.canvas.addEventListener('touchstart', (e) => {
            if (e.touches.length === 1) {
                e.preventDefault();
                this._onDown(this._pos(e.touches[0]));
            }
        }, { passive: false });
        this.canvas.addEventListener('touchmove', (e) => {
            if (e.touches.length === 1) {
                e.preventDefault();
                this._onMove(this._pos(e.touches[0]));
            }
        }, { passive: false });
        window.addEventListener('touchend', () => this._onUp());
    }

    _pos(evt) {
        const r = this.canvas.getBoundingClientRect();
        const sx = this.CANVAS_W / (r.width || this.CANVAS_W);
        const sy = this.CANVAS_H / (r.height || this.CANVAS_H);
        let x = (evt.clientX - r.left) * sx;
        let y = (evt.clientY - r.top) * sy;
        x = Math.max(this.peri.x, Math.min(this.peri.x + this.peri.w, x));
        y = Math.max(this.peri.y, Math.min(this.peri.y + this.peri.h, y));
        return { x, y };
    }

    _onDown(pos) {
        this.startX = pos.x;
        this.startY = pos.y;
        this.curX = pos.x;
        this.curY = pos.y;

        // Modo LÁPIZ: siempre inicia un nuevo dibujo
        if (this.mode === 'draw') {
            this.selectedParcela = null;
            if (this.options.onSelectParcela) this.options.onSelectParcela(null);
            this.isDrawing = true;
            this.isDragging = false;
            this.isResizing = false;
            this.render();
            return;
        }

        // Modo SELECCIONAR: verificar tiradores primero
        if (this.selectedParcela) {
            const h = this._hitHandle(pos.x, pos.y, this.selectedParcela);
            if (h) {
                this.isResizing = true;
                this.activeHandle = h;
                const p = this.selectedParcela;
                p._ox = p.x; p._oy = p.y; p._ow = p.w; p._oh = p.h;
                return;
            }
        }

        const hit = this._hitTest(pos.x, pos.y);
        this.selectedParcela = hit;
        if (hit) {
            this.isDragging = true;
            hit._ox = hit.x;
            hit._oy = hit.y;
        }
        if (this.options.onSelectParcela) this.options.onSelectParcela(hit);
        this.render();
    }

    _onMove(pos) {
        this.curX = pos.x;
        this.curY = pos.y;
        this._updateCursor(pos.x, pos.y);

        if (this.isDrawing) {
            this.render();
            return;
        }

        if (this.isResizing && this.selectedParcela) {
            const dx = pos.x - this.startX;
            const dy = pos.y - this.startY;
            const p = this.selectedParcela;
            if (this.activeHandle === 'se') {
                p.w = Math.max(25, Math.min(this.peri.x + this.peri.w - p.x, p._ow + dx));
                p.h = Math.max(20, Math.min(this.peri.y + this.peri.h - p.y, p._oh + dy));
            } else if (this.activeHandle === 'sw') {
                const nw = Math.max(25, p._ow - dx);
                p.x = Math.max(this.peri.x, p._ox + (p._ow - nw));
                p.w = (p._ox + p._ow) - p.x;
                p.h = Math.max(20, Math.min(this.peri.y + this.peri.h - p.y, p._oh + dy));
            } else if (this.activeHandle === 'ne') {
                p.w = Math.max(25, Math.min(this.peri.x + this.peri.w - p.x, p._ow + dx));
                const nh = Math.max(20, p._oh - dy);
                p.y = Math.max(this.peri.y, p._oy + (p._oh - nh));
                p.h = (p._oy + p._oh) - p.y;
            } else if (this.activeHandle === 'nw') {
                const nw = Math.max(25, p._ow - dx);
                p.x = Math.max(this.peri.x, p._ox + (p._ow - nw));
                p.w = (p._ox + p._ow) - p.x;
                const nh = Math.max(20, p._oh - dy);
                p.y = Math.max(this.peri.y, p._oy + (p._oh - nh));
                p.h = (p._oy + p._oh) - p.y;
            }
            this._recalc(p);
            if (this.options.onSelectParcela) this.options.onSelectParcela(p);
            this.render();
            this.updateResumen();
            return;
        }

        if (this.isDragging && this.selectedParcela) {
            const p = this.selectedParcela;
            p.x = Math.max(this.peri.x, Math.min(this.peri.x + this.peri.w - p.w, p._ox + (pos.x - this.startX)));
            p.y = Math.max(this.peri.y, Math.min(this.peri.y + this.peri.h - p.h, p._oy + (pos.y - this.startY)));
            this.render();
        }
    }

    _onUp() {
        if (this.isDrawing) {
            const w = Math.abs(this.curX - this.startX);
            const h = Math.abs(this.curY - this.startY);
            const x = Math.min(this.startX, this.curX);
            const y = Math.min(this.startY, this.curY);

            if (w > 12 && h > 12) {
                const tipoUso = this.activeTipoUso || this.inferirTipoUso(this.activeCrop);
                const etiqueta = this.activeCrop || this._labelTipoUso(tipoUso);
                const cultivo = (tipoUso === 'cultivo_agricola' || tipoUso === 'pastura') ? etiqueta : '';
                const medidas = this._pxToM(w, h);

                const p = {
                    id: 'tmp_' + Date.now(),
                    nombre: `Sector ${this.parcelas.length + 1} (${etiqueta})`,
                    tipo_uso: tipoUso,
                    cultivo: cultivo,
                    color: this.activeColor,
                    superficie_ha: medidas.ha,
                    superficie_m2: medidas.m2,
                    largo_m: medidas.largo,
                    ancho_m: medidas.ancho,
                    x: Math.round(x),
                    y: Math.round(y),
                    w: Math.round(w),
                    h: Math.round(h),
                    origen: 'croquis_manual',
                };
                this.parcelas.push(p);
                this.selectedParcela = p;
                if (this.options.onSelectParcela) this.options.onSelectParcela(p);
            }

            this.isDrawing = false;
            this.render();
            this.updateResumen();

            const tip = document.getElementById('canvas-status-tip');
            if (tip) {
                tip.textContent = `✏️ Lápiz listo para dibujar: ${this.activeCrop || this._labelTipoUso(this.activeTipoUso)}`;
                tip.style.color = '#047857';
            }
            return;
        }

        this.isDragging = false;
        this.isResizing = false;
        this.activeHandle = null;
        this.render();
    }

    // ── Conversión píxeles → metros reales ───────────────────────────────────
    _pxToM(wPx, hPx) {
        const largo = (wPx / this.peri.w) * this.largoTotalM;
        const ancho = (hPx / this.peri.h) * this.anchoTotalM;
        const m2 = largo * ancho;
        return {
            largo: Math.round(largo * 10) / 10,
            ancho: Math.round(ancho * 10) / 10,
            m2: Math.round(m2 * 10) / 10,
            ha: Math.round((m2 / 10000) * 10000) / 10000,
        };
    }

    _recalc(p) {
        const m = this._pxToM(p.w, p.h);
        p.largo_m = m.largo;
        p.ancho_m = m.ancho;
        p.superficie_m2 = m.m2;
        p.superficie_ha = m.ha;
    }

    _hitTest(x, y) {
        for (let i = this.parcelas.length - 1; i >= 0; i--) {
            const p = this.parcelas[i];
            if (x >= p.x && x <= p.x + p.w && y >= p.y && y <= p.y + p.h) return p;
        }
        return null;
    }

    _hitHandle(x, y, p) {
        const hs = 12;
        const corners = [
            ['nw', p.x, p.y],
            ['ne', p.x + p.w, p.y],
            ['se', p.x + p.w, p.y + p.h],
            ['sw', p.x, p.y + p.h]
        ];
        for (const [n, hx, hy] of corners) {
            if (Math.abs(x - hx) <= hs && Math.abs(y - hy) <= hs) return n;
        }
        return null;
    }

    _updateCursor(x, y) {
        if (this.mode === 'draw') {
            this.canvas.style.cursor = 'crosshair';
            return;
        }
        if (this.selectedParcela) {
            const h = this._hitHandle(x, y, this.selectedParcela);
            if (h === 'nw' || h === 'se') { this.canvas.style.cursor = 'nwse-resize'; return; }
            if (h === 'ne' || h === 'sw') { this.canvas.style.cursor = 'nesw-resize'; return; }
        }
        this.canvas.style.cursor = this._hitTest(x, y) ? 'move' : 'default';
    }

    deleteSelected() {
        if (!this.selectedParcela) return;
        this.parcelas = this.parcelas.filter(p => p !== this.selectedParcela);
        this.selectedParcela = null;
        if (this.options.onSelectParcela) this.options.onSelectParcela(null);
        this.render();
        this.updateResumen();
    }

    updateResumen() {
        let totalHa = 0;
        let totalM2 = 0;
        this.parcelas.forEach(p => {
            totalHa += parseFloat(p.superficie_ha) || 0;
            totalM2 += parseFloat(p.superficie_m2) || ((parseFloat(p.superficie_ha) || 0) * 10000);
        });
        if (this.options.onResumenUpdate) {
            this.options.onResumenUpdate({
                totalParcelas: this.parcelas.length,
                superficieDeclaradaHa: totalHa,
                superficieOcupadaM2: totalM2,
            });
        }
    }

    inferirTipoUso(texto) {
        const c = (texto || '').toLowerCase();
        if (c.includes('acequia') || c.includes('agua') || c.includes('estanque') || c.includes('tanque') || c.includes('riego')) return 'agua';
        if (c.includes('pastura') || c.includes('alfalfa') || c.includes('pasto')) return 'pastura';
        if (c.includes('camino') || c.includes('calzada') || c.includes('sendero')) return 'camino';
        if (c.includes('casa') || c.includes('vivienda') || c.includes('galpon') || c.includes('galpón') || c.includes('corral') || c.includes('construccion') || c.includes('construcción')) return 'construccion';
        if (c.includes('sin cultivar') || c.includes('descanso') || c.includes('vacio') || c.includes('vacío')) return 'sin_cultivar';
        return 'cultivo_agricola';
    }

    _labelTipoUso(tipoUso) {
        const labels = {
            cultivo_agricola: 'Cultivo',
            pastura: 'Pastura',
            agua: 'Agua / Acequia',
            construccion: 'Construcción',
            camino: 'Camino',
            sin_cultivar: 'Sin cultivar',
            otro: 'Otro uso',
        };
        return labels[tipoUso] || 'Sector';
    }

    // ── RENDER ───────────────────────────────────────────────────────────────
    render() {
        const ctx = this.ctx;
        ctx.clearRect(0, 0, this.CANVAS_W, this.CANVAS_H);
        this._drawFondo();
        this._drawPerimetro();
        this.parcelas.forEach(p => this._drawParcela(p));

        // Previsualización en vivo mientras el usuario arrastra el lápiz
        if (this.isDrawing) {
            const rx = Math.min(this.startX, this.curX);
            const ry = Math.min(this.startY, this.curY);
            const rw = Math.abs(this.curX - this.startX);
            const rh = Math.abs(this.curY - this.startY);
            const m = this._pxToM(rw, rh);

            ctx.save();
            ctx.fillStyle = this.activeColor + '55';
            ctx.strokeStyle = this.activeColor;
            ctx.lineWidth = 2.5;
            ctx.setLineDash([6, 4]);
            ctx.fillRect(rx, ry, rw, rh);
            ctx.strokeRect(rx, ry, rw, rh);
            ctx.setLineDash([]);

            if (rw > 8 && rh > 8) {
                // Cotas en metros en los bordes superior e izquierdo
                this._drawDimLabel(ctx, rx + rw / 2, Math.max(this.peri.y + 10, ry - 10), `${m.largo} m`);
                this._drawDimLabel(ctx, Math.max(this.peri.x + 28, rx - 24), ry + rh / 2, `${m.ancho} m`);

                // Etiqueta flotante con superficie en m² y ha
                const nombreVivo = this.activeCrop || this._labelTipoUso(this.activeTipoUso);
                const label = `📐 ${nombreVivo}: ${m.largo}m × ${m.ancho}m (${m.m2.toLocaleString('es-AR')} m² · ${m.ha} ha)`;
                ctx.font = 'bold 13px sans-serif';
                const tw = ctx.measureText(label).width + 18;
                const boxH = 26;
                const lx = Math.max(8, Math.min(rx, this.CANVAS_W - tw - 8));
                const ly = ry > this.peri.y + 34 ? ry - boxH - 18 : Math.min(this.CANVAS_H - boxH - 6, ry + rh + 8);

                ctx.fillStyle = this.activeColor;
                this._roundRect(ctx, lx, ly, tw, boxH, 6);
                ctx.fill();
                ctx.fillStyle = '#ffffff';
                ctx.textAlign = 'left';
                ctx.textBaseline = 'middle';
                ctx.fillText(label, lx + 9, ly + boxH / 2);

                // Actualizar barra superior del lienzo en tiempo real
                const tip = document.getElementById('canvas-status-tip');
                if (tip) {
                    tip.textContent = `📐 Dibujando ${nombreVivo}: ${m.largo}m × ${m.ancho}m = ${m.m2.toLocaleString('es-AR')} m² (${m.ha} ha)`;
                    tip.style.color = this.activeColor;
                }
            }
            ctx.restore();
        }

        this._drawNorte();
    }

    _drawDimLabel(ctx, x, y, text) {
        ctx.save();
        ctx.font = 'bold 11px sans-serif';
        const tw = ctx.measureText(text).width + 10;
        ctx.fillStyle = 'rgba(255, 255, 255, 0.92)';
        ctx.strokeStyle = '#94a3b8';
        ctx.lineWidth = 1;
        ctx.fillRect(x - tw / 2, y - 9, tw, 18);
        ctx.strokeRect(x - tw / 2, y - 9, tw, 18);
        ctx.fillStyle = '#0f172a';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(text, x, y);
        ctx.restore();
    }

    _roundRect(ctx, x, y, w, h, r) {
        ctx.beginPath();
        if (ctx.roundRect) {
            ctx.roundRect(x, y, w, h, r);
        } else {
            ctx.moveTo(x + r, y);
            ctx.lineTo(x + w - r, y);
            ctx.arcTo(x + w, y, x + w, y + r, r);
            ctx.lineTo(x + w, y + h - r);
            ctx.arcTo(x + w, y + h, x + w - r, y + h, r);
            ctx.lineTo(x + r, y + h);
            ctx.arcTo(x, y + h, x, y + h - r, r);
            ctx.lineTo(x, y + r);
            ctx.arcTo(x, y, x + r, y, r);
            ctx.closePath();
        }
    }

    _drawFondo() {
        const ctx = this.ctx;
        ctx.save();
        ctx.fillStyle = '#f8fafc';
        ctx.fillRect(0, 0, this.CANVAS_W, this.CANVAS_H);
        ctx.strokeStyle = '#e2e8f0';
        ctx.lineWidth = 0.7;
        for (let x = 0; x <= this.CANVAS_W; x += 25) {
            ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, this.CANVAS_H); ctx.stroke();
        }
        for (let y = 0; y <= this.CANVAS_H; y += 25) {
            ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(this.CANVAS_W, y); ctx.stroke();
        }
        ctx.restore();
    }

    _drawPerimetro() {
        const ctx = this.ctx;
        const p = this.peri;
        ctx.save();
        ctx.fillStyle = '#f0fdf4';
        ctx.fillRect(p.x, p.y, p.w, p.h);
        ctx.strokeStyle = '#14532d';
        ctx.lineWidth = 2.5;
        ctx.setLineDash([10, 5]);
        ctx.strokeRect(p.x, p.y, p.w, p.h);
        ctx.setLineDash([]);

        ctx.fillStyle = '#14532d';
        ctx.font = 'bold 12px sans-serif';
        ctx.textAlign = 'left';
        ctx.textBaseline = 'alphabetic';
        ctx.fillText(
            `PERÍMETRO DEL TERRENO: ${this.largoTotalM.toFixed(1)} m × ${this.anchoTotalM.toFixed(1)} m · Total: ${this.supTotalHa.toFixed(2)} ha (${Math.round(this.supTotalM2).toLocaleString('es-AR')} m²)`,
            p.x + 6,
            p.y - 10
        );
        ctx.restore();
    }

    _drawParcela(p) {
        const ctx = this.ctx;
        const isSel = this.selectedParcela === p;
        ctx.save();

        ctx.shadowColor = 'rgba(0,0,0,0.16)';
        ctx.shadowBlur = 6;
        ctx.shadowOffsetY = 3;
        ctx.fillStyle = p.color || getColorPorTipoUso(p.tipo_uso);
        ctx.fillRect(p.x, p.y, p.w, p.h);
        ctx.shadowColor = 'transparent';

        ctx.strokeStyle = isSel ? '#0f172a' : '#ffffff';
        ctx.lineWidth = isSel ? 3 : 2;
        ctx.strokeRect(p.x, p.y, p.w, p.h);

        if (p.h >= 30 && p.w >= 48) {
            const barH = Math.min(p.h, 42);
            ctx.fillStyle = 'rgba(0, 0, 0, 0.55)';
            ctx.fillRect(p.x, p.y + p.h - barH, p.w, barH);

            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 12px sans-serif';
            ctx.textAlign = 'left';
            ctx.textBaseline = 'alphabetic';
            const titulo = p.cultivo || p.nombre;
            ctx.fillText(titulo.length > 22 ? titulo.slice(0, 20) + '…' : titulo, p.x + 6, p.y + p.h - barH + 15);

            if (barH >= 28) {
                ctx.font = '10.5px sans-serif';
                ctx.fillStyle = '#e2e8f0';
                const med = p.largo_m
                    ? `${p.largo_m}m × ${p.ancho_m}m · ${parseFloat(p.superficie_ha || 0).toFixed(2)} ha`
                    : `${parseFloat(p.superficie_ha || 0).toFixed(2)} ha`;
                ctx.fillText(med, p.x + 6, p.y + p.h - barH + 32);
            }
        }

        if (isSel) {
            const hs = 9;
            [
                [p.x, p.y],
                [p.x + p.w, p.y],
                [p.x + p.w, p.y + p.h],
                [p.x, p.y + p.h]
            ].forEach(([hx, hy]) => {
                ctx.fillStyle = '#0f172a';
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 1.5;
                ctx.fillRect(hx - hs / 2, hy - hs / 2, hs, hs);
                ctx.strokeRect(hx - hs / 2, hy - hs / 2, hs, hs);
            });
        }
        ctx.restore();
    }

    _drawNorte() {
        const ctx = this.ctx;
        const x = this.CANVAS_W - 22;
        const y = 24;
        ctx.save();
        ctx.beginPath();
        ctx.arc(x, y, 15, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff';
        ctx.strokeStyle = '#14532d';
        ctx.lineWidth = 1.5;
        ctx.fill();
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(x, y - 10);
        ctx.lineTo(x + 4, y + 4);
        ctx.lineTo(x, y);
        ctx.lineTo(x - 4, y + 4);
        ctx.closePath();
        ctx.fillStyle = '#dc2626';
        ctx.fill();

        ctx.fillStyle = '#14532d';
        ctx.font = 'bold 10px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'alphabetic';
        ctx.fillText('N', x, y + 13);
        ctx.restore();
    }
}

window.CroquisManualLibre = CroquisManualLibre;
