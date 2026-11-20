from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class UsuarioOEmailBackend(ModelBackend):
    """
    Backend de autenticación: permite iniciar sesión con el nombre de usuario
    O con el email, más la contraseña.

    Django llama a `authenticate()` de cada backend listado en
    AUTHENTICATION_BACKENDS. Heredamos de ModelBackend, así reutilizamos su
    manejo de permisos y su chequeo de "usuario activo"; solo cambiamos cómo
    se busca al usuario.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        Usuario = get_user_model()
        identificador = username.strip()

        # Si tiene "@" es un email; si no, un nombre de usuario.
        # "__iexact" compara sin distinguir mayúsculas/minúsculas.
        if "@" in identificador:
            filtro = {"email__iexact": identificador}
        else:
            filtro = {"username__iexact": identificador}

        try:
            usuario = Usuario.objects.get(**filtro)
        except Usuario.DoesNotExist:
            # Calculamos un hash igual, para que la respuesta tarde lo mismo que
            # con un usuario existente. Así no se puede averiguar qué usuarios
            # existen midiendo tiempos (lo mismo que hace ModelBackend).
            Usuario().set_password(password)
            return None

        # check_password compara contra la contraseña cifrada guardada.
        # user_can_authenticate rechaza usuarios desactivados (is_active=False).
        if usuario.check_password(password) and self.user_can_authenticate(usuario):
            return usuario
        return None
