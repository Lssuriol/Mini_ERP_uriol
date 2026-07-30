"""Vistas de autenticación: inicio y cierre de sesión."""

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect

from ..forms import FormularioInicioSesion


class VistaIniciarSesion(LoginView):
    """Vista de inicio de sesión con el formulario y template propios del ERP."""

    template_name = 'usuarios/iniciar_sesion.html'
    authentication_form = FormularioInicioSesion
    redirect_authenticated_user = True

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        messages.success(self.request, f'Bienvenido(a), {self.request.user.get_full_name() or self.request.user.username}.')
        return respuesta

    def form_invalid(self, form):
        messages.error(self.request, 'Usuario o contraseña incorrectos.')
        return super().form_invalid(form)


def cerrar_sesion(request):
    """Cierra la sesión del usuario actual y lo redirige al login."""
    logout(request)
    messages.info(request, 'Sesión cerrada correctamente.')
    return redirect('usuarios:iniciar_sesion')
