"""
Decoradores reutilizables para el control de accesos por rol.

Uso:
    @rol_requerido('ADMINISTRADOR', 'INVENTARIO')
    def vista_productos(request):
        ...
"""

from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def rol_requerido(*roles_permitidos):
    """
    Restringe el acceso a una vista según el rol del usuario autenticado.

    El Administrador siempre tiene acceso, sin importar los roles indicados,
    ya que es el rol con mayor jerarquía dentro del sistema.
    """

    def decorador(vista_func):
        @wraps(vista_func)
        @login_required
        def vista_envuelta(request, *args, **kwargs):
            usuario = request.user

            if not usuario.activo_en_sistema:
                messages.error(request, 'Tu usuario se encuentra deshabilitado. Contacta al administrador.')
                return redirect('usuarios:iniciar_sesion')

            if usuario.es_administrador or usuario.rol in roles_permitidos:
                return vista_func(request, *args, **kwargs)

            messages.warning(request, 'No tienes permisos para acceder a esa sección.')
            raise PermissionDenied('No tienes permisos suficientes para acceder a este módulo.')

        return vista_envuelta

    return decorador


def solo_administrador(vista_func):
    """Atajo para restringir una vista exclusivamente al rol Administrador."""
    return rol_requerido('ADMINISTRADOR')(vista_func)
