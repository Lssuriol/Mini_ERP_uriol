from .dashboard import panel_principal
from .ventas import estadisticas_ventas, ventas_por_fecha
from .comprobantes import reporte_comprobantes
from .cajeros import reporte_cajeros
from .inventario import reporte_bajo_movimiento

__all__ = ['panel_principal', 'ventas_por_fecha', 'estadisticas_ventas', 'reporte_comprobantes', 'reporte_cajeros', 'reporte_bajo_movimiento']
