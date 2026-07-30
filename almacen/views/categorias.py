"""Vistas de gestión de categorías de productos."""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from nucleo.decoradores import rol_requerido

from ..forms import FormularioCategoria
from ..models import Categoria

ROLES_ALMACEN = ('ADMINISTRADOR', 'INVENTARIO')


@rol_requerido(*ROLES_ALMACEN)
def lista_categorias(request):
    categorias = Categoria.objects.all()
    return render(request, 'almacen/lista_categorias.html', {'categorias': categorias})


@rol_requerido(*ROLES_ALMACEN)
def crear_categoria(request):
    if request.method == 'POST':
        formulario = FormularioCategoria(request.POST)
        if formulario.is_valid():
            categoria = formulario.save()
            messages.success(request, f'Categoría "{categoria.nombre}" creada correctamente.')
            return redirect('almacen:lista_categorias')
    else:
        formulario = FormularioCategoria()

    return render(request, 'almacen/formulario_categoria.html', {'formulario': formulario, 'titulo': 'Nueva categoría'})


@rol_requerido(*ROLES_ALMACEN)
def editar_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, pk=categoria_id)

    if request.method == 'POST':
        formulario = FormularioCategoria(request.POST, instance=categoria)
        if formulario.is_valid():
            formulario.save()
            messages.success(request, f'Categoría "{categoria.nombre}" actualizada correctamente.')
            return redirect('almacen:lista_categorias')
    else:
        formulario = FormularioCategoria(instance=categoria)

    contexto = {'formulario': formulario, 'titulo': f'Editar categoría: {categoria.nombre}'}
    return render(request, 'almacen/formulario_categoria.html', contexto)
