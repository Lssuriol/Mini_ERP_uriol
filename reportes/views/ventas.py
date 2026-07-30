"""Reportes de ventas diarias y estadísticas generales del minimarket."""

import datetime
import json
from datetime import timedelta

from django.db.models import Count, Sum, F, Q
from django.db.models.functions import Coalesce
from django.shortcuts import render
from django.utils import timezone

from almacen.models import Producto
from caja.models import DetalleVenta, Venta
from nucleo.decoradores import rol_requerido

ROLES_REPORTES = ('ADMINISTRADOR', 'CAJERO', 'INVENTARIO')


@rol_requerido(*ROLES_REPORTES)
def ventas_por_fecha(request):
    """
    Reporte de ventas en un rango de fechas.
    """
    hoy = timezone.localdate()
    fecha_inicio_str = request.GET.get('fecha_inicio', hoy.isoformat())
    fecha_fin_str = request.GET.get('fecha_fin', hoy.isoformat())
    
    try:
        fecha_inicio = datetime.date.fromisoformat(fecha_inicio_str)
        fecha_fin = datetime.date.fromisoformat(fecha_fin_str)
    except ValueError:
        fecha_inicio = hoy
        fecha_fin = hoy
        fecha_inicio_str = fecha_inicio.isoformat()
        fecha_fin_str = fecha_fin.isoformat()

    ventas_rango = (
        Venta.objects.filter(
            fecha_creacion__date__gte=fecha_inicio,
            fecha_creacion__date__lte=fecha_fin
        )
        .select_related('cajero')
        .prefetch_related('detalles__producto')
        .order_by('-fecha_creacion')
    )

    resumen = ventas_rango.filter(estado=Venta.Estado.COMPLETADA).aggregate(
        total_vendido=Sum('total'),
        total_ventas=Count('id'),
    )

    contexto = {
        'ventas_rango': ventas_rango,
        'fecha_inicio': fecha_inicio_str,
        'fecha_fin': fecha_fin_str,
        'total_vendido': resumen['total_vendido'] or 0,
        'total_ventas': resumen['total_ventas'] or 0,
    }
    return render(request, 'reportes/ventas_diarias.html', contexto)


@rol_requerido(*ROLES_REPORTES)
def estadisticas_ventas(request):
    """
    Estadísticas generales: KPIs históricos, gráficos de tendencia,
    productos más vendidos, distribución por categoría y método de pago.

    Todo el cálculo se apoya en annotate/aggregate a nivel de base de
    datos, evitando iterar en Python sobre miles de registros.
    """
    hoy = timezone.localdate()
    ventas_completadas = Venta.objects.filter(estado=Venta.Estado.COMPLETADA)

    # ========== KPIs HISTÓRICOS ==========
    resumen_global = ventas_completadas.aggregate(
        total_vendido=Sum('total'),
        cantidad_ventas=Count('id'),
    )
    total_vendido_global = float(resumen_global['total_vendido'] or 0)
    cantidad_ventas_global = resumen_global['cantidad_ventas'] or 0
    ticket_promedio_global = round(total_vendido_global / cantidad_ventas_global, 2) if cantidad_ventas_global > 0 else 0

    # Ganancia estimada = sum(subtotal_linea) - sum(cantidad * producto.precio_compra)
    ganancia_qs = (
        DetalleVenta.objects.filter(venta__estado=Venta.Estado.COMPLETADA)
        .aggregate(
            ingresos=Sum('subtotal_linea'),
            costo=Sum(F('cantidad') * F('producto__precio_compra')),
        )
    )
    ingresos_totales = float(ganancia_qs['ingresos'] or 0)
    costo_total = float(ganancia_qs['costo'] or 0)
    ganancia_estimada = round(ingresos_totales - costo_total, 2)

    # ========== GRÁFICO: VENTAS ÚLTIMOS 30 DÍAS (línea) ==========
    ventas_30_dias_qs = (
        ventas_completadas
        .filter(fecha_creacion__date__gte=hoy - timedelta(days=29))
        .values('fecha_creacion__date')
        .annotate(total_dia=Sum('total'))
        .order_by('fecha_creacion__date')
    )
    ventas_por_fecha_30d = {str(v['fecha_creacion__date']): float(v['total_dia'] or 0) for v in ventas_30_dias_qs}
    etiquetas_30d = []
    datos_30d = []
    for i in range(29, -1, -1):
        dia = hoy - timedelta(days=i)
        etiquetas_30d.append(dia.strftime('%d/%m'))
        datos_30d.append(ventas_por_fecha_30d.get(str(dia), 0))

    # ========== GRÁFICO: MÉTODO DE PAGO (dona) ==========
    ventas_por_metodo_pago = (
        ventas_completadas
        .values('metodo_pago')
        .annotate(total=Sum('total'), cantidad=Count('id'))
        .order_by('-total')
    )
    metodo_pago_nombres_map = dict(Venta.MetodoPago.choices)
    metodo_etiquetas = [metodo_pago_nombres_map.get(m['metodo_pago'], m['metodo_pago']) for m in ventas_por_metodo_pago]
    metodo_datos = [float(m['total'] or 0) for m in ventas_por_metodo_pago]

    # ========== GRÁFICO: TOP 10 PRODUCTOS (barras horizontales) ==========
    productos_mas_vendidos = (
        DetalleVenta.objects.filter(venta__estado=Venta.Estado.COMPLETADA)
        .select_related('producto', 'producto__categoria')
        .values('producto__nombre', 'producto__categoria__nombre')
        .annotate(unidades_vendidas=Sum('cantidad'), monto_total=Sum('subtotal_linea'))
        .order_by('-unidades_vendidas')[:10]
    )
    top_productos_nombres = [p['producto__nombre'] for p in productos_mas_vendidos]
    top_productos_unidades = [p['unidades_vendidas'] for p in productos_mas_vendidos]

    # ========== GRÁFICO: VENTAS POR CATEGORÍA (dona) ==========
    ventas_por_categoria = (
        DetalleVenta.objects.filter(venta__estado=Venta.Estado.COMPLETADA)
        .values('producto__categoria__nombre')
        .annotate(monto=Sum('subtotal_linea'))
        .order_by('-monto')
    )
    categoria_etiquetas = [c['producto__categoria__nombre'] or 'Sin categoría' for c in ventas_por_categoria]
    categoria_datos = [float(c['monto'] or 0) for c in ventas_por_categoria]

    # ========== TABLA: PRODUCTOS MENOS VENDIDOS ==========
    productos_menos_vendidos = (
        Producto.objects.filter(activo=True)
        .select_related('categoria')
        .annotate(
            unidades_vendidas=Coalesce(
                Sum(
                    'detalles_venta__cantidad',
                    filter=Q(detalles_venta__venta__estado=Venta.Estado.COMPLETADA)
                ), 
                0
            )
        )
        .order_by('unidades_vendidas', 'nombre')[:10]
    )

    ventas_anuladas = Venta.objects.filter(estado=Venta.Estado.ANULADA)
    resumen_anuladas = ventas_anuladas.aggregate(
        total_anulado=Sum('total'),
        cantidad_anuladas=Count('id'),
    )
    total_anulado = float(resumen_anuladas['total_anulado'] or 0)
    cantidad_anuladas = resumen_anuladas['cantidad_anuladas'] or 0

    contexto = {
        # KPIs
        'total_vendido_global': total_vendido_global,
        'cantidad_ventas_global': cantidad_ventas_global,
        'ticket_promedio_global': ticket_promedio_global,
        'ganancia_estimada': ganancia_estimada,
        
        # Anuladas
        'total_anulado': total_anulado,
        'cantidad_anuladas': cantidad_anuladas,
        # Tablas
        'productos_mas_vendidos': productos_mas_vendidos,
        'productos_menos_vendidos': productos_menos_vendidos,
        'ventas_por_metodo_pago': ventas_por_metodo_pago,
        'metodo_pago_nombres_map': metodo_pago_nombres_map,
        # Datos para Chart.js
        'grafico_30d_etiquetas': json.dumps(etiquetas_30d),
        'grafico_30d_datos': json.dumps(datos_30d),
        'grafico_metodo_etiquetas': json.dumps(metodo_etiquetas),
        'grafico_metodo_datos': json.dumps(metodo_datos),
        'grafico_top_nombres': json.dumps(top_productos_nombres),
        'grafico_top_unidades': json.dumps(top_productos_unidades),
        'grafico_cat_etiquetas': json.dumps(categoria_etiquetas),
        'grafico_cat_datos': json.dumps(categoria_datos),
    }
    return render(request, 'reportes/estadisticas_ventas.html', contexto)

