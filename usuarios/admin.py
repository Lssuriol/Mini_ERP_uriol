from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Panel de administración para el modelo Usuario."""

    list_display = ('username', 'first_name', 'last_name', 'rol', 'activo_en_sistema', 'is_staff')
    list_filter = ('rol', 'activo_en_sistema', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Información del ERP', {'fields': ('rol', 'dni', 'telefono', 'activo_en_sistema')}),
    )
