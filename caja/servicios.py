"""
Servicio de procesamiento de ventas.

La función `procesar_venta` es el corazón del módulo de Caja: recibe el
carrito armado en el punto de venta y, dentro de una única transacción
atómica, crea el comprobante, sus detalles y descuenta el stock de cada
producto. Si cualquier paso falla (por ejemplo, stock insuficiente), la
transacción completa se revierte y NO queda ningún registro a medias:
ni la venta, ni el detalle, ni la reducción de stock.
"""

from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.conf import settings

from almacen.models import MovimientoInventario, Producto
from almacen.servicios import registrar_movimiento

from .models import DetalleVenta, Venta

PREFIJOS_COMPROBANTE = {
    Venta.TipoComprobante.BOLETA: getattr(settings, 'SERIE_BOLETA', 'B001'),
    Venta.TipoComprobante.FACTURA: getattr(settings, 'SERIE_FACTURA', 'F001'),
    Venta.TipoComprobante.NOTA_VENTA: 'NV01',
}


def _generar_numero_comprobante(tipo_comprobante: str) -> str:
    """Genera un correlativo simple por tipo de comprobante (ej. B001-000123)."""
    prefijo = PREFIJOS_COMPROBANTE.get(tipo_comprobante, 'NV01')
    correlativo = Venta.objects.filter(tipo_comprobante=tipo_comprobante).count() + 1
    return f'{prefijo}-{correlativo:06d}'


from facturacion.servicios import procesar_emision_electronica

@transaction.atomic
def procesar_venta(*, carrito, cajero, tipo_comprobante, metodo_pago, cliente_nombre='', cliente_documento='', cliente_email='', pos_operador='', pos_tipo_tarjeta='', pos_numero_autorizacion='', pos_ultimos_digitos=''):
    """
    Procesa una venta completa de forma atómica.

    `carrito` es una lista de diccionarios: [{'producto_id': 1, 'cantidad': 2}, ...]

    Si el stock de algún producto no alcanza, se lanza ValidationError y
    transaction.atomic se encarga de deshacer TODO lo realizado hasta ese
    punto (la venta creada, los detalles y cualquier descuento de stock
    ya aplicado), evitando que el stock disminuya para una venta fallida.
    """
    if not carrito:
        raise ValidationError('El carrito de venta está vacío.')

    if tipo_comprobante == Venta.TipoComprobante.FACTURA:
        if not cliente_documento or not cliente_nombre or cliente_nombre.strip().lower() == 'cliente varios':
            raise ValidationError('Para emitir una Factura es obligatorio ingresar el RUC y Razón Social del cliente.')

    venta = Venta.objects.create(
        numero_comprobante=_generar_numero_comprobante(tipo_comprobante),
        tipo_comprobante=tipo_comprobante,
        metodo_pago=metodo_pago,
        cliente_nombre=cliente_nombre or 'Cliente varios',
        cliente_documento=cliente_documento,
        cliente_email=cliente_email,
        pos_operador=pos_operador,
        pos_tipo_tarjeta=pos_tipo_tarjeta,
        pos_numero_autorizacion=pos_numero_autorizacion,
        pos_ultimos_digitos=pos_ultimos_digitos,
        cajero=cajero,
        subtotal=Decimal('0.00'),
        igv=Decimal('0.00'),
        total=Decimal('0.00'),
    )

    total_venta = Decimal('0.00')

    for linea in carrito:
        producto = Producto.objects.select_related('categoria').get(pk=linea['producto_id'])
        cantidad = int(linea['cantidad'])

        if cantidad <= 0:
            raise ValidationError(f'La cantidad de "{producto.nombre}" debe ser mayor a cero.')

        # Descuenta el stock; si no alcanza, lanza ValidationError y
        # transaction.atomic revierte toda la venta.
        registrar_movimiento(
            producto=producto,
            tipo_movimiento=MovimientoInventario.TipoMovimiento.SALIDA,
            cantidad=cantidad,
            usuario=cajero,
            motivo=f'Venta {venta.numero_comprobante}',
        )

        subtotal_linea = (producto.precio_venta * cantidad).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        DetalleVenta.objects.create(
            venta=venta,
            producto=producto,
            cantidad=cantidad,
            precio_unitario=producto.precio_venta,
            subtotal_linea=subtotal_linea,
        )

        total_venta += subtotal_linea

    # El precio de venta se asume con IGV incluido (práctica común en minimarkets).
    tasa_igv = Decimal(str(settings.IGV_PORCENTAJE))
    valor_venta = (total_venta / (Decimal('1') + tasa_igv)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    igv_calculado = total_venta - valor_venta

    venta.subtotal = valor_venta
    venta.igv = igv_calculado
    venta.total = total_venta
    venta.save(update_fields=['subtotal', 'igv', 'total'])

    # Intentar emitir comprobante electrónico (se hace dentro de la misma petición)
    if tipo_comprobante in [Venta.TipoComprobante.BOLETA, Venta.TipoComprobante.FACTURA]:
        try:
            procesar_emision_electronica(venta)
        except Exception as e:
            import traceback
            print("ERROR IN procesar_emision_electronica:", e)
            traceback.print_exc()
            # Si falla de forma catastrófica (ej. error de sintaxis), no revertimos la venta de Django.
            # Se registrará como Error en el admin o logs.
            pass

    return venta


@transaction.atomic
def anular_venta(*, venta: Venta, usuario, motivo: str):
    """Anula una venta y repone el stock de todos sus productos, de forma atómica."""
    if venta.estado == Venta.Estado.ANULADA:
        raise ValidationError('Esta venta ya se encuentra anulada.')

    for detalle in venta.detalles.select_related('producto').all():
        registrar_movimiento(
            producto=detalle.producto,
            tipo_movimiento=MovimientoInventario.TipoMovimiento.ENTRADA,
            cantidad=detalle.cantidad,
            usuario=usuario,
            motivo=f'Anulación de venta {venta.numero_comprobante}',
        )

    venta.estado = Venta.Estado.ANULADA
    venta.motivo_anulacion = motivo
    venta.save(update_fields=['estado', 'motivo_anulacion'])
    return venta
