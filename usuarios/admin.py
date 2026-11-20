from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Panel de administración de usuarios, basado en el de Django más el campo rol."""

    list_display = ("username", "email", "rol", "is_active", "date_joined")
    list_filter = ("rol", "is_active")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)

    # is_staff no se edita a mano: se calcula a partir del rol (ver Usuario.save).
    readonly_fields = ("is_staff", "last_login", "date_joined")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Datos personales", {"fields": ("first_name", "last_name", "email")}),
        ("Rol y permisos", {"fields": ("rol", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Fechas", {"fields": ("last_login", "date_joined")}),
    )

    # Formulario para "Agregar usuario" desde el admin
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("username", "email", "rol", "password1", "password2")}),
    )
