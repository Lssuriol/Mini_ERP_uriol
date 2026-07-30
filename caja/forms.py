"""Formularios del módulo de Caja."""

from django import forms

from .models import Venta


class FormularioDatosVenta(forms.Form):
    """Datos generales del comprobante, previos al armado del carrito en el POS."""

    tipo_comprobante = forms.ChoiceField(
        choices=Venta.TipoComprobante.choices,
        widget=forms.Select(attrs={'class': 'campo-formulario'}),
        label='Tipo de comprobante',
    )
    metodo_pago = forms.ChoiceField(
        choices=Venta.MetodoPago.choices,
        widget=forms.Select(attrs={'class': 'campo-formulario'}),
        label='Método de pago',
    )
    cliente_nombre = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'campo-formulario', 'placeholder': 'Cliente varios'}),
        label='Cliente',
    )
    cliente_documento = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'campo-formulario', 'placeholder': 'DNI / RUC'}),
        label='Documento del cliente',
    )
    cliente_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'campo-formulario', 'placeholder': 'ejemplo@correo.com'}),
        label='Correo (Opcional)',
    )


class FormularioAnulacionVenta(forms.Form):
    motivo_anulacion = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'campo-formulario', 'rows': 3}),
        label='Motivo de la anulación',
    )
