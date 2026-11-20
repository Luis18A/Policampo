import json
import math
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import (
    Establecimiento,
    Parcela,
    CroquisManual,
    COLORES_POLICAMPO,
    TipoUso,
    UbicacionRelativa,
    MetodoCaracterizacion,
    DepartamentoJujuy,
    Ecorregion,
    DisponibilidadAgua,
)
from .forms import EstablecimientoForm, ParcelaForm


# ─── Paleta centralizada de colores por tipo de uso ───────────────────────────
_COLORES_TIPO_USO = {
    'cultivo_agricola': '#2b8a3e',  # Verde fuerte
    'pastura':          '#fcc419',  # Amarillo
    'sin_cultivar':     '#94a3b8',  # Gris azulado
    'camino':           '#d4a76a',  # Marrón tierra
    'agua':             '#339af0',  # Celeste / Azul
    'construccion':     '#ff922b',  # Naranja
    'otro':             '#845ef7',  # Violeta
}


def _establecimiento_del_usuario(request, pk):
    """
    [Integración] Busca un establecimiento SOLO entre los del usuario que inició sesión.
    Si el pk existe pero es de otra persona, devuelve 404 (como si no existiera):
    así nadie puede ver ni modificar los datos de otro productor (Ley 25.326).
    """
    return get_object_or_404(Establecimiento, pk=pk, usuario=request.user)


def get_color_por_tipo_uso(tipo_uso, cultivo=''):
    """
    Devuelve el color predefinido para una parcela según su tipo_uso.
    """
    return _COLORES_TIPO_USO.get(tipo_uso, '#2b8a3e')


# ─── TAREA 5: Inferir ubicación relativa desde coordenadas canvas ─────────────
def inferir_ubicacion(x, y, w_canvas=840, h_canvas=500):
    """
    Infiere la ubicacion_relativa de una parcela a partir de su posición en el canvas.
    """
    col = 'izquierda' if x < w_canvas / 3 else ('derecha' if x > 2 * w_canvas / 3 else 'centro')
    fila = 'arriba' if y < h_canvas / 3 else ('abajo' if y > 2 * h_canvas / 3 else 'centro')
    if fila == 'centro' and col == 'centro':
        return 'centro'
    return f'{fila}_{col}'


@login_required
def pantalla_entrada(request):
    """
    Pantalla de bienvenida inicial (Módulo de Caracterización).
    Presenta las dos opciones principales:
    1. Registrar por superficies (cuestionario)
    2. Dibujar mi terreno (croquis manual)
    y el acceso geográfico complementario.
    """
    establecimientos = Establecimiento.objects.filter(usuario=request.user).order_by('-actualizado_en')
    ultimo_campo = establecimientos.first() if establecimientos.exists() else None

    context = {
        'total_establecimientos': establecimientos.count(),
        'ultimo_campo': ultimo_campo,
    }
    return render(request, 'campos/pantalla_entrada.html', context)


@login_required
def establecimientos_lista(request):
    """
    Listado de 'Mis Establecimientos' caracterizados.
    """
    establecimientos = Establecimiento.objects.filter(usuario=request.user).order_by('-actualizado_en')
    return render(request, 'campos/establecimientos_lista.html', {
        'establecimientos': establecimientos
    })


@login_required
def establecimiento_crear(request):
    """
    Registro inicial del establecimiento agrícola.
    Permite seleccionar el flujo: 'superficies' (cuestionario) o 'disenador' (croquis manual).
    """
    modo = request.GET.get('modo', 'superficies')

    if request.method == 'POST':
        form = EstablecimientoForm(request.POST)
        if form.is_valid():
            establecimiento = form.save(commit=False)
            establecimiento.usuario = request.user  # [Integración] dueño
            if modo == 'disenador':
                establecimiento.metodo_caracterizacion = MetodoCaracterizacion.CROQUIS_MANUAL
            else:
                establecimiento.metodo_caracterizacion = MetodoCaracterizacion.CUESTIONARIO
            establecimiento.save()

            # Inicializar registros complementarios
            CroquisManual.objects.get_or_create(
                establecimiento=establecimiento,
                defaults={
                    'perimetro_largo_m': establecimiento.largo_estimado_m or Decimal('100.00'),
                    'perimetro_ancho_m': establecimiento.ancho_estimado_m or Decimal('100.00'),
                }
            )

            messages.success(request, f'¡Establecimiento "{establecimiento.nombre}" registrado exitosamente!')

            if modo == 'disenador':
                return redirect('campos:croquis_manual', pk=establecimiento.pk)
            elif modo == 'mapa':
                # [Unificación] El mapa de Sol se reemplazó por el de Agus (app mapa)
                return redirect('mapa:delimitar_terreno', pk=establecimiento.pk)
            else:
                return redirect('campos:parcelas_cuestionario', pk=establecimiento.pk)
    else:
        form = EstablecimientoForm()

    return render(request, 'campos/establecimiento_form.html', {
        'form': form,
        'modo': modo,
        'titulo': 'Nuevo Establecimiento Agrícola',
        'subtitulo': 'Completá los datos básicos de tu campo para comenzar la caracterización.',
        'boton_texto': 'Guardar y continuar',
    })


@login_required
def establecimiento_editar(request, pk):
    """
    Edición de datos generales del establecimiento (incluida dirección).
    """
    establecimiento = _establecimiento_del_usuario(request, pk)

    if request.method == 'POST':
        form = EstablecimientoForm(request.POST, instance=establecimiento)
        if form.is_valid():
            form.save()
            messages.success(request, 'Datos del establecimiento actualizados correctamente.')
            return redirect('campos:establecimiento_detalle', pk=establecimiento.pk)
    else:
        form = EstablecimientoForm(instance=establecimiento)

    return render(request, 'campos/establecimiento_form.html', {
        'form': form,
        'establecimiento': establecimiento,
        'modo': 'editar',
        'titulo': f'Editar: {establecimiento.nombre}',
        'subtitulo': 'Modificá los datos generales del predio.',
        'boton_texto': 'Guardar cambios',
    })


@login_required
def establecimiento_detalle(request, pk):
    """
    Ficha central de un establecimiento con métricas y accesos a sus representaciones.
    """
    establecimiento = _establecimiento_del_usuario(request, pk)
    parcelas = establecimiento.parcelas.all()
    croquis_manual, _ = CroquisManual.objects.get_or_create(establecimiento=establecimiento)

    return render(request, 'campos/establecimiento_detalle.html', {
        'establecimiento': establecimiento,
        'parcelas': parcelas,
        'croquis_manual': croquis_manual,
        'superficie_total': establecimiento.superficie_total_ha,
        'superficie_distribuida': establecimiento.superficie_distribuida_ha,
        'superficie_restante': establecimiento.superficie_restante_ha,
        'porcentaje_utilizado': establecimiento.porcentaje_utilizado,
    })


@login_required
def parcelas_cuestionario(request, pk):
    """
    Opción A: Cuestionario de parcelas y cultivos por superficies.
    Permite registrar parcelas con superficies y ubicaciones relativas.
    Al finalizar, genera inmediatamente el croquis automático.
    """
    establecimiento = _establecimiento_del_usuario(request, pk)
    parcelas = establecimiento.parcelas.all()

    if request.method == 'POST':
        # Si el usuario presionó el botón de "Finalizar y generar croquis"
        if 'accion_finalizar' in request.POST:
            return redirect('campos:croquis_automatico', pk=establecimiento.pk)

        form = ParcelaForm(request.POST)
        if form.is_valid():
            parcela = form.save(commit=False)
            parcela.establecimiento = establecimiento
            parcela.origen = 'cuestionario'

            # Validar que no se supere la superficie total si se ingresó superficie
            if parcela.superficie_ha:
                nueva_distribuida = establecimiento.superficie_distribuida_ha + parcela.superficie_ha
                if nueva_distribuida > establecimiento.superficie_total_ha:
                    exceso = nueva_distribuida - establecimiento.superficie_total_ha
                    form.add_error(
                        'superficie_ha',
                        f'La superficie ingresada supera la superficie total del predio por {exceso:.4f} ha. '
                        f'Disponible actualmente: {establecimiento.superficie_restante_ha:.4f} ha.'
                    )
                else:
                    if not parcela.color_hex:
                        parcela.color_hex = get_color_por_tipo_uso(parcela.tipo_uso, parcela.cultivo)
                    parcela.save()

                    # Actualizar método en establecimiento si corresponde
                    if establecimiento.metodo_caracterizacion == MetodoCaracterizacion.CROQUIS_MANUAL:
                        establecimiento.metodo_caracterizacion = MetodoCaracterizacion.AMBOS
                        establecimiento.save(update_fields=['metodo_caracterizacion'])

                    messages.success(request, f'Parcela "{parcela.nombre}" agregada correctamente.')
                    
                    # Si el botón presionado fue "Guardar y generar croquis inmediato"
                    if 'guardar_y_ver_croquis' in request.POST:
                        return redirect('campos:croquis_automatico', pk=establecimiento.pk)

                    return redirect('campos:parcelas_cuestionario', pk=establecimiento.pk)
            else:
                parcela.save()
                messages.success(request, f'Parcela "{parcela.nombre}" agregada.')
                return redirect('campos:parcelas_cuestionario', pk=establecimiento.pk)
    else:
        form = ParcelaForm()

    context = {
        'establecimiento': establecimiento,
        'parcelas': parcelas,
        'form': form,
        'colores': COLORES_POLICAMPO,
        'superficie_total': establecimiento.superficie_total_ha,
        'superficie_distribuida': establecimiento.superficie_distribuida_ha,
        'superficie_restante': establecimiento.superficie_restante_ha,
        'porcentaje_utilizado': establecimiento.porcentaje_utilizado,
    }
    return render(request, 'campos/parcelas_cuestionario.html', context)


@login_required
def parcela_editar(request, pk, parcela_id):
    """
    Editar parcela existente.
    """
    establecimiento = _establecimiento_del_usuario(request, pk)
    parcela = get_object_or_404(Parcela, pk=parcela_id, establecimiento=establecimiento)

    if request.method == 'POST':
        form = ParcelaForm(request.POST, instance=parcela)
        if form.is_valid():
            nueva_superficie = form.cleaned_data.get('superficie_ha') or Decimal('0.0000')
            otras_parcelas_total = sum(
                (p.superficie_ha or Decimal('0.0000'))
                for p in establecimiento.parcelas.exclude(pk=parcela.pk)
            )
            nueva_distribuida = otras_parcelas_total + nueva_superficie

            if nueva_distribuida > establecimiento.superficie_total_ha:
                exceso = nueva_distribuida - establecimiento.superficie_total_ha
                disponible = max(Decimal('0.0000'), establecimiento.superficie_total_ha - otras_parcelas_total)
                form.add_error(
                    'superficie_ha',
                    f'La superficie modificada excede el total por {exceso:.4f} ha. '
                    f'Superficie máxima disponible: {disponible:.4f} ha.'
                )
            else:
                form.save()
                messages.success(request, f'Parcela "{parcela.nombre}" actualizada.')
                return redirect('campos:parcelas_cuestionario', pk=establecimiento.pk)
    else:
        form = ParcelaForm(instance=parcela)

    return render(request, 'campos/parcela_editar.html', {
        'establecimiento': establecimiento,
        'parcela': parcela,
        'form': form,
        'colores': COLORES_POLICAMPO,
    })


@login_required
@require_POST
def parcela_eliminar(request, pk, parcela_id):
    """
    Eliminar parcela.
    """
    establecimiento = _establecimiento_del_usuario(request, pk)
    parcela = get_object_or_404(Parcela, pk=parcela_id, establecimiento=establecimiento)
    nombre = parcela.nombre
    parcela.delete()
    messages.info(request, f'Parcela "{nombre}" eliminada.')
    return redirect('campos:parcelas_cuestionario', pk=establecimiento.pk)


@login_required
def croquis_automatico(request, pk):
    """
    Primera representación: Croquis Automático (No editable).
    Construye la representación gráfica basada en los datos del cuestionario.
    El productor comprueba si la representación coincide con la información que proporcionó.
    """
    establecimiento = _establecimiento_del_usuario(request, pk)
    parcelas = establecimiento.parcelas.all()

    cuadricula = {
        'arriba_izquierda': [],
        'arriba_centro': [],
        'arriba_derecha': [],
        'centro_izquierda': [],
        'centro': [],
        'centro_derecha': [],
        'abajo_izquierda': [],
        'abajo_centro': [],
        'abajo_derecha': [],
    }

    for p in parcelas:
        loc = p.ubicacion_relativa or 'centro'
        if loc in cuadricula:
            cuadricula[loc].append(p)
        else:
            cuadricula['centro'].append(p)

    # Definición geométrica de cuadrantes para SVG (viewBox 0 0 1000 700)
    cuadrantes_coords = {
        'arriba_izquierda': {'col': 0, 'fila': 0, 'nombre': 'ARRIBA A LA IZQUIERDA'},
        'arriba_centro':    {'col': 1, 'fila': 0, 'nombre': 'ARRIBA AL CENTRO'},
        'arriba_derecha':   {'col': 2, 'fila': 0, 'nombre': 'ARRIBA A LA DERECHA'},
        'centro_izquierda': {'col': 0, 'fila': 1, 'nombre': 'CENTRO A LA IZQUIERDA'},
        'centro':           {'col': 1, 'fila': 1, 'nombre': 'CENTRO'},
        'centro_derecha':   {'col': 2, 'fila': 1, 'nombre': 'CENTRO A LA DERECHA'},
        'abajo_izquierda':  {'col': 0, 'fila': 2, 'nombre': 'ABAJO A LA IZQUIERDA'},
        'abajo_centro':     {'col': 1, 'fila': 2, 'nombre': 'ABAJO AL CENTRO'},
        'abajo_derecha':    {'col': 2, 'fila': 2, 'nombre': 'ABAJO A LA DERECHA'},
    }

    origin_x = 55
    origin_y = 98
    cell_w = 260
    cell_h = 172
    gap = 12

    sectores_svg = []
    parcelas_svg = []

    for loc_key, items in cuadricula.items():
        c_info = cuadrantes_coords[loc_key]
        base_x = origin_x + c_info['col'] * (cell_w + gap)
        base_y = origin_y + c_info['fila'] * (cell_h + gap)

        sectores_svg.append({
            'x': int(base_x),
            'y': int(base_y),
            'w': int(cell_w),
            'h': int(cell_h),
            'tiene_parcelas': len(items) > 0,
            'nombre': c_info['nombre'],
            'label_x': int(round(base_x + cell_w / 2)),
            'label_y': int(round(base_y + cell_h / 2)),
        })

        if items:
            k = len(items)
            sub_h = (cell_h - 8 - (k - 1) * 6) / k
            for idx, p in enumerate(items):
                p_y = base_y + 4 + idx * (sub_h + 6)
                ha_val = float(p.superficie_ha) if p.superficie_ha is not None else 0.0
                ha_str = f"{ha_val:.2f} ha" if ha_val > 0 else "Sup. no esp."
                if p.cultivo and sub_h > 50:
                    sub_texto = f"{p.cultivo} ({ha_str})"
                else:
                    sub_texto = p.cultivo or ha_str

                bar_h = 44 if sub_h > 65 else 32

                # Respetar exactamente el color elegido por el usuario en el cuestionario,
                # o usar el color predefinido por tipo de uso si no se especificó ninguno.
                color_final = p.color_hex or get_color_por_tipo_uso(p.tipo_uso, p.cultivo or '')

                p_y_int = int(round(p_y))
                sub_h_int = int(round(sub_h))
                bar_h_int = int(min(sub_h_int, bar_h))

                parcelas_svg.append({
                    'id': p.pk,
                    'nombre': p.nombre,
                    'cultivo': p.cultivo or '',
                    'sub_texto': sub_texto,
                    'color': color_final,
                    'x': int(base_x + 4),
                    'y': p_y_int,
                    'w': int(cell_w - 8),
                    'h': sub_h_int,
                    'bar_y': p_y_int + max(0, sub_h_int - bar_h_int),
                    'bar_h': bar_h_int,
                    'text_nom_y': p_y_int + (sub_h_int - 24 if sub_h_int > 65 else sub_h_int - 16),
                    'text_sub_y': p_y_int + (sub_h_int - 10 if sub_h_int > 65 else sub_h_int - 4),
                    'font_size_nom': 13 if sub_h_int > 65 else 11,
                    'font_size_sub': 11 if sub_h_int > 65 else 9,
                })

    parcelas_list = []
    for p in parcelas:
        ha_float = float(p.superficie_ha) if p.superficie_ha is not None else 0.0
        m2_float = float(p.superficie_m2) if p.superficie_ha is not None else 0.0
        color_auto = get_color_por_tipo_uso(p.tipo_uso, p.cultivo or '')
        parcelas_list.append({
            'id': p.pk,
            'nombre': p.nombre,
            'cultivo': p.cultivo or '',
            'tipoUso': p.get_tipo_uso_display(),
            'ha': ha_float,
            'm2': m2_float,
            'ubicacion': p.ubicacion_relativa or 'centro',
            'color': p.color_hex or color_auto,
        })

    context = {
        'establecimiento': establecimiento,
        'parcelas': parcelas,
        'sectores_svg': sectores_svg,
        'parcelas_svg': parcelas_svg,
        'parcelas_json': json.dumps(parcelas_list),
        'superficie_total': establecimiento.superficie_total_ha,
        'superficie_distribuida': establecimiento.superficie_distribuida_ha,
        'superficie_restante': establecimiento.superficie_restante_ha,
        'porcentaje_utilizado': establecimiento.porcentaje_utilizado,
    }
    return render(request, 'campos/croquis_automatico.html', context)


@login_required
def croquis_manual(request, pk):
    """
    Opción B: Dibujar mi terreno (croquis manual).
    Editor intuitivo con clic y arrastre donde el productor dibuja libremente
    la distribución de sus terrenos y cultivos, sin escalas métricas inventadas.
    Las parcelas dibujadas se sincronizan directamente en la tabla Parcela.
    """
    establecimiento = _establecimiento_del_usuario(request, pk)
    croquis, _ = CroquisManual.objects.get_or_create(establecimiento=establecimiento)
    parcelas = establecimiento.parcelas.all()

    # Preparar datos de parcelas para el editor interactivo
    parcelas_list = []
    colores_disponibles = [c[0] for c in COLORES_POLICAMPO]

    for idx, p in enumerate(parcelas):
        # Si tiene geometría guardada la usamos, si no le asignamos una posición visual inicial
        geo = p.geometria_visual or {}
        x = geo.get('x', 50 + (idx % 3) * 220)
        y = geo.get('y', 50 + (idx // 3) * 160)
        w = geo.get('w', 180)
        h = geo.get('h', 130)

        parcelas_list.append({
            'id': p.pk,
            'nombre': p.nombre,
            'tipo_uso': p.tipo_uso,
            'cultivo': p.cultivo or '',
            'superficie_ha': float(p.superficie_ha) if p.superficie_ha is not None else None,
            'color': p.color_hex or colores_disponibles[idx % len(colores_disponibles)],
            'x': x,
            'y': y,
            'w': w,
            'h': h,
            'origen': p.origen,
        })

    # Calcular dimensiones reales del establecimiento en metros para la escala del lienzo
    sup_total_ha_float = float(establecimiento.superficie_total_ha or Decimal('1.0'))
    sup_total_m2_float = sup_total_ha_float * 10000.0
    lado_default = round(math.sqrt(sup_total_m2_float), 2)
    largo_total_m = float(establecimiento.largo_estimado_m) if establecimiento.largo_estimado_m else lado_default
    ancho_total_m = float(establecimiento.ancho_estimado_m) if establecimiento.ancho_estimado_m else lado_default

    context = {
        'establecimiento': establecimiento,
        'croquis': croquis,
        'colores': COLORES_POLICAMPO,
        'tipos_uso': TipoUso.choices,
        'parcelas_json': json.dumps(parcelas_list),
        'sup_total_ha_json': json.dumps(sup_total_ha_float),
        'largo_total_m_json': json.dumps(largo_total_m),
        'ancho_total_m_json': json.dumps(ancho_total_m),
        'superficie_total': establecimiento.superficie_total_ha,
        'superficie_distribuida': establecimiento.superficie_distribuida_ha,
        'superficie_restante': establecimiento.superficie_restante_ha,
    }
    return render(request, 'campos/croquis_manual.html', context)


@login_required
@require_POST
def croquis_manual_guardar(request, pk):
    """
    API endpoint para persistir el croquis manual.
    Sincroniza directamente las figuras dibujadas con registros de la tabla Parcela,
    garantizando que la información quede en la misma estructura unificada para Proceso.
    """
    establecimiento = _establecimiento_del_usuario(request, pk)

    try:
        data = json.loads(request.body.decode('utf-8'))
        parcelas_recibidas = data.get('parcelas', [])
        ids_recibidos = []

        for p_data in parcelas_recibidas:
            pid = p_data.get('id')
            nombre = p_data.get('nombre', 'Parcela').strip() or 'Parcela'
            tipo_uso = p_data.get('tipo_uso', 'cultivo_agricola')
            cultivo = p_data.get('cultivo', '').strip()
            sup_val = p_data.get('superficie_ha')
            superficie_ha = Decimal(str(sup_val)) if sup_val not in (None, '', 0) else None
            color = p_data.get('color', '#2b8a3e')
            geometria = {
                'x': float(p_data.get('x', 50)),
                'y': float(p_data.get('y', 50)),
                'w': float(p_data.get('w', 150)),
                'h': float(p_data.get('h', 100)),
            }

            centro_x = geometria['x'] + geometria['w'] / 2.0
            centro_y = geometria['y'] + geometria['h'] / 2.0
            ubi_rel = inferir_ubicacion(centro_x, centro_y)

            if pid and str(pid).isdigit():
                # Actualizar parcela existente
                try:
                    parcela = Parcela.objects.get(pk=int(pid), establecimiento=establecimiento)
                    parcela.nombre = nombre
                    parcela.tipo_uso = tipo_uso
                    parcela.cultivo = cultivo
                    parcela.superficie_ha = superficie_ha
                    parcela.color_hex = color
                    parcela.geometria_visual = geometria
                    parcela.origen = 'croquis_manual'
                    parcela.ubicacion_relativa = ubi_rel
                    parcela.save()
                    ids_recibidos.append(parcela.pk)
                except Parcela.DoesNotExist:
                    continue
            else:
                # Crear nueva parcela en la misma estructura común
                parcela = Parcela.objects.create(
                    establecimiento=establecimiento,
                    nombre=nombre,
                    tipo_uso=tipo_uso,
                    cultivo=cultivo,
                    superficie_ha=superficie_ha,
                    color_hex=color,
                    geometria_visual=geometria,
                    origen='croquis_manual',
                    ubicacion_relativa=ubi_rel,
                )
                ids_recibidos.append(parcela.pk)

        # Si alguna parcela manual fue borrada en el editor, eliminarla
        Parcela.objects.filter(
            establecimiento=establecimiento,
            origen='croquis_manual'
        ).exclude(pk__in=ids_recibidos).delete()

        # Actualizar método de caracterización
        if establecimiento.metodo_caracterizacion == MetodoCaracterizacion.CUESTIONARIO and Parcela.objects.filter(establecimiento=establecimiento, origen='cuestionario').exists():
            establecimiento.metodo_caracterizacion = MetodoCaracterizacion.AMBOS
        else:
            establecimiento.metodo_caracterizacion = MetodoCaracterizacion.CROQUIS_MANUAL
        establecimiento.save(update_fields=['metodo_caracterizacion'])

        return JsonResponse({
            'status': 'ok',
            'mensaje': 'Croquis y parcelas guardados exitosamente en la base de datos.',
            'total_parcelas': establecimiento.parcelas.count(),
            'superficie_distribuida_ha': float(establecimiento.superficie_distribuida_ha),
            'parcelas_ids': ids_recibidos,
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'mensaje': str(e)}, status=400)


@login_required
def proceso_datos_api(request, pk):
    """
    Endpoint de integración para el futuro módulo Proceso.
    Retorna la estructura de datos unificada de caracterización
    (establecimiento, parcelas, cultivos y superficies).
    """
    establecimiento = _establecimiento_del_usuario(request, pk)
    return JsonResponse(establecimiento.get_datos_para_proceso(), json_dumps_params={'indent': 2})
