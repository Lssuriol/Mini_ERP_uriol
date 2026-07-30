"""
Modelo de usuario personalizado para el Mini ERP.

Se extiende AbstractUser para incorporar el campo `rol`, que determina
los permisos y las vistas a las que cada persona puede acceder:
    - ADMINISTRADOR: acceso total al sistema.
    - CAJERO: acceso al módulo de caja (ventas y facturación).
    - INVENTARIO: acceso al módulo de almacén (control de stock).
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    """Usuario del sistema con un rol de acceso asociado."""

    class Rol(models.TextChoices):
        ADMINISTRADOR = 'ADMINISTRADOR', 'Administrador'
        CAJERO = 'CAJERO', 'Cajero'
        INVENTARIO = 'INVENTARIO', 'Inventario'

    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.CAJERO,
        verbose_name='Rol de acceso',
    )
    dni = models.CharField(max_length=8, blank=True, null=True, verbose_name='DNI')
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name='Teléfono')
    activo_en_sistema = models.BooleanField(default=True, verbose_name='¿Habilitado en el sistema?')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['first_name', 'last_name']

    def __str__(self):
        nombre_completo = self.get_full_name()
        return f'{nombre_completo or self.username} ({self.get_rol_display()})'

    @property
    def es_administrador(self):
        return self.rol == self.Rol.ADMINISTRADOR

    @property
    def es_cajero(self):
        return self.rol == self.Rol.CAJERO

    @property
    def es_inventario(self):
        return self.rol == self.Rol.INVENTARIO
