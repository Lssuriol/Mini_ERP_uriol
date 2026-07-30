"""Vistas de gestión (CRUD) de usuarios del sistema. Acceso exclusivo del Administrador."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from nucleo.decoradores import solo_administrador

from ..forms import FormularioEdicionUsuario, FormularioUsuario
from ..models import Usuario


@solo_administrador
def lista_usuarios(request):
    """Lista todos los usuarios registrados en el sistema."""
    usuarios = Usuario.objects.all().order_by('rol', 'first_name')
    return render(request, 'usuarios/lista_usuarios.html', {'usuarios': usuarios})


@solo_administrador
def crear_usuario(request):
    """Crea un nuevo usuario (administrador, cajero o inventario)."""
    if request.method == 'POST':
        formulario = FormularioUsuario(request.POST)
        if formulario.is_valid():
            usuario = formulario.save()
            messages.success(request, f'Usuario "{usuario.username}" creado correctamente.')
            return redirect('usuarios:lista_usuarios')
    else:
        formulario = FormularioUsuario()

    contexto = {'formulario': formulario, 'titulo': 'Nuevo usuario'}
    return render(request, 'usuarios/formulario_usuario.html', contexto)


@solo_administrador
def editar_usuario(request, usuario_id):
    """Edita los datos de un usuario existente."""
    usuario = get_object_or_404(Usuario, pk=usuario_id)

    if request.method == 'POST':
        formulario = FormularioEdicionUsuario(request.POST, instance=usuario)
        if formulario.is_valid():
            formulario.save()
            messages.success(request, f'Usuario "{usuario.username}" actualizado correctamente.')
            return redirect('usuarios:lista_usuarios')
    else:
        formulario = FormularioEdicionUsuario(instance=usuario)

    contexto = {'formulario': formulario, 'titulo': f'Editar usuario: {usuario.username}', 'usuario_editado': usuario}
    return render(request, 'usuarios/formulario_usuario.html', contexto)


@solo_administrador
def alternar_estado_usuario(request, usuario_id):
    """Habilita o deshabilita el acceso de un usuario al sistema."""
    usuario = get_object_or_404(Usuario, pk=usuario_id)

    if usuario == request.user:
        messages.error(request, 'No puedes deshabilitar tu propio usuario.')
    else:
        usuario.activo_en_sistema = not usuario.activo_en_sistema
        usuario.save(update_fields=['activo_en_sistema'])
        estado = 'habilitado' if usuario.activo_en_sistema else 'deshabilitado'
        messages.success(request, f'Usuario "{usuario.username}" {estado} correctamente.')

    return redirect('usuarios:lista_usuarios')


@login_required
def mi_perfil(request):
    """Muestra la información del perfil del usuario autenticado."""
    return render(request, 'usuarios/mi_perfil.html', {'usuario': request.user})
