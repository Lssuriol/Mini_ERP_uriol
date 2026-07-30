from django.contrib import admin

from .models import ComprobanteElectronico

@admin.register(ComprobanteElectronico)
class ComprobanteElectronicoAdmin(admin.ModelAdmin):
    list_display = ('venta', 'estado_emision', 'serie', 'correlativo', 'fecha_creacion')
    list_filter = ('estado_emision', 'correo_enviado')
    search_fields = ('venta__numero_comprobante', 'serie', 'codigo_respuesta')
    readonly_fields = ('external_id', 'errores_api', 'motivo_rechazo', 'hash_sunat', 'codigo_respuesta', 'enlace_pdf', 'enlace_xml', 'enlace_cdr')
