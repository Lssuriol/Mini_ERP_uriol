"""Modelos base abstractos compartidos entre las aplicaciones del ERP."""

from django.db import models


class ModeloBase(models.Model):
    """
    Modelo abstracto con campos de auditoría comunes a la mayoría
    de entidades del sistema (fechas de creación y actualización).
    """

    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name='Última actualización')

    class Meta:
        abstract = True
