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
            'cultivo_principal': 'Tomate agroecológico',
            'disponibilidad_agua': 'Acequia / Turno de riego',
        }
        res = self.client.post(reverse('campos:establecimiento_crear'), data)
        self.assertEqual(res.status_code, 302)
        finca = Establecimiento.objects.get(nombre='Finca Los Valles')
        self.assertEqual(finca.direccion, 'Ruta Provincial 42')
        self.assertEqual(finca.usuario, self.usuario)  # [Integración] queda a nombre de quien lo crea

    def test_guardar_parcela_y_ver_croquis_inmediato(self):
        data = {
            'nombre': 'Parcela Directa',
            'tipo_uso': 'cultivo_agricola',
            'cultivo': 'Maíz',
            'superficie_ha': '1.0000',
            'ubicacion_relativa': 'centro',
            'color_hex': '#2b8a3e',
            'guardar_y_ver_croquis': '1'
        }
        url = reverse('campos:parcelas_cuestionario', kwargs={'pk': self.establecimiento.pk})
        res = self.client.post(url, data)
        # Debe redirigir de inmediato al croquis automático
        self.assertEqual(res.status_code, 302)
        self.assertIn(reverse('campos:croquis_automatico', kwargs={'pk': self.establecimiento.pk}), res.url)

    def test_croquis_manual_sincroniza_con_modelo_parcela(self):
        # Cuando el productor dibuja en el croquis manual, debe crear filas en la tabla Parcela
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
                    'tipo_uso': 'pastura',
                    'cultivo': 'Alfalfa',
                    'superficie_ha': None,  # Productor no conoce aún la superficie
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
        p1 = parcelas_db.get(nombre='Cuadro Dibujado 1')
        self.assertEqual(p1.cultivo, 'Habas andinas')
        self.assertEqual(p1.superficie_ha, Decimal('0.8000'))
        self.assertEqual(p1.origen, 'croquis_manual')
        self.assertIn('x', p1.geometria_visual)

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
