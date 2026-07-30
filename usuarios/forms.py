"""Formularios relacionados a la autenticación y gestión de usuarios."""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Usuario


class FormularioInicioSesion(AuthenticationForm):
    """Formulario de login personalizado con estilos propios del ERP."""

    username = forms.CharField(
        label='Usuario',
        widget=forms.TextInput(attrs={'class': 'campo-formulario', 'autofocus': True, 'placeholder': 'Usuario'}),
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'campo-formulario', 'placeholder': 'Contraseña'}),
    )


class FormularioUsuario(UserCreationForm):
    """Formulario para crear o editar un usuario del sistema (solo Administrador)."""

    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'dni', 'telefono', 'rol', 'activo_en_sistema']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'campo-formulario'}),
            'first_name': forms.TextInput(attrs={'class': 'campo-formulario'}),
            'last_name': forms.TextInput(attrs={'class': 'campo-formulario'}),
            'email': forms.EmailInput(attrs={'class': 'campo-formulario'}),
            'dni': forms.TextInput(attrs={'class': 'campo-formulario'}),
            'telefono': forms.TextInput(attrs={'class': 'campo-formulario'}),
            'rol': forms.Select(attrs={'class': 'campo-formulario'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre_campo in ['password1', 'password2']:
            self.fields[nombre_campo].widget.attrs.update({'class': 'campo-formulario'})


class FormularioEdicionUsuario(forms.ModelForm):
    """Formulario para editar datos de un usuario existente sin tocar la contraseña."""

    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email', 'dni', 'telefono', 'rol', 'activo_en_sistema']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'campo-formulario'}),
            'last_name': forms.TextInput(attrs={'class': 'campo-formulario'}),
            'email': forms.EmailInput(attrs={'class': 'campo-formulario'}),
            'dni': forms.TextInput(attrs={'class': 'campo-formulario'}),
            'telefono': forms.TextInput(attrs={'class': 'campo-formulario'}),
            'rol': forms.Select(attrs={'class': 'campo-formulario'}),
        }
