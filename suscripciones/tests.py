"""Tests de las pantallas de plan y pago (solo visuales)."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

CONTRASENA = "Quebrada-Huma2024"


class PantallasDeSuscripcionTests(TestCase):
    url_plan = reverse("suscripciones:plan")
    url_pago = reverse("suscripciones:pago")

    def iniciar_sesion(self):
        get_user_model().objects.create_user("martina", "martina@mail.com", CONTRASENA)
        self.client.login(username="martina", password=CONTRASENA)

    def test_sin_sesion_redirige_al_login(self):
        for url in (self.url_plan, self.url_pago):
            respuesta = self.client.get(url)
            # LoginRequiredMixin manda al login y recuerda a dónde ibas con ?next=
            self.assertRedirects(respuesta, f"{reverse('usuarios:login')}?next={url}")

    def test_pantalla_del_plan(self):
        self.iniciar_sesion()
        respuesta = self.client.get(self.url_plan)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "PoliCampo Pro")
        self.assertContains(respuesta, self.url_pago)            # botón "Continuar al pago"
        self.assertContains(respuesta, "Continuar sin pagar por ahora")

    def test_pantalla_de_pago_es_solo_visual(self):
        self.iniciar_sesion()
        respuesta = self.client.get(self.url_pago)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Los pagos todavía no están habilitados")
        # El botón Pagar está deshabilitado
        self.assertContains(respuesta, 'disabled aria-disabled="true">Pagar')
        # No hay campos para datos de tarjeta ni un formulario que envíe datos de pago.
        # (El único <form> de la página es el de "Cerrar sesión" en la cabecera.)
        contenido = respuesta.content.decode()
        self.assertEqual(contenido.count("<form"), 1)
        for campo in ('autocomplete="cc-', 'name="tarjeta', 'name="cvv', 'name="numero'):
            self.assertNotIn(campo, contenido)

    def test_registro_lleva_al_plan(self):
        datos = {"username": "nueva", "email": "nueva@mail.com",
                 "password1": CONTRASENA, "password2": CONTRASENA}
        respuesta = self.client.post(reverse("usuarios:registro"), datos, follow=True)
        self.assertTemplateUsed(respuesta, "suscripciones/plan.html")
        self.assertContains(respuesta, "Bienvenido/a a PoliCampo, nueva")
