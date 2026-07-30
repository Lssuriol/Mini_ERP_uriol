"""
Servicios de dominio del módulo Almacén.

Centraliza la lógica de actualización de stock para que tanto las vistas
de Almacén (entradas manuales, ajustes) como las vistas de Caja (salidas
por venta) compartan una única fuente de verdad al modificar el inventario.
"""

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import MovimientoInventario, Producto, Lote


@transaction.atomic
def registrar_movimiento(
    *, 
    producto: Producto, 
    tipo_movimiento: str, 
    cantidad: int, 
    usuario, 
    motivo: str = '',
    numero_lote: str = '',
    fecha_vencimiento=None
):
    """
    Registra un movimiento de inventario y actualiza el stock del producto
    de forma atómica: si algo falla, ni el stock ni el movimiento se guardan.
    """
    if cantidad <= 0:
        raise ValidationError('La cantidad del movimiento debe ser mayor a cero.')

    # Bloquea la fila del producto para evitar condiciones de carrera
    producto_bloqueado = Producto.objects.select_for_update().get(pk=producto.pk)

    lote_creado = None

    if tipo_movimiento in (MovimientoInventario.TipoMovimiento.ENTRADA,):
        producto_bloqueado.stock_actual += cantidad
        
        # Crear lote si se especificó
        if numero_lote:
            lote_creado = Lote.objects.create(
                producto=producto_bloqueado,
                numero_lote=numero_lote,
                fecha_vencimiento=fecha_vencimiento,
                stock_inicial=cantidad,
                stock_actual=cantidad
            )
            
    else:  # SALIDA, AJUSTE (resta) o MERMA
        if producto_bloqueado.stock_actual < cantidad:
            raise ValidationError(
                f'Stock insuficiente para "{producto_bloqueado.nombre}". '
                f'Disponible: {producto_bloqueado.stock_actual}, solicitado: {cantidad}.'
            )
        producto_bloqueado.stock_actual -= cantidad
        
        # Descuento de lotes (Lógica FIFO)
        cantidad_restante = cantidad
        lotes_activos = Lote.objects.select_for_update().filter(
            producto=producto_bloqueado, 
            stock_actual__gt=0
        ).order_by('fecha_creacion')
        
        for lote in lotes_activos:
            if cantidad_restante <= 0:
                break
                
            if lote.stock_actual >= cantidad_restante:
                lote.stock_actual -= cantidad_restante
                lote.save(update_fields=['stock_actual'])
                cantidad_restante = 0
            else:
                cantidad_restante -= lote.stock_actual
                lote.stock_actual = 0
                lote.save(update_fields=['stock_actual'])

    producto_bloqueado.save(update_fields=['stock_actual'])

    movimiento = MovimientoInventario.objects.create(
        producto=producto_bloqueado,
        tipo_movimiento=tipo_movimiento,
        cantidad=cantidad,
        stock_resultante=producto_bloqueado.stock_actual,
        motivo=motivo,
        usuario=usuario,
        lote=lote_creado
    )

    return movimiento
