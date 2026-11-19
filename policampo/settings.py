"""
Configuración del proyecto PoliCampo.

Los datos sensibles (SECRET_KEY, credenciales de la base de datos) NO se escriben
acá: se leen de variables de entorno que se cargan desde el archivo `.env`.
Ver `.env.example` para saber qué variables hacen falta.

Documentación: https://docs.djangoproject.com/en/5.2/ref/settings/
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# BASE_DIR es la carpeta raíz del proyecto (donde está manage.py).
BASE_DIR = Path(__file__).resolve().parent.parent

# Carga las variables del archivo .env en os.environ.
load_dotenv(BASE_DIR / ".env")


def variable_obligatoria(nombre):
    """Devuelve una variable de entorno o falla con un mensaje claro si no existe."""
    valor = os.environ.get(nombre)
    if not valor:
        raise ImproperlyConfigured(
            f"Falta la variable de entorno {nombre}. Revisá tu archivo .env "
            f"(podés copiar .env.example como punto de partida)."
        )
    return valor


# --- Seguridad -----------------------------------------------------------------

SECRET_KEY = variable_obligatoria("SECRET_KEY")

# En el .env: DEBUG=True para desarrollo. En producción tiene que ser False.
DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "si", "sí")

# Lista separada por comas, ej: "localhost,127.0.0.1"
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]


# --- Aplicaciones --------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Apps propias
    "usuarios",
    "principal",
    "suscripciones",   # por ahora solo pantallas visuales de plan y pago (no cobra nada)
    "campos",          # carga de establecimientos: cuestionario, croquis y mapa (parte de Sol)
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",  # protección CSRF en formularios
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "policampo.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Carpeta de plantillas compartidas (base.html, etc.)
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "policampo.wsgi.application"


# --- Base de datos (PostgreSQL) ------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": variable_obligatoria("DB_NAME"),
        "USER": variable_obligatoria("DB_USER"),
        "PASSWORD": variable_obligatoria("DB_PASSWORD"),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}


# --- Autenticación -------------------------------------------------------------

# Modelo de usuario propio. Tiene que estar definido ANTES de la primera migración.
AUTH_USER_MODEL = "usuarios.Usuario"

# Backends que Django prueba, en orden, para autenticar a alguien.
# El nuestro permite entrar con nombre de usuario o con email.
AUTHENTICATION_BACKENDS = [
    "usuarios.backends.UsuarioOEmailBackend",
]

# A dónde redirigir: login requerido, después de entrar y después de salir.
LOGIN_URL = "usuarios:login"
# Después de iniciar sesión, el usuario va a la pantalla de entrada de carga de datos (app campos).
LOGIN_REDIRECT_URL = "campos:pantalla_entrada"
LOGOUT_REDIRECT_URL = "principal:inicio"

AUTH_PASSWORD_VALIDATORS = [
    # Que la contraseña no se parezca al usuario o al email
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    # Mínimo 8 caracteres
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    # Que no sea una contraseña muy común ("12345678", "password"...)
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    # Que no sea solo números
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --- Idioma y zona horaria -----------------------------------------------------

LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Jujuy"
USE_I18N = True
USE_TZ = True


# --- Archivos estáticos (CSS, JS, imágenes) ------------------------------------

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
