from django.shortcuts import render
from django.core.paginator import Paginator
from facturacion.models import ComprobanteElectronico
from nucleo.decoradores import rol_requerido

@rol_requerido("ADMINISTRADOR", "CAJERO", "INVENTARIO")
def reporte_comprobantes(request):
    """
    Muestra el historial de boletas y facturas emitidas, incluyendo 
    su estado en SUNAT (aceptado, rechazado, pendiente).
    """
    comprobantes_qs = ComprobanteElectronico.objects.select_related(
        "venta", "venta__cajero"
    ).order_by("-fecha_creacion")
    
    estado = request.GET.get("estado")
    if estado:
        comprobantes_qs = comprobantes_qs.filter(estado_emision=estado)
        
    paginador = Paginator(comprobantes_qs, 20)
    numero_pagina = request.GET.get("page")
    page_obj = paginador.get_page(numero_pagina)
    
    contexto = {
        "page_obj": page_obj,
        "estado_seleccionado": estado,
        "estados": ComprobanteElectronico.EstadoEmision.choices,
    }
    return render(request, "reportes/reporte_comprobantes.html", contexto)

