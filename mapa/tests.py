"""Tests del mapa de diseño espacial (parte de Agus, integrado)."""

import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from campos.models import Establecimiento

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


def payload(porcentaje=21.5, cumple=True):
    """Un diseño con la misma forma que el que arma mapa.js al guardar."""
    return {
        "version": "1.0",
        "ubicacion": {"lat": -24.375, "lng": -65.095, "zona_seleccionada": "Perico"},
        "cultivo_principal": {"codigo": "frutilla", "nombre": "Frutilla"},
        "diseno": {"tipo": "perimetral", "porcentaje_objetivo": 20, "porcentaje_real": porcentaje},
        "metricas": {"area_total_ha": 1.2345, "perimetro_m": 450},
        "diagnostico_espacial": {"estado": "ok", "cumple_minimo_20_pct": cumple, "mensaje": ""},
        "geometrias": {
            "parcela": PARCELA,
            "sectores_cultivo": {"type": "FeatureCollection", "features": []},
            "corredores_florales": {"type": "FeatureCollection", "features": []},
        },
    }


class MapaTests(TestCase):
    def setUp(self):
        Usuario = get_user_model()
        self.ana = Usuario.objects.create_user("ana", "ana@mail.com", CONTRASENA)
        self.beto = Usuario.objects.create_user("beto", "beto@mail.com", CONTRASENA)
        self.finca = Establecimiento.objects.create(
            usuario=self.ana, nombre="Finca de Ana", localidad="Perico",
            superficie_total_ha=Decimal("1.5"), cultivo_principal="Frutilla",
        )
        self.url_mapa = reverse("mapa:delimitar_terreno", kwargs={"pk": self.finca.pk})
        self.url_guardar = reverse("mapa:guardar_diseno", kwargs={"pk": self.finca.pk})

    def guardar(self, datos):
        cuerpo = datos if isinstance(datos, str) else json.dumps(datos)
        return self.client.post(self.url_guardar, cuerpo, content_type="application/json")

    def test_sin_sesion_redirige_al_login(self):
        res = self.client.get(self.url_mapa)
        self.assertRedirects(res, f"{reverse('usuarios:login')}?next={self.url_mapa}")

    def test_el_duenio_ve_el_mapa_de_su_establecimiento(self):
        self.client.login(username="ana", password=CONTRASENA)
        res = self.client.get(self.url_mapa)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Finca de Ana")
        self.assertContains(res, f'window.POLICAMPO_API_GUARDAR_URL = "{self.url_guardar}"')

    def test_otro_usuario_no_puede_ver_ni_guardar(self):
        self.client.login(username="beto", password=CONTRASENA)
        self.assertEqual(self.client.get(self.url_mapa).status_code, 404)
        self.assertEqual(self.guardar(payload()).status_code, 404)
        self.assertFalse(DisenoEspacial.objects.exists())

    def test_guardar_y_reemplazar_el_diseno(self):
        self.client.login(username="ana", password=CONTRASENA)
        res = self.guardar(payload())
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["ok"])

        diseno = DisenoEspacial.objects.get(establecimiento=self.finca)
        self.assertEqual(diseno.area_total_ha, Decimal("1.2345"))
        self.assertEqual(diseno.porcentaje_floral, Decimal("21.50"))
        self.assertTrue(diseno.cumple_minimo_20)
        self.assertEqual(diseno.tipo_diseno, "perimetral")

        # Guardar de nuevo reemplaza el anterior (uno por establecimiento)
        self.guardar(payload(porcentaje=12, cumple=False))
        self.assertEqual(DisenoEspacial.objects.count(), 1)
        diseno.refresh_from_db()
        self.assertFalse(diseno.cumple_minimo_20)

    def test_datos_invalidos_devuelven_400(self):
        self.client.login(username="ana", password=CONTRASENA)
        sin_parcela = payload()
        del sin_parcela["geometrias"]["parcela"]
        for malo in ("esto no es json", {"metricas": {}}, sin_parcela):
            self.assertEqual(self.guardar(malo).status_code, 400)
        self.assertFalse(DisenoEspacial.objects.exists())

    def test_sin_diseno_el_mapa_arranca_vacio(self):
        self.client.login(username="ana", password=CONTRASENA)
        res = self.client.get(self.url_mapa)
        self.assertIsNone(res.context["parcela_inicial"])
        self.assertIsNone(res.context["centro_inicial"])

    def test_precarga_el_ultimo_diseno_guardado(self):
        self.client.login(username="ana", password=CONTRASENA)
        self.guardar(payload())
        res = self.client.get(self.url_mapa)
        self.assertEqual(res.context["parcela_inicial"], PARCELA)
        self.assertEqual(res.context["centro_inicial"], {"lat": -24.375, "lng": -65.095, "zoom": 16})

    def test_inicio_lista_y_ficha_llevan_al_mapa_de_agus(self):
        self.client.login(username="ana", password=CONTRASENA)
        for nombre, kwargs in (("campos:pantalla_entrada", {}),
                               ("campos:establecimientos_lista", {}),
                               ("campos:establecimiento_detalle", {"pk": self.finca.pk})):
            res = self.client.get(reverse(nombre, kwargs=kwargs))
            self.assertContains(res, self.url_mapa, msg_prefix=nombre)

    def test_nuevo_predio_en_modo_mapa_termina_en_el_mapa_de_agus(self):
        self.client.login(username="ana", password=CONTRASENA)
        url = reverse("campos:establecimiento_crear") + "?modo=mapa"
        res = self.client.post(url, {
            "nombre": "Finca Nueva", "direccion": "Ruta 9 km 1", "departamento": "Palpalá",
            "localidad": "Palpalá", "ecorregion": "Valles Templados", "superficie_total_ha": "2.5",
            "cultivo_principal": "Maíz", "disponibilidad_agua": "Pozo / Bomba",
        })
        nueva = Establecimiento.objects.get(nombre="Finca Nueva")
        self.assertRedirects(res, reverse("mapa:delimitar_terreno", kwargs={"pk": nueva.pk}))

    def test_el_mapa_de_sol_ya_no_existe(self):
        self.client.login(username="ana", password=CONTRASENA)
        self.assertEqual(self.client.get(f"/campos/establecimientos/{self.finca.pk}/mapa/").status_code, 404)
