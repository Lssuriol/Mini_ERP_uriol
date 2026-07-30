"""Formularios del módulo de Almacén: productos, categorías y movimientos manuales."""

from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

from django import forms
from django.core.files.base import ContentFile
from django.utils.text import slugify

from .models import Categoria, MovimientoInventario, Producto


class FormularioCategoria(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'campo-formulario'}),
            'descripcion': forms.Textarea(attrs={'class': 'campo-formulario', 'rows': 3}),
        }


class FormularioProducto(forms.ModelForm):
    imagen_url = forms.URLField(
        required=False,
        label='Link de imagen (opcional)',
        widget=forms.URLInput(attrs={'class': 'campo-formulario', 'placeholder': 'https://...'}),
    )

    class Meta:
        model = Producto
        fields = [
            'codigo', 'nombre', 'descripcion', 'categoria', 'imagen',
            'precio_compra', 'precio_venta', 'stock_minimo', 'unidad_medida', 'activo',
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'campo-formulario'}),
            'nombre': forms.TextInput(attrs={'class': 'campo-formulario'}),
            'descripcion': forms.Textarea(attrs={'class': 'campo-formulario', 'rows': 3}),
            'categoria': forms.Select(attrs={'class': 'campo-formulario'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'campo-formulario', 'accept': 'image/*'}),
            'precio_compra': forms.NumberInput(attrs={'class': 'campo-formulario', 'step': '0.01'}),
            'precio_venta': forms.NumberInput(attrs={'class': 'campo-formulario', 'step': '0.01'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'campo-formulario'}),
            'unidad_medida': forms.TextInput(attrs={'class': 'campo-formulario'}),
        }

    def clean_imagen_url(self):
        url = (self.cleaned_data.get('imagen_url') or '').strip()
        if not url:
            return ''

        try:
            with urlopen(url, timeout=10) as respuesta:
                content_type = respuesta.headers.get('Content-Type', '')
                if not content_type.startswith('image/'):
                    raise forms.ValidationError('La URL debe apuntar a una imagen válida.')
                datos = respuesta.read(1024)
                if not datos:
                    raise forms.ValidationError('La URL no devolvió datos de imagen.')
        except forms.ValidationError:
            raise
        except Exception:
            raise forms.ValidationError('No se pudo cargar la imagen desde la URL ingresada.')

        return url

    def clean(self):
        datos_limpios = super().clean()
        precio_compra = datos_limpios.get('precio_compra')
        precio_venta = datos_limpios.get('precio_venta')

        if precio_compra is not None and precio_venta is not None and precio_venta < precio_compra:
            self.add_error('precio_venta', 'El precio de venta no puede ser menor al precio de compra.')

        return datos_limpios

    def save(self, commit=True):
        instancia = super().save(commit=False)
        imagen_url = (self.cleaned_data.get('imagen_url') or '').strip()
        imagen_subida = self.files.get('imagen')

        if imagen_url and not imagen_subida:
            try:
                with urlopen(imagen_url, timeout=10) as respuesta:
                    datos = respuesta.read()
            except Exception as error:
                raise forms.ValidationError('No se pudo descargar la imagen desde la URL ingresada.') from error

            if not datos:
                raise forms.ValidationError('La URL no devolvió datos de imagen.')

            ruta = Path(urlparse(imagen_url).path)
            extension = ruta.suffix.lower() if ruta.suffix else '.jpg'
            if extension not in {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}:
                extension = '.jpg'

            nombre_archivo = f"{slugify(instancia.nombre or 'producto')}{extension}"
            instancia.imagen.save(nombre_archivo, ContentFile(datos), save=False)

        if commit:
            instancia.save()

        return instancia


class FormularioMovimientoManual(forms.Form):
    """Formulario para registrar entradas de mercadería o ajustes/mermas manuales."""

    OPCIONES_TIPO = [
        (MovimientoInventario.TipoMovimiento.ENTRADA, 'Entrada de mercadería'),
        (MovimientoInventario.TipoMovimiento.AJUSTE, 'Ajuste de inventario (resta)'),
        (MovimientoInventario.TipoMovimiento.MERMA, 'Merma / producto dañado'),
    ]

    producto = forms.ModelChoiceField(
        queryset=Producto.objects.filter(activo=True).order_by('nombre'),
        widget=forms.HiddenInput(attrs={'id': 'id_producto_hidden'}),
        label='Producto',
    )
    tipo_movimiento = forms.ChoiceField(
        choices=OPCIONES_TIPO,
        widget=forms.Select(attrs={'class': 'campo-formulario'}),
        label='Tipo de movimiento',
    )
    cantidad = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'campo-formulario'}),
        label='Cantidad',
    )
    motivo = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'campo-formulario', 'placeholder': 'Opcional'}),
        label='Motivo / observación',
    )
