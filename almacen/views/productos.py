"""Vistas del catálogo de productos: listado, creación, edición y baja lógica."""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from nucleo.decoradores import rol_requerido

from ..forms import FormularioProducto
from ..models import Producto

ROLES_ALMACEN = ('ADMINISTRADOR', 'INVENTARIO')


@rol_requerido(*ROLES_ALMACEN)
def lista_productos(request):
    """
    Lista los productos del catálogo con su stock en tiempo real.

    Se usa select_related('categoria') para evitar el problema N+1 al
    mostrar la categoría de cada producto en la tabla.
    """
    termino_busqueda = request.GET.get('buscar', '').strip()
    filtro_categoria = request.GET.get('categoria', '')

    productos = Producto.objects.select_related('categoria').all()

    if termino_busqueda:
        from django.db.models import Q
        productos = productos.filter(
            Q(nombre__icontains=termino_busqueda) | Q(codigo__icontains=termino_busqueda)
        )

    if filtro_categoria:
        productos = productos.filter(categoria_id=filtro_categoria)

    from .categorias import Categoria
    from django.core.paginator import Paginator

    # Paginación
    paginator = Paginator(productos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    contexto = {
        'page_obj': page_obj,
        'categorias': Categoria.objects.filter(activa=True),
        'termino_busqueda': termino_busqueda,
        'filtro_categoria_actual': filtro_categoria,
    }
    return render(request, 'almacen/lista_productos.html', contexto)


@rol_requerido(*ROLES_ALMACEN)
def crear_producto(request):
    if request.method == 'POST':
        formulario = FormularioProducto(request.POST, request.FILES)
        if formulario.is_valid():
            producto = formulario.save()
            messages.success(request, f'Producto "{producto.nombre}" creado correctamente.')
            return redirect('almacen:lista_productos')
    else:
        formulario = FormularioProducto()

    return render(
        request,
        'almacen/formulario_producto.html',
        {'formulario': formulario, 'titulo': 'Nuevo producto', 'imagen_actual': ''},
    )


@rol_requerido(*ROLES_ALMACEN)
def editar_producto(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)

    if request.method == 'POST':
        formulario = FormularioProducto(request.POST, request.FILES, instance=producto)
        if formulario.is_valid():
            formulario.save()
            messages.success(request, f'Producto "{producto.nombre}" actualizado correctamente.')
            return redirect('almacen:lista_productos')
    else:
        formulario = FormularioProducto(instance=producto)

    imagen_actual = producto.imagen.url if producto.imagen and producto.imagen.name else ''
    contexto = {
        'formulario': formulario,
        'titulo': f'Editar producto: {producto.nombre}',
        'producto': producto,
        'imagen_actual': imagen_actual,
    }
    return render(request, 'almacen/formulario_producto.html', contexto)


@rol_requerido(*ROLES_ALMACEN)
def alternar_estado_producto(request, producto_id):
    """Activa o desactiva un producto sin eliminarlo (baja lógica)."""
    producto = get_object_or_404(Producto, pk=producto_id)
    producto.activo = not producto.activo
    producto.save(update_fields=['activo'])
    estado = 'activado' if producto.activo else 'desactivado'
    messages.success(request, f'Producto "{producto.nombre}" {estado} correctamente.')
    return redirect('almacen:lista_productos')


@rol_requerido(*ROLES_ALMACEN)
def buscar_productos_almacen_json(request):
    """
    Endpoint AJAX para buscar productos en los formularios de almacén (ej. Movimientos).
    A diferencia del POS, este incluye productos sin stock, ya que se necesita registrar 
    entradas para productos agotados.
    """
    from django.http import JsonResponse
    from django.db.models import Q
    
    termino = request.GET.get('q', '').strip()
    productos = Producto.objects.filter(activo=True)

    if termino:
        productos = productos.filter(Q(nombre__icontains=termino) | Q(codigo__icontains=termino))

    productos = productos.order_by('nombre')[:20]

    resultados = [
        {
            'id': p.id,
            'codigo': p.codigo,
            'nombre': p.nombre,
            'stock_actual': p.stock_actual,
        }
        for p in productos
    ]
    return JsonResponse({'resultados': resultados})
