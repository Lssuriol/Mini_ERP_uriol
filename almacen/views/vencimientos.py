"""Vistas para el control de fechas de vencimiento de lotes."""

from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render
from nucleo.decoradores import rol_requerido
from ..models import Lote

ROLES_ALMACEN = ('ADMINISTRADOR', 'INVENTARIO')

@rol_requerido(*ROLES_ALMACEN)
def control_vencimientos(request):
    """
    Panel de control de vencimientos.
    Muestra los lotes activos con fecha de vencimiento clasificados en:
    - Vencidos (fecha < hoy)
    - Próximos a vencer (hoy <= fecha <= hoy + 30 días)
    - Vigentes (fecha > hoy + 30 días)
    """
    hoy = timezone.now().date()
    limite_proximos = hoy + timedelta(days=30)

    lotes_con_vencimiento = Lote.objects.filter(
        stock_actual__gt=0,
        fecha_vencimiento__isnull=False
    ).select_related('producto').order_by('fecha_vencimiento')

    vencidos = []
    proximos = []
    vigentes = []

    for lote in lotes_con_vencimiento:
        if lote.fecha_vencimiento < hoy:
            vencidos.append(lote)
        elif lote.fecha_vencimiento <= limite_proximos:
            proximos.append(lote)
        else:
            vigentes.append(lote)

    contexto = {
        'vencidos': vencidos,
        'proximos': proximos,
        'vigentes': vigentes,
    }
    return render(request, 'almacen/control_vencimientos.html', contexto)
