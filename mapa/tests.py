"""Tests del mapa (parte de Agus, integrado): paso 1 terreno (entrada) y paso 2 propuesta (salida)."""

import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from campos.models import Establecimiento, MetodoCaracterizacion

from .models import DisenoEspacial

CONTRASENA = "Quebrada-Huma2024"

PARCELA = {
    "type": "Feature",
    "properties": {},
    "geometry": {
        "type": "Polygon",
        "coordinates": [[[-65.10, -24.38], [-65.09, -24.38], [-65.09, -24.37], [-65.10, -24.37], [-65.10, -24.38]]],
    },
}


def terreno():
    """Lo que guarda el paso 1 (entrada_mapa.js): contorno y sectores, todavía sin métricas."""
    return {"version": "1.0", "geometrias": {"parcela": PARCELA}}


def propuesta(porcentaje=21.5, cumple=True):
    """Lo que guarda el paso 2 (salida_mapa.js): el rediseño con franjas y métricas."""
    return {
        "version": "1.0",
        "diseno": {"tipo": "perimetral", "porcentaje_objetivo": 20, "porcentaje_real": porcentaje},
        "metricas": {"area_total_ha": 1.2345, "perimetro_m": 450},
        "diagnostico_espacial": {"estado": "ok", "cumple_minimo_20_pct": cumple, "mensaje": ""},
        "geometrias": {"parcela": PARCELA},
    }


class MapaTests(TestCase):
    def setUp(self):
        Usuario = get_user_model()
        self.ana = Usuario.objects.create_user("ana", "ana@mail.com", CONTRASENA)
        self.beto = Usuario.objects.create_user("beto", "beto@mail.com", CONTRASENA)
        self.finca = Establecimiento.objects.create(
            usuario=self.ana, nombre="Finca de Ana", localidad="Perico",
            superficie_total_ha=Decimal("1.5"),
            metodo_caracterizacion=MetodoCaracterizacion.MAPA,  # [Unificación] cargada por el mapa
        )
        pk = {"pk": self.finca.pk}
        self.url_terreno = reverse("mapa:registro_terreno", kwargs=pk)
        self.url_guardar_terreno = reverse("mapa:guardar_terreno", kwargs=pk)
        self.url_propuesta = reverse("mapa:propuesta_redisenio", kwargs=pk)
        self.url_guardar_propuesta = reverse("mapa:guardar_propuesta", kwargs=pk)

    def post_json(self, url, datos):
        cuerpo = datos if isinstance(datos, str) else json.dumps(datos)
        return self.client.post(url, cuerpo, content_type="application/json")

    # ─── Acceso y privacidad ───
    def test_sin_sesion_redirige_al_login(self):
        for url in (self.url_terreno, self.url_propuesta):
            res = self.client.get(url)
            self.assertRedirects(res, f"{reverse('usuarios:login')}?next={url}")

    def test_el_duenio_ve_las_dos_paginas(self):
        self.client.login(username="ana", password=CONTRASENA)
        res = self.client.get(self.url_terreno)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, f'window.POLICAMPO_API_GUARDAR_ENTRADA_URL = "{self.url_guardar_terreno}"')
        self.assertContains(res, f'window.POLICAMPO_URL_PROPUESTA = "{self.url_propuesta}"')
        res = self.client.get(self.url_propuesta)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, f'window.POLICAMPO_API_GUARDAR_PROPUESTA_URL = "{self.url_guardar_propuesta}"')

    def test_otro_usuario_no_puede_ver_ni_guardar(self):
        self.client.login(username="beto", password=CONTRASENA)
        for url in (self.url_terreno, self.url_propuesta):
            self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.post_json(self.url_guardar_terreno, terreno()).status_code, 404)
        self.assertEqual(self.post_json(self.url_guardar_propuesta, propuesta()).status_code, 404)
        self.assertFalse(DisenoEspacial.objects.exists())

    # ─── Paso 1 → paso 2 ───
    def test_guardar_terreno_y_despues_la_propuesta(self):
        self.client.login(username="ana", password=CONTRASENA)
        res = self.post_json(self.url_guardar_terreno, terreno())
        self.assertEqual(res.status_code, 200)
        diseno = DisenoEspacial.objects.get(establecimiento=self.finca)
        self.assertEqual(diseno.tipo_diseno, "Borrador (Paso 1)")
        self.assertFalse(diseno.cumple_minimo_20)

        # La propuesta recibe el terreno guardado
        res = self.client.get(self.url_propuesta)
        self.assertEqual(res.context["terreno"], terreno())
        self.assertContains(res, 'id="terreno-inicial"')

        # Guardar la propuesta completa las métricas (y reemplaza: uno por finca)
        res = self.post_json(self.url_guardar_propuesta, propuesta())
        self.assertTrue(res.json()["ok"])
        self.assertEqual(DisenoEspacial.objects.count(), 1)
        diseno.refresh_from_db()
        self.assertEqual(diseno.area_total_ha, Decimal("1.2345"))
        self.assertEqual(diseno.porcentaje_floral, Decimal("21.50"))
        self.assertTrue(diseno.cumple_minimo_20)
        self.assertEqual(diseno.tipo_diseno, "perimetral")

    def test_propuesta_sin_terreno_no_rompe(self):
        self.client.login(username="ana", password=CONTRASENA)
        res = self.client.get(self.url_propuesta)
        self.assertEqual(res.status_code, 200)
        self.assertIsNone(res.context["terreno"])
        self.assertNotContains(res, "POLICAMPO_TERRENO_INICIAL = JSON.parse")

    def test_datos_invalidos_devuelven_400(self):
        self.client.login(username="ana", password=CONTRASENA)
        for url in (self.url_guardar_terreno, self.url_guardar_propuesta):
            for malo in ("esto no es json", "[1, 2]"):
                self.assertEqual(self.post_json(url, malo).status_code, 400, url)
        malo = propuesta()
        malo["metricas"]["area_total_ha"] = "mucho"
        self.assertEqual(self.post_json(self.url_guardar_propuesta, malo).status_code, 400)
        self.assertFalse(DisenoEspacial.objects.exists())

    def test_el_terreno_se_escapa_al_pasarlo_a_javascript(self):
        # Un texto con </script> no puede cortar el <script> de la página (json_script lo escapa)
        self.client.login(username="ana", password=CONTRASENA)
        datos = terreno()
        datos["nota"] = "</script><script>alert(1)</script>"
        self.post_json(self.url_guardar_terreno, datos)
        res = self.client.get(self.url_propuesta)
        self.assertNotContains(res, "<script>alert(1)")

    # ─── Unificación con el resto del sistema ───
    def test_inicio_por_mapa_siempre_crea_una_finca_nueva(self):
        # [Unificación] Como las otras dos opciones, "Ubicar mi campo en el mapa" carga una finca nueva
        self.client.login(username="ana", password=CONTRASENA)
        res = self.client.get(reverse("campos:pantalla_entrada"))
        self.assertContains(res, reverse("campos:establecimiento_crear") + "?modo=mapa")
        self.assertNotContains(res, self.url_terreno)

    def test_la_ficha_tiene_el_boton_editar_en_el_mapa(self):
        self.client.login(username="ana", password=CONTRASENA)
        res = self.client.get(reverse("campos:establecimiento_detalle", kwargs={"pk": self.finca.pk}))
        self.assertNotContains(res, "Herramientas y Representaciones")
        self.assertContains(res, self.url_terreno)
        self.assertContains(res, "Editar en el mapa")

    def test_la_tarjeta_de_la_lista_solo_lleva_a_la_ficha(self):
        self.client.login(username="ana", password=CONTRASENA)
        res = self.client.get(reverse("campos:establecimientos_lista"))
        self.assertContains(res, reverse("campos:establecimiento_detalle", kwargs={"pk": self.finca.pk}))
        self.assertNotContains(res, self.url_terreno)

    def test_nuevo_predio_en_modo_mapa_termina_en_el_registro_de_terreno(self):
        self.client.login(username="ana", password=CONTRASENA)
        url = reverse("campos:establecimiento_crear") + "?modo=mapa"
        res = self.client.post(url, {
            "nombre": "Finca Nueva", "direccion": "Ruta 9 km 1", "departamento": "Palpalá",
            "localidad": "Palpalá", "ecorregion": "Valles Templados", "superficie_total_ha": "2.5",
        })
        nueva = Establecimiento.objects.get(nombre="Finca Nueva")
        self.assertRedirects(res, reverse("mapa:registro_terreno", kwargs={"pk": nueva.pk}))
        self.assertEqual(nueva.metodo_caracterizacion, MetodoCaracterizacion.MAPA)

    def test_el_mapa_de_sol_y_el_mapa_viejo_ya_no_existen(self):
        self.client.login(username="ana", password=CONTRASENA)
        for viejo in ("mapa", "disenar"):
            res = self.client.get(f"/campos/establecimientos/{self.finca.pk}/{viejo}/")
            self.assertEqual(res.status_code, 404, viejo)
