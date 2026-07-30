"""
Modelos del módulo de Almacén: categorías, productos y movimientos de inventario.

El control de stock se mantiene en tiempo real mediante el campo
`stock_actual` de Producto, el cual se actualiza automáticamente
cada vez que se registra un MovimientoInventario (entrada o salida).
"""

from django.core.validators import MinValueValidator
from django.db import models

from nucleo.models import ModeloBase


class Categoria(ModeloBase):
    """Categoría de productos (ej. Abarrotes, Bebidas, Limpieza, Lácteos)."""

    nombre = models.CharField(max_length=100, unique=True, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    activa = models.BooleanField(default=True, verbose_name='¿Categoría activa?')

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Producto(ModeloBase):
    """Producto del minimarket, con su stock actual controlado en tiempo real."""

    codigo = models.CharField(max_length=30, unique=True, verbose_name='Código / SKU')
    nombre = models.CharField(max_length=150, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT, related_name='productos', verbose_name='Categoría',
    )
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True, verbose_name='Imagen')

    precio_compra = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)],
        verbose_name='Precio de compra',
    )
    precio_venta = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)],
        verbose_name='Precio de venta',
    )

    stock_actual = models.PositiveIntegerField(default=0, verbose_name='Stock actual')
    stock_minimo = models.PositiveIntegerField(default=5, verbose_name='Stock mínimo')
    unidad_medida = models.CharField(max_length=20, default='UND', verbose_name='Unidad de medida')

    activo = models.BooleanField(default=True, verbose_name='¿Producto activo?')

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']
        indexes = [models.Index(fields=['codigo']), models.Index(fields=['nombre'])]

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'

    @property
    def stock_bajo(self):
        """Indica si el producto se encuentra en o por debajo de su stock mínimo."""
        return self.stock_actual <= self.stock_minimo

    @property
    def margen_ganancia(self):
        if self.precio_compra:
            return self.precio_venta - self.precio_compra
        return self.precio_venta


class MovimientoInventario(ModeloBase):
    """
    Registro histórico de cada entrada o salida de stock de un producto.

    Toda modificación al stock (compras, ajustes, ventas) queda trazada
    aquí, permitiendo auditar el movimiento del inventario en el tiempo.
    """

    class TipoMovimiento(models.TextChoices):
        ENTRADA = 'ENTRADA', 'Entrada de mercadería'
        SALIDA = 'SALIDA', 'Salida por venta'
        AJUSTE = 'AJUSTE', 'Ajuste de inventario'
        MERMA = 'MERMA', 'Merma / producto dañado'

    producto = models.ForeignKey(
        Producto, on_delete=models.PROTECT, related_name='movimientos', verbose_name='Producto',
    )
    tipo_movimiento = models.CharField(max_length=10, choices=TipoMovimiento.choices, verbose_name='Tipo de movimiento')
    cantidad = models.PositiveIntegerField(verbose_name='Cantidad')
    stock_resultante = models.PositiveIntegerField(verbose_name='Stock resultante')
    motivo = models.CharField(max_length=255, blank=True, verbose_name='Motivo / observación')
    usuario = models.ForeignKey(
        'usuarios.Usuario', on_delete=models.PROTECT, related_name='movimientos_inventario', verbose_name='Registrado por',
    )

    class Meta:
        verbose_name = 'Movimiento de inventario'
        verbose_name_plural = 'Movimientos de inventario'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'{self.get_tipo_movimiento_display()} - {self.producto.nombre} ({self.cantidad})'
