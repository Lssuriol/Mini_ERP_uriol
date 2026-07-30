"""Vistas del historial de movimientos de inventario y registro manual."""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render

from nucleo.decoradores import rol_requerido

from ..forms import FormularioMovimientoManual
from ..models import MovimientoInventario
from ..servicios import registrar_movimiento

ROLES_ALMACEN = ('ADMINISTRADOR', 'INVENTARIO')


@rol_requerido(*ROLES_ALMACEN)
def lista_movimientos(request):
    """
    Historial de movimientos de inventario.

    Se usa select_related('producto', 'usuario') para traer en una sola
    consulta los datos relacionados y evitar el problema N+1 al listar.
    """
    movimientos = MovimientoInventario.objects.select_related('producto', 'usuario')[:200]
    return render(request, 'almacen/lista_movimientos.html', {'movimientos': movimientos})


@rol_requerido(*ROLES_ALMACEN)
def registrar_movimiento_manual(request):
    """Registra manualmente una entrada de mercadería, ajuste o merma."""
    if request.method == 'POST':
        formulario = FormularioMovimientoManual(request.POST)
        if formulario.is_valid():
            try:
                registrar_movimiento(
                    producto=formulario.cleaned_data['producto'],
                    tipo_movimiento=formulario.cleaned_data['tipo_movimiento'],
                    cantidad=formulario.cleaned_data['cantidad'],
                    usuario=request.user,
                    motivo=formulario.cleaned_data['motivo'],
                    numero_lote=formulario.cleaned_data.get('numero_lote', ''),
                    fecha_vencimiento=formulario.cleaned_data.get('fecha_vencimiento'),
                )
                messages.success(request, 'Movimiento de inventario registrado correctamente.')
                return redirect('almacen:lista_movimientos')
            except ValidationError as error:
                messages.error(request, error.message if hasattr(error, 'message') else str(error))
    else:
        formulario = FormularioMovimientoManual()

    return render(request, 'almacen/formulario_movimiento.html', {'formulario': formulario})
