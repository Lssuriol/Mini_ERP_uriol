from django.contrib import admin

from .models import DetalleVenta, Venta


class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('numero_comprobante', 'tipo_comprobante', 'cajero', 'total', 'estado', 'fecha_creacion')
    list_filter = ('tipo_comprobante', 'estado', 'metodo_pago')
    search_fields = ('numero_comprobante', 'cliente_nombre')
    list_select_related = ('cajero',)
    inlines = [DetalleVentaInline]
