import json
import urllib.request
import urllib.error
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from caja.models import Venta

# Constantes de Nubefact
NUBEFACT_URL = getattr(settings, 'NUBEFACT_URL', '')
NUBEFACT_TOKEN = getattr(settings, 'NUBEFACT_TOKEN', '')

class NubefactAdapter:
    """Adaptador para interactuar con la API de Nubefact."""

    def __init__(self):
        self.url = NUBEFACT_URL
        self.token = NUBEFACT_TOKEN

    def _preparar_payload(self, comprobante_electronico):
        """Convierte la Venta de Django al formato JSON esperado por Nubefact."""
        venta = comprobante_electronico.venta
        
        # Mapeo de tipos
        # 1 = Factura, 2 = Boleta
        tipo_comprobante = 1 if venta.tipo_comprobante == Venta.TipoComprobante.FACTURA else 2
        
        serie, numero = venta.numero_comprobante.split('-')
        
        # Tipo documento cliente: 6 = RUC, 1 = DNI, - = Varios
        tipo_doc_cliente = 6 if tipo_comprobante == 1 else (1 if venta.cliente_documento else '-')
        
        items = []
        for detalle in venta.detalles.select_related('producto').all():
            items.append({
                "unidad_de_medida": "NIU",
                "codigo": detalle.producto.codigo,
                "descripcion": detalle.producto.nombre,
                "cantidad": str(detalle.cantidad),
                "valor_unitario": str((detalle.precio_unitario / Decimal('1.18')).quantize(Decimal('0.0001'))),
                "precio_unitario": str(detalle.precio_unitario),
                "descuento": "",
                "subtotal": str((detalle.subtotal_linea / Decimal('1.18')).quantize(Decimal('0.01'))),
                "tipo_de_igv": "1",
                "igv": str((detalle.subtotal_linea - (detalle.subtotal_linea / Decimal('1.18'))).quantize(Decimal('0.01'))),
                "total": str(detalle.subtotal_linea),
                "anticipo_regularizacion": "false",
                "anticipo_documento_serie": "",
                "anticipo_documento_numero": ""
            })

        payload = {
            "operacion": "generar_comprobante",
            "tipo_de_comprobante": tipo_comprobante,
            "serie": serie,
            "numero": int(numero),
            "sunat_transaction": "1",
            "cliente_tipo_de_documento": tipo_doc_cliente,
            "cliente_numero_de_documento": venta.cliente_documento or "00000000",
            "cliente_denominacion": venta.cliente_nombre or "CLIENTE VARIOS",
            "cliente_direccion": "",
            "cliente_email": venta.cliente_email or "",
            "cliente_email_1": "",
            "cliente_email_2": "",
            "fecha_de_emision": timezone.localtime(venta.fecha_creacion).strftime('%d-%m-%Y'),
            "fecha_de_vencimiento": "",
            "moneda": "1",
            "tipo_de_cambio": "",
            "porcentaje_de_igv": "18.00",
            "descuento_global": "",
            "total_descuento": "",
            "total_anticipo": "",
            "total_gravada": str(venta.subtotal),
            "total_inafecta": "",
            "total_exonerada": "",
            "total_igv": str(venta.igv),
            "total_gratuita": "",
            "total_otros_cargos": "",
            "total": str(venta.total),
            "percepcion_tipo": "",
            "percepcion_base_imponible": "",
            "total_percepcion": "",
            "total_incluido_percepcion": "",
            "detraccion": "false",
            "observaciones": "",
            "documento_que_se_modifica_tipo": "",
            "documento_que_se_modifica_serie": "",
            "documento_que_se_modifica_numero": "",
            "tipo_de_nota_de_credito": "",
            "tipo_de_nota_de_debito": "",
            "enviar_automaticamente_a_la_sunat": "true",
            "enviar_automaticamente_al_cliente": "false",
            "codigo_unico": "",
            "condiciones_de_pago": "",
            "medio_de_pago": "",
            "items": items
        }
        return payload

    def consultar_comprobante(self, serie, numero, tipo_comprobante):
        """Consulta en Nubefact si el comprobante ya existe."""
        tipo_nubefact = 1 if tipo_comprobante == Venta.TipoComprobante.FACTURA else 2
        
        payload = {
            "operacion": "consultar_comprobante",
            "tipo_de_comprobante": tipo_nubefact,
            "serie": serie,
            "numero": int(numero)
        }
        
        return self._ejecutar_peticion(payload)

    def emitir_comprobante(self, comprobante_electronico):
        """
        Emite el comprobante y maneja idempotencia.
        Primero consulta si ya existe para no duplicar.
        """
        if not self.token:
            # Modo Simulado (Mock) si no hay token configurado
            return self._simular_respuesta(comprobante_electronico)

        venta = comprobante_electronico.venta
        serie, numero = venta.numero_comprobante.split('-')
        
        # 1. Idempotencia: Consultar si ya fue emitido
        consulta_resp = self.consultar_comprobante(serie, numero, venta.tipo_comprobante)
        
        if consulta_resp.get('exito') and 'enlace' in consulta_resp.get('data', {}):
            # Ya existía y está aceptado
            return consulta_resp
            
        # 2. Si no existe, enviarlo
        payload = self._preparar_payload(comprobante_electronico)
        return self._ejecutar_peticion(payload)

    def _ejecutar_peticion(self, payload):
        """Ejecuta la petición HTTP a la API de Nubefact."""
        headers = {
            'Authorization': f'Token token="{self.token}"',
            'Content-Type': 'application/json',
        }
        
        req = urllib.request.Request(self.url, data=json.dumps(payload).encode('utf-8'), headers=headers)
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                resp_data = json.loads(response.read().decode('utf-8'))
                
                # Nubefact retorna errors si hubo rechazo
                if 'errors' in resp_data:
                    return {'exito': False, 'data': resp_data, 'error': resp_data['errors']}
                    
                return {'exito': True, 'data': resp_data}
                
        except urllib.error.HTTPError as e:
            try:
                error_data = json.loads(e.read().decode('utf-8'))
                return {'exito': False, 'data': error_data, 'error': error_data.get('errors', str(e))}
            except:
                return {'exito': False, 'data': None, 'error': str(e)}
        except Exception as e:
            return {'exito': False, 'data': None, 'error': f"Error de red: {str(e)}"}

    def _simular_respuesta(self, comprobante_electronico):
        """Simula una respuesta exitosa de Nubefact para desarrollo."""
        import time
        time.sleep(1) # Simular latencia de red
        
        venta = comprobante_electronico.venta
        serie, numero = venta.numero_comprobante.split('-')
        
        return {
            'exito': True,
            'data': {
                'tipo_de_comprobante': 1 if venta.tipo_comprobante == Venta.TipoComprobante.FACTURA else 2,
                'serie': serie,
                'numero': numero,
                'enlace': f'https://demo.nubefact.com/pdf/{serie}-{numero}.pdf',
                'enlace_del_xml': f'https://demo.nubefact.com/xml/{serie}-{numero}.xml',
                'enlace_del_cdr': f'https://demo.nubefact.com/cdr/{serie}-{numero}.zip',
                'sunat_hash': 'xyz123hashsimulado=',
                'aceptada_por_sunat': True,
                'sunat_description': 'Aceptado simulado',
            }
        }
