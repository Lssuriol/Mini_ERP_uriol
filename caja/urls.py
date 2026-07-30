"""URLs del módulo Caja."""

from django.urls import path

from . import views

app_name = 'caja'

urlpatterns = [
    path('punto-de-venta/', views.punto_venta, name='punto_venta'),
    path('api/productos/', views.buscar_productos_json, name='buscar_productos_json'),
    path('api/registrar-venta/', views.registrar_venta, name='registrar_venta'),
    path('api/consultar-documento/', views.consultar_documento, name='consultar_documento'),

    path('ventas/', views.lista_ventas, name='lista_ventas'),
    path('ventas/<int:venta_id>/', views.detalle_venta, name='detalle_venta'),
    path('ventas/<int:venta_id>/anular/', views.anular_venta, name='anular_venta'),
]
