"""URLs del módulo Reportes."""

from django.urls import path

from . import views

app_name = 'reportes'

urlpatterns = [
    path('', views.panel_principal, name='panel_principal'),
    path('ventas-diarias/', views.ventas_por_fecha, name='ventas_diarias'),
    path('estadisticas/', views.estadisticas_ventas, name='estadisticas_ventas'),
    path('comprobantes/', views.reporte_comprobantes, name='reporte_comprobantes'),
    path('cajeros/', views.reporte_cajeros, name='reporte_cajeros'),
    path('bajo-movimiento/', views.reporte_bajo_movimiento, name='reporte_bajo_movimiento'),
]
