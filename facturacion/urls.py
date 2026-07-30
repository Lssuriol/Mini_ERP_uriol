from django.urls import path
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from caja.models import Venta
from facturacion.servicios import procesar_emision_electronica, enviar_correo_comprobante
from facturacion.models import ComprobanteElectronico
from nucleo.decoradores import rol_requerido

app_name = 'facturacion'

@require_POST
@rol_requerido('ADMINISTRADOR', 'CAJERO')
def reintentar_emision(request, venta_id):
    venta = get_object_or_404(Venta, pk=venta_id)
    
    try:
        comprobante = procesar_emision_electronica(venta)
        if not comprobante:
            return JsonResponse({'exito': False, 'mensaje': 'Este tipo de comprobante no se envía a SUNAT.'})
            
        return JsonResponse({
            'exito': comprobante.estado_emision == 'ACEPTADA',
            'estado': comprobante.estado_emision,
            'mensaje': f'Estado actual: {comprobante.get_estado_emision_display()}',
        })
    except Exception as e:
        return JsonResponse({'exito': False, 'mensaje': str(e)})


@require_POST
@rol_requerido('ADMINISTRADOR', 'CAJERO')
def enviar_correo_view(request, venta_id):
    """Envía el comprobante electrónico por correo al cliente via Brevo API."""
    venta = get_object_or_404(Venta, pk=venta_id)
    
    try:
        comprobante = venta.comprobante_electronico
    except ComprobanteElectronico.DoesNotExist:
        return JsonResponse({'exito': False, 'mensaje': 'Esta venta no tiene comprobante electrónico.'})
    
    # Permitir reenvío si ya fue enviado
    forzar = comprobante.correo_enviado
    resultado = enviar_correo_comprobante(comprobante, forzar_reenvio=forzar)
    return JsonResponse(resultado)


urlpatterns = [
    path('api/reintentar/<int:venta_id>/', reintentar_emision, name='reintentar_emision'),
    path('api/enviar-correo/<int:venta_id>/', enviar_correo_view, name='enviar_correo'),
]
