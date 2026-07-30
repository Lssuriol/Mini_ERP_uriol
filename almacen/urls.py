"""URLs del módulo Almacén."""

from django.urls import path

from . import views

app_name = 'almacen'

urlpatterns = [
    path('productos/', views.lista_productos, name='lista_productos'),
    path('productos/nuevo/', views.crear_producto, name='crear_producto'),
    path('productos/<int:producto_id>/editar/', views.editar_producto, name='editar_producto'),
    path('productos/<int:producto_id>/alternar-estado/', views.alternar_estado_producto, name='alternar_estado_producto'),
    path('productos/buscar-json/', views.buscar_productos_almacen_json, name='buscar_productos_json'),

    path('categorias/', views.lista_categorias, name='lista_categorias'),
    path('categorias/nueva/', views.crear_categoria, name='crear_categoria'),
    path('categorias/<int:categoria_id>/editar/', views.editar_categoria, name='editar_categoria'),

    path('movimientos/', views.lista_movimientos, name='lista_movimientos'),
    path('movimientos/nuevo/', views.registrar_movimiento_manual, name='registrar_movimiento_manual'),
]
