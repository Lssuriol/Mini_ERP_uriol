from django.shortcuts import render
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta
import datetime

from almacen.models import Producto
from caja.models import Venta
from nucleo.decoradores import rol_requerido

@rol_requerido("ADMINISTRADOR", "INVENTARIO")
def reporte_bajo_movimiento(request):
    """
    Reporte de productos con poco o nulo movimiento en un rango de fechas.
    """
    hoy = timezone.localdate()
    fecha_inicio_str = request.GET.get("fecha_inicio", (hoy - timedelta(days=30)).isoformat())
    fecha_fin_str = request.GET.get("fecha_fin", hoy.isoformat())
    try:
        umbral = int(request.GET.get("umbral", 5))
    except ValueError:
        umbral = 5

    try:
        fecha_inicio = datetime.date.fromisoformat(fecha_inicio_str)
        fecha_fin = datetime.date.fromisoformat(fecha_fin_str)
    except ValueError:
        fecha_inicio = hoy - timedelta(days=30)
        fecha_fin = hoy
        fecha_inicio_str = fecha_inicio.isoformat()
        fecha_fin_str = fecha_fin.isoformat()
        
    productos = (
        Producto.objects.filter(activo=True)
        .select_related("categoria")
        .annotate(
            unidades_vendidas=Coalesce(
                Sum(
                    "detalles_venta__cantidad",
                    filter=Q(
                        detalles_venta__venta__estado=Venta.Estado.COMPLETADA,
                        detalles_venta__venta__fecha_creacion__date__gte=fecha_inicio,
                        detalles_venta__venta__fecha_creacion__date__lte=fecha_fin
                    )
                ), 
                0
            )
        )
        .filter(unidades_vendidas__lte=umbral)
        .order_by("unidades_vendidas", "nombre")
    )
    
    contexto = {
        "productos": productos,
        "fecha_inicio": fecha_inicio_str,
        "fecha_fin": fecha_fin_str,
        "umbral": umbral,
    }
    
    return render(request, "reportes/bajo_movimiento.html", contexto)
