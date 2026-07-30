"""Vistas de control de caja: anulación de comprobantes."""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from nucleo.decoradores import rol_requerido

from ..forms import FormularioAnulacionVenta
from ..models import Venta
from ..servicios import anular_venta as anular_venta_servicio

ROLES_CAJA = ('ADMINISTRADOR', 'CAJERO')


@rol_requerido(*ROLES_CAJA)
def anular_venta(request, venta_id):
    """Anula una venta y repone el stock de sus productos automáticamente."""
    venta = get_object_or_404(Venta, pk=venta_id)

    if venta.estado == Venta.Estado.ANULADA:
        messages.warning(request, 'Esta venta ya se encuentra anulada.')
        return redirect('caja:detalle_venta', venta_id=venta.id)

    if request.method == 'POST':
        formulario = FormularioAnulacionVenta(request.POST)
        if formulario.is_valid():
            try:
                anular_venta_servicio(
                    venta=venta,
                    usuario=request.user,
                    motivo=formulario.cleaned_data['motivo_anulacion'],
                )
                messages.success(request, f'Venta {venta.numero_comprobante} anulada. El stock fue repuesto.')
                return redirect('caja:detalle_venta', venta_id=venta.id)
            except ValidationError as error:
                messages.error(request, str(error))
    else:
        formulario = FormularioAnulacionVenta()

    return render(request, 'caja/formulario_anulacion.html', {'formulario': formulario, 'venta': venta})
