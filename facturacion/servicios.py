import urllib.request
import urllib.error
import json
import base64
from django.conf import settings
from django.template.loader import render_to_string
from facturacion.models import ComprobanteElectronico
from facturacion.proveedores import NubefactAdapter
import logging

logger = logging.getLogger(__name__)

def procesar_emision_electronica(venta):
    """
    Función principal llamada desde Caja al terminar una venta.
    Crea el ComprobanteElectronico (si no existe) y llama a la API.
    """
    # No emitir Notas de Venta a SUNAT
    if venta.tipo_comprobante == 'NOTA_VENTA':
        return None

    comprobante, _ = ComprobanteElectronico.objects.get_or_create(
        venta=venta,
        defaults={'estado_emision': ComprobanteElectronico.EstadoEmision.PENDIENTE}
    )
    
    if comprobante.estado_emision == ComprobanteElectronico.EstadoEmision.ACEPTADA:
        return comprobante # Ya fue procesado
        
    comprobante.estado_emision = ComprobanteElectronico.EstadoEmision.ENVIANDO
    comprobante.save(update_fields=['estado_emision'])
    
    adaptador = NubefactAdapter()
    resultado = adaptador.emitir_comprobante(comprobante)
    
    if resultado['exito']:
        data = resultado['data']
        comprobante.estado_emision = ComprobanteElectronico.EstadoEmision.ACEPTADA
        comprobante.serie = data.get('serie') or ''
        comprobante.correlativo = data.get('numero')
        comprobante.enlace_pdf = data.get('enlace') or ''
        comprobante.enlace_xml = data.get('enlace_del_xml') or ''
        comprobante.enlace_cdr = data.get('enlace_del_cdr') or ''
        comprobante.hash_sunat = data.get('sunat_hash') or ''
        comprobante.codigo_respuesta = '0'
        comprobante.motivo_rechazo = data.get('sunat_description') or ''
        comprobante.errores_api = ''
    else:
        # Error o Rechazo
        errores = resultado.get('error', 'Error desconocido')
        
        # Clasificar si es rechazo de SUNAT o error de conexión
        if isinstance(errores, str) and 'Error de red' in errores:
            comprobante.estado_emision = ComprobanteElectronico.EstadoEmision.ERROR
            comprobante.motivo_rechazo = "Problemas de conexión con la API o SUNAT."
        else:
            comprobante.estado_emision = ComprobanteElectronico.EstadoEmision.RECHAZADA
            comprobante.motivo_rechazo = str(errores)
            
        comprobante.errores_api = str(resultado.get('data', ''))
        
    comprobante.save()
    
    # Enviar correo si fue aceptada y el cliente tiene correo
    if comprobante.estado_emision == ComprobanteElectronico.EstadoEmision.ACEPTADA and venta.cliente_email:
        try:
            enviar_correo_comprobante(comprobante)
        except Exception as e:
            logger.error(f"Error al enviar correo tras emitir comprobante: {e}")
        
    return comprobante


# ---------------------------------------------------------------------------
# Envío de correo con Brevo API
# ---------------------------------------------------------------------------

def _construir_html_correo(comprobante):
    """Genera el HTML del correo usando el template de Django."""
    venta = comprobante.venta
    contexto = {
        'nombre_empresa': getattr(settings, 'NOMBRE_EMPRESA', 'Empresa'),
        'ruc_empresa': getattr(settings, 'RUC_EMPRESA', ''),
        'direccion_empresa': getattr(settings, 'DIRECCION_EMPRESA', ''),
        'cliente_nombre': venta.cliente_nombre or 'Cliente',
        'cliente_documento': venta.cliente_documento or '',
        'fecha_venta': venta.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
        'tipo_comprobante': venta.get_tipo_comprobante_display(),
        'numero_comprobante': venta.numero_comprobante,
        'subtotal': f'{venta.subtotal:.2f}',
        'igv': f'{venta.igv:.2f}',
        'total': f'{venta.total:.2f}',
        'enlace_pdf': comprobante.enlace_pdf,
        'enlace_xml': comprobante.enlace_xml,
    }
    return render_to_string('facturacion/email_comprobante.html', contexto)


def enviar_correo_comprobante(comprobante, forzar_reenvio=False):
    """
    Envía el comprobante electrónico por correo al cliente usando la API de Brevo.
    
    Descarga el PDF y XML de Nubefact, los codifica en base64 y los envía
    como adjuntos via POST https://api.brevo.com/v3/smtp/email.
    
    Args:
        comprobante: instancia de ComprobanteElectronico
        forzar_reenvio: si True, reenvía aunque ya se haya enviado antes
        
    Returns:
        dict con claves 'exito' (bool) y 'mensaje' (str)
    """
    venta = comprobante.venta
    
    # Validaciones previas
    if not venta.cliente_email:
        return {'exito': False, 'mensaje': 'La venta no tiene correo del cliente registrado.'}
    
    if comprobante.estado_emision != ComprobanteElectronico.EstadoEmision.ACEPTADA:
        return {'exito': False, 'mensaje': 'El comprobante no ha sido aceptado por SUNAT.'}
    
    if comprobante.correo_enviado and not forzar_reenvio:
        return {'exito': True, 'mensaje': 'El correo ya fue enviado anteriormente.'}
    
    api_key = getattr(settings, 'BREVO_API_KEY', '')
    if not api_key:
        return {'exito': False, 'mensaje': 'La API Key de Brevo no está configurada.'}
    
    # Construir el payload para Brevo
    sender_email = getattr(settings, 'BREVO_SENDER_EMAIL', 'facturacion@uriol.com')
    sender_name = getattr(settings, 'BREVO_SENDER_NAME', 'Uriol Distribuciones SAC')
    
    payload = {
        'sender': {
            'name': sender_name,
            'email': sender_email,
        },
        'to': [{
            'email': venta.cliente_email,
            'name': venta.cliente_nombre or 'Cliente',
        }],
        'subject': f'Comprobante Electrónico {venta.numero_comprobante} - {sender_name}',
        'htmlContent': _construir_html_correo(comprobante),
    }
    
    # Enviar via API REST de Brevo
    url_brevo = 'https://api.brevo.com/v3/smtp/email'
    headers = {
        'api-key': api_key,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url_brevo, data=data, headers=headers, method='POST')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            status = response.status
            resp_body = response.read().decode('utf-8')
        
        if status in (200, 201):
            comprobante.marcar_como_enviado_por_correo()
            logger.info(f"Correo enviado exitosamente para {venta.numero_comprobante} a {venta.cliente_email}")
            return {'exito': True, 'mensaje': f'Correo enviado correctamente a {venta.cliente_email}.'}
        else:
            error_msg = f'Brevo respondió con estado {status}: {resp_body}'
            logger.error(error_msg)
            return {'exito': False, 'mensaje': error_msg}
            
    except urllib.error.HTTPError as e:
        error_body = ''
        try:
            error_body = e.read().decode('utf-8')
        except Exception:
            pass
        error_msg = f'Error HTTP {e.code} de Brevo: {error_body}'
        logger.error(error_msg)
        return {'exito': False, 'mensaje': error_msg}
    except urllib.error.URLError as e:
        error_msg = f'Error de conexión con Brevo: {e.reason}'
        logger.error(error_msg)
        return {'exito': False, 'mensaje': error_msg}
    except Exception as e:
        error_msg = f'Error inesperado al enviar correo: {str(e)}'
        logger.error(error_msg)
        return {'exito': False, 'mensaje': error_msg}
