"""Tests de la landing page. Se corren con:  venv\\Scripts\\python manage.py test"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class LandingTests(TestCase):
    url = reverse("principal:inicio")

    def test_la_landing_carga_y_es_publica(self):
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertTemplateUsed(respuesta, "principal/inicio.html")
        for seccion in ('id="que-es"', 'id="como-funciona"', 'id="para-quien"', 'id="contacto"'):
            self.assertContains(respuesta, seccion)

    def test_no_se_filtran_comentarios_de_plantilla(self):
        # Un comentario {# #} escrito en varias líneas no se oculta: Django lo muestra como texto.
        respuesta = self.client.get(self.url)
        self.assertNotContains(respuesta, "{#")
        self.assertNotContains(respuesta, "{% comment")

    def test_visitante_ve_botones_de_registro_y_login(self):
        respuesta = self.client.get(self.url)
        self.assertContains(respuesta, reverse("usuarios:registro"))
        self.assertContains(respuesta, reverse("usuarios:login"))
        self.assertNotContains(respuesta, "Cerrar sesión")

    def test_usuario_logueado_ve_su_nombre_y_cerrar_sesion(self):
        get_user_model().objects.create_user("martina", "martina@mail.com", "Quebrada-Huma2024")
        self.client.login(username="martina", password="Quebrada-Huma2024")
        respuesta = self.client.get(self.url)
        # El avatar con la inicial indica la sesión iniciada (y nombra al usuario para lectores de pantalla)
        self.assertContains(respuesta, 'aria-label="Sesión iniciada como martina"')
        self.assertNotContains(respuesta, "Hola, martina")
        self.assertContains(respuesta, "Cerrar sesión")
        self.assertNotContains(respuesta, "Crear cuenta")

    def test_menu_cambia_segun_si_inicio_sesion(self):
        # Visitante: ve las secciones de la landing
        visitante = self.client.get(self.url)
        self.assertContains(visitante, 'href="/#que-es"')
        self.assertNotContains(visitante, reverse("campos:establecimiento_crear"))

        # Con sesión iniciada: ve Inicio, Mis establecimientos y Nuevo predio, y no las secciones
        get_user_model().objects.create_user("martina", "martina@mail.com", "Quebrada-Huma2024")
        self.client.login(username="martina", password="Quebrada-Huma2024")
        con_sesion = self.client.get(self.url)
        self.assertNotContains(con_sesion, 'href="/#que-es"')
        self.assertContains(con_sesion, reverse("campos:establecimientos_lista"))
        self.assertContains(con_sesion, reverse("campos:establecimiento_crear"))

        # La opción de la página actual queda marcada
        lista = self.client.get(reverse("campos:establecimientos_lista"))
        self.assertContains(lista, 'class="activo" aria-current="page">Mis establecimientos')

    def test_boton_administracion_solo_para_administradores(self):
        Usuario = get_user_model()
        Usuario.objects.create_user("comun", "comun@mail.com", "Quebrada-Huma2024")
        Usuario.objects.create_superuser("jefa", "jefa@mail.com", "Quebrada-Huma2024")
        url_admin = reverse("admin:index")

        self.client.login(username="comun", password="Quebrada-Huma2024")
        self.assertNotContains(self.client.get(self.url), url_admin)

        self.client.login(username="jefa", password="Quebrada-Huma2024")
        self.assertContains(self.client.get(self.url), f'href="{url_admin}" class="boton boton-contorno boton-admin"')

    def test_mensaje_de_bienvenida_se_muestra_como_aviso_flotante(self):
        # Después de registrarse, la landing muestra el mensaje en el contenedor flotante
        # (.mensajes), que no ocupa lugar en la página y no empuja la portada.
        datos = {"username": "nueva", "email": "nueva@mail.com",
                 "password1": "Quebrada-Huma2024", "password2": "Quebrada-Huma2024"}
        respuesta = self.client.post(reverse("usuarios:registro"), datos, follow=True)
        self.assertContains(respuesta, 'class="mensajes" data-mensajes')
        self.assertContains(respuesta, "Bienvenido/a a PoliCampo, nueva")
