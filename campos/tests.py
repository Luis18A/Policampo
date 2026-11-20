import json
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from .models import (
    Establecimiento,
    Parcela,
    CroquisManual,
    DepartamentoJujuy,
    Ecorregion,
    DisponibilidadAgua,
    TipoUso,
    UbicacionRelativa,
    MetodoCaracterizacion,
    COLORES_POLICAMPO,
)


CONTRASENA = "Quebrada-Huma2024"


def crear_usuario(nombre):
    """[Integración] Los establecimientos ahora tienen dueño: los tests necesitan un usuario."""
    return get_user_model().objects.create_user(nombre, f"{nombre}@mail.com", CONTRASENA)


class PoliCampoModelosTests(TestCase):
    def setUp(self):
        self.establecimiento = Establecimiento.objects.create(
            usuario=crear_usuario("sol"),
            nombre="Finca Flor de Maíz",
            direccion="Ruta Nacional 9 Km 1772",
            departamento=DepartamentoJujuy.TILCARA,
            localidad="Maimará",
            ecorregion=Ecorregion.QUEBRADA,
            superficie_total_ha=Decimal('2.5000'),
            disponibilidad_agua=DisponibilidadAgua.ACEQUIA,
            cultivo_principal="Maíz morado andino",
        )

    def test_calculo_superficie_m2(self):
        # 2.5 ha = 25.000 m²
        self.assertEqual(self.establecimiento.superficie_total_m2, Decimal('25000.0000'))

    def test_distribucion_parcelas_cuestionario(self):
        p1 = Parcela.objects.create(
            establecimiento=self.establecimiento,
            nombre="Tablón Alto",
            tipo_uso=TipoUso.CULTIVO,
            cultivo="Maíz morado",
            superficie_ha=Decimal('1.0000'),
            ubicacion_relativa=UbicacionRelativa.ARRIBA_IZQUIERDA,
            color_hex='#2b8a3e',
            origen='cuestionario'
        )
        p2 = Parcela.objects.create(
            establecimiento=self.establecimiento,
            nombre="Huerta familiar",
            tipo_uso=TipoUso.CULTIVO,
            cultivo="Hortalizas agroecológicas",
            superficie_ha=Decimal('0.7500'),
            ubicacion_relativa=UbicacionRelativa.CENTRO,
            color_hex='#339af0',
            origen='cuestionario'
        )

        self.assertEqual(self.establecimiento.superficie_distribuida_ha, Decimal('1.7500'))
        self.assertEqual(self.establecimiento.superficie_restante_ha, Decimal('0.7500'))
        self.assertEqual(self.establecimiento.porcentaje_utilizado, 70.0)

    def test_estructura_unificada_para_modulo_proceso(self):
        # Crear una parcela desde cuestionario y otra desde croquis manual
        Parcela.objects.create(
            establecimiento=self.establecimiento,
            nombre="Sector Maíz",
            tipo_uso=TipoUso.CULTIVO,
            cultivo="Maíz morado",
            superficie_ha=Decimal('1.2000'),
            origen='cuestionario'
        )
        Parcela.objects.create(
            establecimiento=self.establecimiento,
            nombre="Sector Huerta Dibujada",
            tipo_uso=TipoUso.CULTIVO,
            cultivo="Acelga y lechuga",
            superficie_ha=Decimal('0.5000'),
            origen='croquis_manual',
            geometria_visual={'x': 100, 'y': 120, 'w': 200, 'h': 150}
        )

        datos = self.establecimiento.get_datos_para_proceso()

        # Comprobar estructura común requerida para el módulo Proceso
        self.assertEqual(datos['establecimiento_id'], self.establecimiento.pk)
        self.assertEqual(datos['nombre'], "Finca Flor de Maíz")
        self.assertEqual(datos['direccion'], "Ruta Nacional 9 Km 1772")
        self.assertEqual(datos['total_parcelas'], 2)
        self.assertEqual(datos['superficie_distribuida_ha'], 1.7)
        self.assertEqual(len(datos['parcelas']), 2)

        cultivos = [p['cultivo'] for p in datos['parcelas']]
        self.assertIn("Maíz morado", cultivos)
        self.assertIn("Acelga y lechuga", cultivos)

    def test_colores_oficiales_policampo(self):
        self.assertEqual(len(COLORES_POLICAMPO), 8)
        colores_hex = [c[0] for c in COLORES_POLICAMPO]
        self.assertIn('#2b8a3e', colores_hex)
        self.assertIn('#339af0', colores_hex)
        self.assertIn('#ff922b', colores_hex)
        self.assertIn('#fcc419', colores_hex)
        self.assertIn('#e64980', colores_hex)
        self.assertIn('#cc5de8', colores_hex)
        self.assertIn('#845ef7', colores_hex)
        self.assertIn('#20c997', colores_hex)


class PoliCampoVistasTests(TestCase):
    def setUp(self):
        self.client = Client()
        # [Integración] Las vistas ahora piden iniciar sesión
        self.usuario = crear_usuario("sol")
        self.client.login(username="sol", password=CONTRASENA)
        self.establecimiento = Establecimiento.objects.create(
            usuario=self.usuario,
            nombre="Chacra La Huerta",
            direccion="Camino Comunal s/n",
            departamento=DepartamentoJujuy.HUMAHUACA,
            localidad="Uquía",
            ecorregion=Ecorregion.QUEBRADA,
            superficie_total_ha=Decimal('3.0000'),
            disponibilidad_agua=DisponibilidadAgua.RIO,
            cultivo_principal="Papas andinas y habas",
        )

    def test_pantalla_entrada_carga_correctamente(self):
        res = self.client.get(reverse('campos:pantalla_entrada'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Comencemos a conocer tu campo 🌱')
        self.assertContains(res, 'Registrar por superficies')
        self.assertContains(res, 'Dibujar mi terreno')

    def test_creacion_establecimiento_con_direccion(self):
        data = {
            'nombre': 'Finca Los Valles',
            'direccion': 'Ruta Provincial 42',
            'departamento': 'El Carmen',
            'localidad': 'Perico',
            'ecorregion': 'Valles Templados',
            'superficie_total_ha': '5.0',
        }
        res = self.client.post(reverse('campos:establecimiento_crear'), data)
        self.assertEqual(res.status_code, 302)
        finca = Establecimiento.objects.get(nombre='Finca Los Valles')
        self.assertEqual(finca.direccion, 'Ruta Provincial 42')
        self.assertEqual(finca.usuario, self.usuario)  # [Integración] queda a nombre de quien lo crea
        self.assertEqual(finca.cultivo_principal, '')  # [Unificación] el cuestionario no lo pide

    def test_guardar_parcela_y_ver_croquis_inmediato(self):
        data = {
            'tipo_uso': 'cultivo_agricola',
            'cultivo': 'Maíz',
            'superficie_ha': '1.0000',
            'ubicacion_relativa': 'centro',
            'guardar_y_ver_croquis': '1'
        }
        url = reverse('campos:parcelas_cuestionario', kwargs={'pk': self.establecimiento.pk})
        res = self.client.post(url, data)
        # Debe redirigir de inmediato al croquis automático
        self.assertEqual(res.status_code, 302)
        self.assertIn(reverse('campos:croquis_automatico', kwargs={'pk': self.establecimiento.pk}), res.url)

    def test_croquis_manual_sincroniza_con_modelo_parcela(self):
        # Cuando el productor dibuja en el croquis manual, debe crear filas en la tabla Parcela
        # [Unificación] Solo una finca cargada por croquis se puede guardar desde el croquis
        self.establecimiento.metodo_caracterizacion = MetodoCaracterizacion.CROQUIS_MANUAL
        self.establecimiento.save()
        url = reverse('campos:croquis_manual_guardar', kwargs={'pk': self.establecimiento.pk})
        payload = {
            'parcelas': [
                {
                    'id': 'new_101',
                    'nombre': 'Cuadro Dibujado 1',
                    'tipo_uso': 'cultivo_agricola',
                    'cultivo': 'Habas andinas',
                    'superficie_ha': 0.8,
                    'color': '#ff922b',
                    'x': 60,
                    'y': 60,
                    'w': 180,
                    'h': 130
                },
                {
                    'id': 'new_102',
                    'nombre': 'Sector Huerta Sin Ha Conocida',
                    'tipo_uso': 'sector_flores',
                    'cultivo': 'Alfalfa',  # [Unificación] se descarta: un sector de flores no lleva cultivo
                    'superficie_ha': None,
                    'color': '#20c997',
                    'x': 260,
                    'y': 60,
                    'w': 140,
                    'h': 100
                }
            ]
        }
        res = self.client.post(url, json.dumps(payload), content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # Comprobar que en la base de datos se crearon 2 parcelas reales
        parcelas_db = Parcela.objects.filter(establecimiento=self.establecimiento)
        self.assertEqual(parcelas_db.count(), 2)
        # [Unificación] El nombre y el color los asigna el servidor, no el dibujo
        p1 = parcelas_db.get(nombre='Habas andinas')
        self.assertEqual(p1.cultivo, 'Habas andinas')
        self.assertEqual(p1.color_hex, '#2b8a3e')
        self.assertEqual(p1.superficie_ha, Decimal('0.8000'))
        self.assertEqual(p1.origen, 'croquis_manual')
        self.assertIn('x', p1.geometria_visual)
        flores = parcelas_db.get(tipo_uso='sector_flores')
        self.assertEqual(flores.nombre, 'Sector de flores 1')
        self.assertEqual(flores.cultivo, '')
        self.assertEqual(flores.color_hex, '#e64980')

    def test_endpoint_api_proceso_retorna_json_valido(self):
        # Crear parcela
        Parcela.objects.create(
            establecimiento=self.establecimiento,
            nombre="Parcela Test",
            tipo_uso=TipoUso.CULTIVO,
            cultivo="Quinoa",
            superficie_ha=Decimal('0.5'),
            origen='croquis_manual'
        )

        url = reverse('campos:proceso_datos_api', kwargs={'pk': self.establecimiento.pk})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['nombre'], self.establecimiento.nombre)
        self.assertEqual(len(data['parcelas']), 1)
        self.assertEqual(data['parcelas'][0]['cultivo'], "Quinoa")


class SeguridadYPrivacidadTests(TestCase):
    """
    [Integración] Cada usuario ve y modifica SOLO sus establecimientos (Ley 25.326).
    Si alguien prueba con el número (pk) del establecimiento de otro, recibe 404.
    """

    def setUp(self):
        self.ana = crear_usuario("ana")
        self.beto = crear_usuario("beto")
        self.finca_de_ana = Establecimiento.objects.create(
            usuario=self.ana,
            nombre="Finca de Ana",
            localidad="Perico",
            superficie_total_ha=Decimal('2.0000'),
            cultivo_principal="Frutilla",
        )

    def test_sin_sesion_redirige_al_login(self):
        for url in (reverse('campos:pantalla_entrada'),
                    reverse('campos:establecimientos_lista'),
                    reverse('campos:establecimiento_detalle', kwargs={'pk': self.finca_de_ana.pk})):
            res = self.client.get(url)
            self.assertRedirects(res, f"{reverse('usuarios:login')}?next={url}")

    def test_la_lista_muestra_solo_los_propios(self):
        self.client.login(username="beto", password=CONTRASENA)
        res = self.client.get(reverse('campos:establecimientos_lista'))
        self.assertNotContains(res, "Finca de Ana")

    def test_no_se_puede_ver_ni_modificar_lo_de_otro_usuario(self):
        self.client.login(username="beto", password=CONTRASENA)
        pk = self.finca_de_ana.pk
        for nombre in ('establecimiento_detalle', 'establecimiento_editar', 'parcelas_cuestionario',
                       'croquis_automatico', 'croquis_manual', 'proceso_datos_api'):
            res = self.client.get(reverse(f'campos:{nombre}', kwargs={'pk': pk}))
            self.assertEqual(res.status_code, 404, nombre)

        # Tampoco puede guardar un croquis sobre la finca de Ana
        res = self.client.post(reverse('campos:croquis_manual_guardar', kwargs={'pk': pk}),
                               json.dumps({'parcelas': [{'id': 'new_1', 'nombre': 'Intruso'}]}),
                               content_type='application/json')
        self.assertEqual(res.status_code, 404)
        self.assertFalse(Parcela.objects.filter(nombre='Intruso').exists())

    def test_login_lleva_a_la_pantalla_de_entrada(self):
        res = self.client.post(reverse('usuarios:login'), {'username': 'ana', 'password': CONTRASENA})
        self.assertRedirects(res, reverse('campos:pantalla_entrada'))


class DatosDeEntradaSegunEsquemaTests(TestCase):
    """
    [Unificación] Cada forma de carga pide solo los datos del esquema del grupo:
    - Cuestionario: nombre, dirección, departamento, localidad, ecorregión, superficie total;
      por sector: tipo (cultivo o flores), cultivo, superficie y ubicación.
    - Croquis: lo mismo más el cultivo principal; por sector: tipo y cultivo.
    """

    def setUp(self):
        self.usuario = crear_usuario("ana")
        self.client.login(username="ana", password=CONTRASENA)
        self.finca = Establecimiento.objects.create(
            usuario=self.usuario, nombre="Finca de Ana", localidad="Perico",
            superficie_total_ha=Decimal('2.5'),
        )

    def campos_del_formulario(self, url):
        return set(self.client.get(url).context['form'].fields)

    def test_el_alta_pide_solo_los_datos_basicos_en_los_tres_modos(self):
        # Sin cultivo principal, agua ni largo/ancho
        basicos = {'nombre', 'direccion', 'departamento', 'localidad', 'ecorregion', 'superficie_total_ha'}
        for modo in ('superficies', 'disenador', 'mapa'):
            url = reverse('campos:establecimiento_crear') + f'?modo={modo}'
            self.assertEqual(self.campos_del_formulario(url), basicos, modo)

    def test_alta_por_croquis_sin_cultivo_principal(self):
        url = reverse('campos:establecimiento_crear') + '?modo=disenador'
        res = self.client.post(url, {
            'nombre': 'Finca Croquis', 'departamento': 'Palpalá', 'localidad': 'Palpalá',
            'ecorregion': 'Valles Templados', 'superficie_total_ha': '1',
        })
        finca = Establecimiento.objects.get(nombre='Finca Croquis')
        self.assertRedirects(res, reverse('campos:croquis_manual', kwargs={'pk': finca.pk}))
        self.assertNotContains(self.client.get(url), 'Cultivo principal')

    def test_sector_del_cuestionario_solo_pide_los_datos_del_esquema(self):
        url = reverse('campos:parcelas_cuestionario', kwargs={'pk': self.finca.pk})
        form = self.client.get(url).context['form']
        self.assertEqual(set(form.fields), {'tipo_uso', 'cultivo', 'superficie_ha', 'ubicacion_relativa'})
        self.assertEqual([v for v, _ in form.fields['tipo_uso'].choices], ['cultivo_agricola', 'sector_flores'])

    def test_sectores_de_flores_se_numeran_y_no_llevan_cultivo(self):
        url = reverse('campos:parcelas_cuestionario', kwargs={'pk': self.finca.pk})
        for _ in range(2):
            self.client.post(url, {'tipo_uso': 'sector_flores', 'cultivo': 'Papa',
                                   'superficie_ha': '0.5', 'ubicacion_relativa': 'centro'})
        nombres = list(self.finca.parcelas.values_list('nombre', 'cultivo'))
        self.assertEqual(nombres, [('Sector de flores 1', ''), ('Sector de flores 2', '')])

    def test_un_cultivo_necesita_nombre_y_toma_ese_nombre(self):
        url = reverse('campos:parcelas_cuestionario', kwargs={'pk': self.finca.pk})
        res = self.client.post(url, {'tipo_uso': 'cultivo_agricola', 'cultivo': '',
                                     'superficie_ha': '0.5', 'ubicacion_relativa': 'centro'})
        self.assertEqual(res.status_code, 200)
        self.assertFalse(self.finca.parcelas.exists())
        self.client.post(url, {'tipo_uso': 'cultivo_agricola', 'cultivo': 'Frutilla',
                               'superficie_ha': '0.5', 'ubicacion_relativa': 'arriba_izquierda'})
        self.assertEqual(self.finca.parcelas.get().nombre, 'Frutilla')

    def test_no_se_pueden_cargar_otros_tipos_de_sector(self):
        url = reverse('campos:parcelas_cuestionario', kwargs={'pk': self.finca.pk})
        res = self.client.post(url, {'tipo_uso': 'camino', 'cultivo': '',
                                     'superficie_ha': '0.5', 'ubicacion_relativa': 'centro'})
        self.assertEqual(res.status_code, 200)
        self.assertFalse(self.finca.parcelas.exists())

    def finca_de_croquis(self):
        """Una finca cargada por croquis (las de setUp son de cuestionario)."""
        return Establecimiento.objects.create(
            usuario=self.usuario, nombre="Finca croquis", localidad="Perico",
            superficie_total_ha=Decimal('2.5'), metodo_caracterizacion=MetodoCaracterizacion.CROQUIS_MANUAL,
        )

    def test_el_croquis_solo_ofrece_cultivo_y_flores_y_escala_por_superficie(self):
        res = self.client.get(reverse('campos:croquis_manual', kwargs={'pk': self.finca_de_croquis().pk}))
        self.assertEqual([v for v, _ in res.context['tipos_uso']], ['cultivo_agricola', 'sector_flores'])
        self.assertNotContains(res, 'id="prop-nombre"')
        self.assertNotContains(res, 'id="prop-superficie"')
        # 2,5 ha = 25.000 m2 -> cuadrado de 158,11 m de lado
        self.assertEqual(res.context['largo_total_m_json'], '158.11')

    def test_cuestionario_y_croquis_terminan_con_solicitar_diagnostico(self):
        # [Unificación] Botón final, deshabilitado hasta que exista el módulo de diagnóstico
        for nombre, finca in (('parcelas_cuestionario', self.finca), ('croquis_manual', self.finca_de_croquis())):
            res = self.client.get(reverse(f'campos:{nombre}', kwargs={'pk': finca.pk}))
            self.assertContains(res, 'Solicitar diagnóstico', msg_prefix=nombre)
            self.assertContains(res, 'class="btn btn-diagnostico" disabled', msg_prefix=nombre)
        # En las demás pantallas no aparece
        res = self.client.get(reverse('campos:establecimiento_detalle', kwargs={'pk': self.finca.pk}))
        self.assertNotContains(res, 'Solicitar diagnóstico')


class UnMetodoPorFincaTests(TestCase):
    """[Unificación] Cada finca se carga con un método y solo se edita con ese mismo."""

    def setUp(self):
        self.usuario = crear_usuario("ana")
        self.client.login(username="ana", password=CONTRASENA)
        self.fincas = {
            metodo: Establecimiento.objects.create(
                usuario=self.usuario, nombre=f"Finca {metodo}", localidad="Perico",
                superficie_total_ha=Decimal('2'), metodo_caracterizacion=metodo,
            )
            for metodo in (MetodoCaracterizacion.CUESTIONARIO, MetodoCaracterizacion.CROQUIS_MANUAL,
                           MetodoCaracterizacion.MAPA)
        }
        self.urls = {
            MetodoCaracterizacion.CUESTIONARIO: 'campos:parcelas_cuestionario',
            MetodoCaracterizacion.CROQUIS_MANUAL: 'campos:croquis_manual',
            MetodoCaracterizacion.MAPA: 'mapa:registro_terreno',
        }

    def test_cada_finca_abre_solo_su_metodo_y_los_otros_redirigen(self):
        for metodo_finca, finca in self.fincas.items():
            propia = reverse(self.urls[metodo_finca], kwargs={'pk': finca.pk})
            self.assertEqual(self.client.get(propia).status_code, 200, metodo_finca)
            for metodo, nombre_url in self.urls.items():
                if metodo != metodo_finca:
                    res = self.client.get(reverse(nombre_url, kwargs={'pk': finca.pk}))
                    self.assertRedirects(res, propia, msg_prefix=f'{metodo_finca} por {metodo}')

    def test_no_se_puede_guardar_con_otro_metodo(self):
        finca = self.fincas[MetodoCaracterizacion.CUESTIONARIO]
        croquis = self.client.post(reverse('campos:croquis_manual_guardar', kwargs={'pk': finca.pk}),
                                   json.dumps({'parcelas': [{'id': 'new_1', 'cultivo': 'Papa'}]}),
                                   content_type='application/json')
        self.assertEqual(croquis.status_code, 403)
        mapa = self.client.post(reverse('mapa:guardar_terreno', kwargs={'pk': finca.pk}),
                                '{}', content_type='application/json')
        self.assertEqual(mapa.status_code, 403)
        self.assertFalse(finca.parcelas.exists())

        finca_croquis = self.fincas[MetodoCaracterizacion.CROQUIS_MANUAL]
        self.client.post(reverse('campos:parcelas_cuestionario', kwargs={'pk': finca_croquis.pk}),
                         {'tipo_uso': 'cultivo_agricola', 'cultivo': 'Papa',
                          'superficie_ha': '0.5', 'ubicacion_relativa': 'centro'})
        self.assertFalse(finca_croquis.parcelas.exists())

    def test_guardar_no_cambia_el_metodo(self):
        finca = self.fincas[MetodoCaracterizacion.CROQUIS_MANUAL]
        self.client.post(reverse('campos:croquis_manual_guardar', kwargs={'pk': finca.pk}),
                         json.dumps({'parcelas': [{'id': 'new_1', 'tipo_uso': 'cultivo_agricola',
                                                   'cultivo': 'Papa', 'superficie_ha': 0.5}]}),
                         content_type='application/json')
        finca.refresh_from_db()
        self.assertEqual(finca.metodo_caracterizacion, MetodoCaracterizacion.CROQUIS_MANUAL)
        self.assertEqual(finca.parcelas.count(), 1)

    def test_la_ficha_tiene_un_solo_boton_de_edicion_segun_el_metodo(self):
        textos = {
            MetodoCaracterizacion.CUESTIONARIO: 'Editar en el cuestionario',
            MetodoCaracterizacion.CROQUIS_MANUAL: 'Editar el croquis',
            MetodoCaracterizacion.MAPA: 'Editar en el mapa',
        }
        for metodo, finca in self.fincas.items():
            res = self.client.get(reverse('campos:establecimiento_detalle', kwargs={'pk': finca.pk}))
            self.assertContains(res, reverse(self.urls[metodo], kwargs={'pk': finca.pk}), msg_prefix=metodo)
            for otro, texto in textos.items():
                if otro == metodo:
                    self.assertContains(res, texto, msg_prefix=metodo)
                else:
                    self.assertNotContains(res, texto, msg_prefix=metodo)

    def test_la_ficha_termina_con_ver_diagnostico(self):
        # [Unificación] Botón al final de la ficha, deshabilitado hasta que exista el módulo
        for metodo, finca in self.fincas.items():
            res = self.client.get(reverse('campos:establecimiento_detalle', kwargs={'pk': finca.pk}))
            self.assertContains(res, 'Ver diagnóstico', msg_prefix=metodo)
            self.assertContains(res, 'class="btn btn-diagnostico" disabled', msg_prefix=metodo)
            contenido = res.content.decode()
            # Va abajo de todo: después de las métricas de superficie
            self.assertGreater(contenido.index('Ver diagnóstico'), contenido.index('Ocupación'))
