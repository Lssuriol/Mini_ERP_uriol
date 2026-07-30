"""Panel principal del ERP: resumen ejecutivo visible al iniciar sesión."""

import json
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count, F, Sum
from django.shortcuts import render
from django.utils import timezone

from almacen.models import Producto
from caja.models import DetalleVenta, Venta


@login_required
def panel_principal(request):
    """
    Panel principal con indicadores clave (KPIs) del minimarket.

    Las consultas usan select_related/prefetch_related y agregaciones a
    nivel de base de datos para evitar traer objetos innecesarios a Python.
    """
    hoy = timezone.localdate()

    # --- KPIs del día ---
    ventas_hoy = Venta.objects.filter(fecha_creacion__date=hoy, estado=Venta.Estado.COMPLETADA)
    resumen_hoy = ventas_hoy.aggregate(total_vendido=Sum('total'), cantidad_ventas=Count('id'))
    total_vendido_hoy = resumen_hoy['total_vendido'] or 0
    cantidad_ventas_hoy = resumen_hoy['cantidad_ventas'] or 0
    ticket_promedio = round(total_vendido_hoy / cantidad_ventas_hoy, 2) if cantidad_ventas_hoy > 0 else 0

    # --- Productos con stock bajo ---
    productos_stock_bajo = (
        Producto.objects.select_related('categoria')
        .filter(activo=True, stock_actual__lte=F('stock_minimo'))
        .order_by('stock_actual')[:8]
    )

    # --- Productos más vendidos (histórico) ---
    productos_mas_vendidos = (
        DetalleVenta.objects.filter(venta__estado=Venta.Estado.COMPLETADA)
        .select_related('producto')
        .values('producto__nombre')
        .annotate(unidades_vendidas=Sum('cantidad'))
        .order_by('-unidades_vendidas')[:5]
    )

    # --- Últimas ventas ---
    ultimas_ventas = (
        Venta.objects.select_related('cajero')
        .prefetch_related('detalles__producto')
        .order_by('-fecha_creacion')[:6]
    )

    # --- Ventas de los últimos 7 días (para gráfico de barras) ---
    dias_semana_es = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    ventas_7_dias_qs = (
        Venta.objects.filter(
            fecha_creacion__date__gte=hoy - timedelta(days=6),
            estado=Venta.Estado.COMPLETADA,
        )
        .values('fecha_creacion__date')
        .annotate(total_dia=Sum('total'), cantidad_dia=Count('id'))
        .order_by('fecha_creacion__date')
    )
    ventas_por_fecha = {str(v['fecha_creacion__date']): float(v['total_dia'] or 0) for v in ventas_7_dias_qs}
    etiquetas_7d = []
    datos_7d = []
    for i in range(6, -1, -1):
        dia = hoy - timedelta(days=i)
        etiquetas_7d.append(dias_semana_es[dia.weekday()] + ' ' + dia.strftime('%d/%m'))
        datos_7d.append(ventas_por_fecha.get(str(dia), 0))

    contexto = {
        'total_vendido_hoy': total_vendido_hoy,
        'cantidad_ventas_hoy': cantidad_ventas_hoy,
        'ticket_promedio': ticket_promedio,
        'productos_stock_bajo': productos_stock_bajo,
        'productos_mas_vendidos': productos_mas_vendidos,
        'ultimas_ventas': ultimas_ventas,
        'total_productos_activos': Producto.objects.filter(activo=True).count(),
        # Datos para Chart.js (serializados como JSON)
        'grafico_7d_etiquetas': json.dumps(etiquetas_7d),
        'grafico_7d_datos': json.dumps(datos_7d),
    }
    return render(request, 'reportes/panel_principal.html', contexto)

