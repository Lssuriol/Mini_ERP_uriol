"""
Modelos del módulo de Caja: ventas y su detalle (facturación).

Cada venta agrupa uno o más productos vendidos (DetalleVenta). El total
de la venta se calcula a partir de la suma de sus detalles más el IGV.
"""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from nucleo.models import ModeloBase


class Venta(ModeloBase):
    """Comprobante de venta emitido por un cajero."""

    class TipoComprobante(models.TextChoices):
        BOLETA = 'BOLETA', 'Boleta de venta'
        FACTURA = 'FACTURA', 'Factura'
        NOTA_VENTA = 'NOTA_VENTA', 'Nota de venta'

    class MetodoPago(models.TextChoices):
        EFECTIVO = 'EFECTIVO', 'Efectivo'
        TARJETA = 'TARJETA', 'Tarjeta'
        YAPE_PLIN = 'YAPE_PLIN', 'Yape / Plin'

    class Estado(models.TextChoices):
        COMPLETADA = 'COMPLETADA', 'Completada'
        ANULADA = 'ANULADA', 'Anulada'

    numero_comprobante = models.CharField(max_length=20, unique=True, verbose_name='N° de comprobante')
    tipo_comprobante = models.CharField(
        max_length=15, choices=TipoComprobante.choices, default=TipoComprobante.BOLETA,
        verbose_name='Tipo de comprobante',
    )
    metodo_pago = models.CharField(max_length=15, choices=MetodoPago.choices, default=MetodoPago.EFECTIVO)

    cliente_nombre = models.CharField(max_length=150, blank=True, default='Cliente varios', verbose_name='Cliente')
    cliente_documento = models.CharField(max_length=15, blank=True, verbose_name='DNI / RUC del cliente')
    cliente_email = models.EmailField(blank=True, null=True, verbose_name='Correo del cliente')

    # --- Campos para POS Físico (solo para método_pago == TARJETA) ---
    pos_operador = models.CharField(max_length=50, blank=True, verbose_name='Operador POS (ej. Niubiz)')
    pos_tipo_tarjeta = models.CharField(max_length=50, blank=True, verbose_name='Tipo de tarjeta')
    pos_numero_autorizacion = models.CharField(max_length=50, blank=True, verbose_name='N° Autorización')
    pos_ultimos_digitos = models.CharField(max_length=4, blank=True, verbose_name='Últimos 4 dígitos')

    cajero = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='ventas_realizadas', verbose_name='Cajero',
    )

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    igv = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    total = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    estado = models.CharField(max_length=15, choices=Estado.choices, default=Estado.COMPLETADA)
    motivo_anulacion = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-fecha_creacion']
        indexes = [models.Index(fields=['numero_comprobante']), models.Index(fields=['fecha_creacion'])]

    def __str__(self):
        return f'{self.get_tipo_comprobante_display()} {self.numero_comprobante}'


class DetalleVenta(models.Model):
    """Línea de detalle de una venta: un producto, su cantidad y su subtotal."""

    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles', verbose_name='Venta')
    producto = models.ForeignKey(
        'almacen.Producto', on_delete=models.PROTECT, related_name='detalles_venta', verbose_name='Producto',
    )
    cantidad = models.PositiveIntegerField(verbose_name='Cantidad')
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio unitario')
    subtotal_linea = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Subtotal')

    class Meta:
        verbose_name = 'Detalle de venta'
        verbose_name_plural = 'Detalles de venta'

    def __str__(self):
        return f'{self.producto.nombre} x{self.cantidad}'
