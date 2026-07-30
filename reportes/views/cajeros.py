from django.shortcuts import render
from decimal import Decimal
from django.db.models import Count, Sum, Q
from django.db.models.functions import Coalesce
from usuarios.models import Usuario
from caja.models import Venta
from nucleo.decoradores import rol_requerido

@rol_requerido("ADMINISTRADOR", "CAJERO")
def reporte_cajeros(request):
    """
    Reporte de desempeño de cada cajero.
    Muestra la cantidad de ventas, monto total vendido, y promedio por venta.
    """
    cajeros = (
        Usuario.objects.filter(activo_en_sistema=True, rol__in=["ADMINISTRADOR", "CAJERO"])
        .annotate(
            total_ventas=Count(
                "ventas_realizadas", 
                filter=Q(ventas_realizadas__estado=Venta.Estado.COMPLETADA)
            ),
            monto_vendido=Coalesce(
                Sum(
                    "ventas_realizadas__total", 
                    filter=Q(ventas_realizadas__estado=Venta.Estado.COMPLETADA)
                ),
                Decimal('0.00')
            )
        )
        .order_by("-monto_vendido", "-total_ventas")
    )
    
    # Para el método de pago por cajero, se puede hacer en python para no complicar la query
    datos_cajeros = []
    for cajero in cajeros:
        # Calcular el promedio por venta (ticket promedio)
        ticket_promedio = 0
        if cajero.total_ventas > 0:
            ticket_promedio = cajero.monto_vendido / cajero.total_ventas
            
        # Agrupar por métodos de pago
        metodos = (
            Venta.objects.filter(cajero=cajero, estado=Venta.Estado.COMPLETADA)
            .values("metodo_pago")
            .annotate(cantidad=Count("id"), total=Sum("total"))
        )
        
        
        datos_cajeros.append({
            "cajero": cajero,
            "total_ventas": cajero.total_ventas,
            "monto_vendido": cajero.monto_vendido,
            "ticket_promedio": round(ticket_promedio, 2),
            "metodos_pago": metodos,
        })
        
    cajero_id = request.GET.get("cajero_id")
    ventas_historial_qs = Venta.objects.select_related("cajero").order_by("-fecha_creacion")
    if cajero_id:
        ventas_historial_qs = ventas_historial_qs.filter(cajero_id=cajero_id)
    
    ventas_historial = ventas_historial_qs[:50]
        
    metodo_pago_map = dict(Venta.MetodoPago.choices)
        
    return render(request, "reportes/reporte_cajeros.html", {
        "datos_cajeros": datos_cajeros,
        "metodo_pago_map": metodo_pago_map,
        "cajeros_lista": cajeros,
        "cajero_seleccionado": int(cajero_id) if cajero_id and cajero_id.isdigit() else '',
        "ventas_historial": ventas_historial,
    })
