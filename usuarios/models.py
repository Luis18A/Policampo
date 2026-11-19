from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.db.models.functions import Lower


class UsuarioManager(UserManager):
    """
    El "manager" es el objeto `Usuario.objects`: se encarga de crear y buscar usuarios.
    Lo extendemos para que `createsuperuser` cree usuarios con rol Administrador.
    """

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("rol", Usuario.Rol.ADMINISTRADOR)
        return super().create_superuser(username, email, password, **extra_fields)


class Usuario(AbstractUser):
    """
    Usuario del sistema. Hereda de AbstractUser todo lo de Django (username,
    contraseña cifrada, nombre, apellido, is_active, is_staff, etc.) y agrega:
    - email obligatorio y único
    - rol: Usuario (productor/ingeniero) o Administrador
    """

    class Rol(models.TextChoices):
        # valor guardado en la base / texto que se muestra
        USUARIO = "USUARIO", "Usuario"
        ADMINISTRADOR = "ADMINISTRADOR", "Administrador"

    email = models.EmailField("email", unique=True)
    rol = models.CharField("rol", max_length=20, choices=Rol.choices, default=Rol.USUARIO)

    objects = UsuarioManager()

    # Campos que pide `createsuperuser` además del username y la contraseña.
    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        constraints = [
            # Refuerzo en la base de datos: no puede haber dos usernames iguales
            # aunque difieran en mayúsculas ("Martina" y "martina").
            models.UniqueConstraint(Lower("username"), name="username_unico_sin_mayusculas"),
        ]

    def __str__(self):
        return self.username

    @property
    def es_administrador(self):
        return self.rol == self.Rol.ADMINISTRADOR

    def save(self, *args, **kwargs):
        # El email se guarda siempre en minúsculas para que "Ana@Mail.com" y
        # "ana@mail.com" se consideren el mismo.
        if self.email:
            self.email = self.email.strip().lower()
        # El rol manda: un Administrador puede entrar al panel /admin (is_staff).
        # Un superusuario siempre es Administrador.
        if self.is_superuser:
            self.rol = self.Rol.ADMINISTRADOR
        self.is_staff = self.es_administrador
        super().save(*args, **kwargs)
