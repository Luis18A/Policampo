"""
Tests de registro y login.

Se corren con:  venv\\Scripts\\python manage.py test usuarios
Django crea una base de datos de prueba vacía (test_policampo), corre los tests
y la borra al final: tus datos reales no se tocan.
"""

from django.contrib.auth import authenticate, get_user_model
from django.test import TestCase
from django.urls import reverse

Usuario = get_user_model()

CONTRASENA = "Quebrada-Huma2024"


class ModeloUsuarioTests(TestCase):
    def test_usuario_nuevo_tiene_rol_usuario_y_no_es_staff(self):
        u = Usuario.objects.create_user("ana", "ana@mail.com", CONTRASENA)
        self.assertEqual(u.rol, Usuario.Rol.USUARIO)
        self.assertFalse(u.is_staff)

    def test_superusuario_es_administrador_y_staff(self):
        admin = Usuario.objects.create_superuser("jefa", "jefa@mail.com", CONTRASENA)
        self.assertEqual(admin.rol, Usuario.Rol.ADMINISTRADOR)
        self.assertTrue(admin.is_staff)

    def test_rol_administrador_activa_staff(self):
        u = Usuario.objects.create_user("beto", "beto@mail.com", CONTRASENA)
        u.rol = Usuario.Rol.ADMINISTRADOR
        u.save()
        self.assertTrue(u.is_staff)

    def test_email_se_guarda_en_minusculas(self):
        u = Usuario.objects.create_user("caro", "Caro@Mail.COM", CONTRASENA)
        self.assertEqual(u.email, "caro@mail.com")

    def test_la_contrasena_se_guarda_cifrada(self):
        u = Usuario.objects.create_user("dani", "dani@mail.com", CONTRASENA)
        self.assertNotEqual(u.password, CONTRASENA)
        self.assertTrue(u.check_password(CONTRASENA))


class RegistroTests(TestCase):
    url = reverse("usuarios:registro")

    def datos(self, **cambios):
        datos = {
            "username": "martina",
            "email": "martina@mail.com",
            "password1": CONTRASENA,
            "password2": CONTRASENA,
        }
        datos.update(cambios)
        return datos

    def test_la_pagina_de_registro_carga(self):
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Crear cuenta")

    def test_registro_valido_crea_usuario_con_rol_usuario_e_inicia_sesion(self):
        respuesta = self.client.post(self.url, self.datos())
        # Después de registrarse va al paso 2: elegir el plan
        self.assertRedirects(respuesta, reverse("suscripciones:plan"))

        u = Usuario.objects.get(username="martina")
        self.assertEqual(u.email, "martina@mail.com")
        self.assertEqual(u.rol, Usuario.Rol.USUARIO)
        # Quedó logueado: la sesión guarda el id del usuario
        self.assertEqual(int(self.client.session["_auth_user_id"]), u.pk)

    def test_no_se_puede_registrar_como_administrador(self):
        self.client.post(self.url, self.datos(rol="ADMINISTRADOR", is_staff="on", is_superuser="on"))
        u = Usuario.objects.get(username="martina")
        self.assertEqual(u.rol, Usuario.Rol.USUARIO)
        self.assertFalse(u.is_staff)
        self.assertFalse(u.is_superuser)

    def test_email_repetido_es_rechazado(self):
        Usuario.objects.create_user("otra", "martina@mail.com", CONTRASENA)
        respuesta = self.client.post(self.url, self.datos())
        self.assertEqual(respuesta.status_code, 200)  # vuelve a mostrar el formulario
        self.assertFormError(respuesta.context["form"], "email", "Ya existe una cuenta registrada con este email.")
        self.assertFalse(Usuario.objects.filter(username="martina").exists())

    def test_email_repetido_con_mayusculas_es_rechazado(self):
        Usuario.objects.create_user("otra", "martina@mail.com", CONTRASENA)
        respuesta = self.client.post(self.url, self.datos(email="MARTINA@Mail.com"))
        self.assertTrue(respuesta.context["form"].has_error("email"))
        self.assertEqual(Usuario.objects.count(), 1)

    def test_usuario_repetido_es_rechazado(self):
        Usuario.objects.create_user("martina", "otro@mail.com", CONTRASENA)
        respuesta = self.client.post(self.url, self.datos())
        self.assertTrue(respuesta.context["form"].has_error("username"))
        self.assertEqual(Usuario.objects.count(), 1)

    def test_usuario_repetido_con_mayusculas_es_rechazado(self):
        Usuario.objects.create_user("martina", "otro@mail.com", CONTRASENA)
        respuesta = self.client.post(self.url, self.datos(username="Martina"))
        self.assertTrue(respuesta.context["form"].has_error("username"))
        self.assertEqual(Usuario.objects.count(), 1)

    def test_contrasena_debil_es_rechazada(self):
        respuesta = self.client.post(self.url, self.datos(password1="12345678", password2="12345678"))
        self.assertTrue(respuesta.context["form"].has_error("password2"))
        self.assertFalse(Usuario.objects.exists())

    def test_contrasenas_distintas_son_rechazadas(self):
        respuesta = self.client.post(self.url, self.datos(password2="Otra-Cosa-2024"))
        self.assertTrue(respuesta.context["form"].has_error("password2"))
        self.assertFalse(Usuario.objects.exists())

    def test_email_obligatorio(self):
        respuesta = self.client.post(self.url, self.datos(email=""))
        self.assertTrue(respuesta.context["form"].has_error("email"))
        self.assertFalse(Usuario.objects.exists())


class LoginTests(TestCase):
    url = reverse("usuarios:login")

    def setUp(self):
        self.usuario = Usuario.objects.create_user("martina", "martina@mail.com", CONTRASENA)

    def assertLogueado(self):
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.usuario.pk)

    def assertNoLogueado(self):
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_la_pagina_de_login_carga(self):
        respuesta = self.client.get(self.url)
        self.assertContains(respuesta, "Usuario o email")

    def test_login_con_nombre_de_usuario(self):
        respuesta = self.client.post(self.url, {"username": "martina", "password": CONTRASENA})
        self.assertRedirects(respuesta, reverse("principal:inicio"))
        self.assertLogueado()

    def test_login_con_email(self):
        respuesta = self.client.post(self.url, {"username": "martina@mail.com", "password": CONTRASENA})
        self.assertRedirects(respuesta, reverse("principal:inicio"))
        self.assertLogueado()

    def test_login_con_email_en_mayusculas(self):
        self.client.post(self.url, {"username": "MARTINA@Mail.com", "password": CONTRASENA})
        self.assertLogueado()

    def test_login_con_usuario_en_mayusculas(self):
        self.client.post(self.url, {"username": "Martina", "password": CONTRASENA})
        self.assertLogueado()

    def test_contrasena_incorrecta(self):
        respuesta = self.client.post(self.url, {"username": "martina", "password": "incorrecta"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Usuario/email o contraseña incorrectos.")
        self.assertNoLogueado()

    def test_usuario_inexistente(self):
        self.client.post(self.url, {"username": "nadie", "password": CONTRASENA})
        self.assertNoLogueado()

    def test_email_inexistente(self):
        self.client.post(self.url, {"username": "nadie@mail.com", "password": CONTRASENA})
        self.assertNoLogueado()

    def test_usuario_desactivado_no_puede_entrar(self):
        self.usuario.is_active = False
        self.usuario.save()
        self.client.post(self.url, {"username": "martina", "password": CONTRASENA})
        self.assertNoLogueado()

    def test_logout_cierra_la_sesion(self):
        self.client.login(username="martina", password=CONTRASENA)
        respuesta = self.client.post(reverse("usuarios:logout"))
        self.assertRedirects(respuesta, reverse("principal:inicio"))
        self.assertNoLogueado()


class BackendTests(TestCase):
    """Prueba el backend directamente, sin pasar por la vista."""

    def setUp(self):
        self.usuario = Usuario.objects.create_user("martina", "martina@mail.com", CONTRASENA)

    def test_authenticate_con_usuario_y_con_email(self):
        self.assertEqual(authenticate(username="martina", password=CONTRASENA), self.usuario)
        self.assertEqual(authenticate(username="martina@mail.com", password=CONTRASENA), self.usuario)

    def test_authenticate_sin_datos_devuelve_none(self):
        self.assertIsNone(authenticate(username=None, password=CONTRASENA))
        self.assertIsNone(authenticate(username="martina", password=None))
