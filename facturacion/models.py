"""
Modelos del módulo de facturación electrónica.

Este módulo almacena el estado de los comprobantes electrónicos enviados
a la SUNAT (o a un OSE/PSE) y almacena los enlaces a los archivos PDF, XML y CDR.
"""
import uuid
from django.db import models
from django.utils import timezone
from nucleo.models import ModeloBase
from caja.models import Venta

class ComprobanteElectronico(ModeloBase):
    """
    Representa el estado de emisión electrónica de una Venta.
    Almacena los enlaces devueltos por la API de facturación y errores.
    """
    class EstadoEmision(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        ENVIANDO = 'ENVIANDO', 'Enviando'
        ACEPTADA = 'ACEPTADA', 'Aceptada por SUNAT'
        RECHAZADA = 'RECHAZADA', 'Rechazada por SUNAT'
        ERROR = 'ERROR', 'Error de comunicación'

    venta = models.OneToOneField(Venta, on_delete=models.CASCADE, related_name='comprobante_electronico')
    external_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, help_text="ID único para idempotencia")
    
    estado_emision = models.CharField(max_length=20, choices=EstadoEmision.choices, default=EstadoEmision.PENDIENTE)
    
    serie = models.CharField(max_length=4, blank=True)
    correlativo = models.IntegerField(null=True, blank=True)
    
    # URLs retornadas por la API (Nubefact, etc)
    enlace_pdf = models.URLField(max_length=500, blank=True)
    enlace_xml = models.URLField(max_length=500, blank=True)
    enlace_cdr = models.URLField(max_length=500, blank=True)
    hash_sunat = models.CharField(max_length=200, blank=True)
    
    # Respuestas de error
    codigo_respuesta = models.CharField(max_length=50, blank=True)
    motivo_rechazo = models.TextField(blank=True)
    errores_api = models.TextField(blank=True, help_text="Raw error logs for debugging")
    
    # Control de correos
    correo_enviado = models.BooleanField(default=False)
    fecha_envio_correo = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.venta.numero_comprobante} - {self.get_estado_emision_display()}"
    
    def marcar_como_enviado_por_correo(self):
        self.correo_enviado = True
        self.fecha_envio_correo = timezone.now()
        self.save(update_fields=['correo_enviado', 'fecha_envio_correo'])
