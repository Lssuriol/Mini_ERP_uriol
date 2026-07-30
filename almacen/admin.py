from django.contrib import admin

from .models import Categoria, MovimientoInventario, Producto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activa')
    search_fields = ('nombre',)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'categoria', 'precio_venta', 'stock_actual', 'activo')
    list_filter = ('categoria', 'activo')
    search_fields = ('codigo', 'nombre')
    list_select_related = ('categoria',)


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ('producto', 'tipo_movimiento', 'cantidad', 'stock_resultante', 'usuario', 'fecha_creacion')
    list_filter = ('tipo_movimiento',)
    list_select_related = ('producto', 'usuario')
