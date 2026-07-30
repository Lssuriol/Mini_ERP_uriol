"""Vistas del punto de venta (POS): búsqueda de productos y registro de ventas."""

import json
import urllib.request
import urllib.error
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from almacen.models import Producto
from nucleo.decoradores import rol_requerido

from ..forms import FormularioDatosVenta
from ..models import Venta
from ..servicios import procesar_venta

ROLES_CAJA = ('ADMINISTRADOR', 'CAJERO')


@rol_requerido(*ROLES_CAJA)
def punto_venta(request):
    """Pantalla principal del POS, donde el cajero arma el carrito de venta."""
    formulario = FormularioDatosVenta(initial={'tipo_comprobante': 'BOLETA', 'metodo_pago': 'EFECTIVO'})
    return render(request, 'caja/punto_venta.html', {'formulario': formulario})


@rol_requerido(*ROLES_CAJA)
@require_GET
def buscar_productos_json(request):
    """
    Endpoint AJAX que alimenta el buscador del POS.

    Solo trae productos activos con stock disponible, usando select_related
    para no golpear la base de datos por cada producto al serializar.
    """
    termino = request.GET.get('q', '').strip()
    productos = Producto.objects.select_related('categoria').filter(activo=True, stock_actual__gt=0)

    if termino:
        productos = productos.filter(Q(nombre__icontains=termino) | Q(codigo__icontains=termino))

    productos = productos.order_by('nombre')[:20]

    resultados = [
        {
            'id': producto.id,
            'codigo': producto.codigo,
            'nombre': producto.nombre,
            'precio_venta': str(producto.precio_venta),
            'stock_actual': producto.stock_actual,
            'categoria': producto.categoria.nombre,
            'imagen': producto.imagen.url if producto.imagen else None,
        }
        for producto in productos
    ]
    return JsonResponse({'resultados': resultados})


@rol_requerido(*ROLES_CAJA)
@require_POST
def registrar_venta(request):
    """
    Recibe el carrito (JSON) desde el POS y procesa la venta de forma atómica.

    Ante cualquier error (ej. stock insuficiente) se responde con un JSON
    de error y, gracias a `transaction.atomic` en el servicio, no queda
    ningún dato a medias en la base de datos.
    """
    try:
        cuerpo = json.loads(request.body)
        carrito = cuerpo.get('carrito', [])

        venta = procesar_venta(
            carrito=carrito,
            cajero=request.user,
            tipo_comprobante=cuerpo.get('tipo_comprobante', Venta.TipoComprobante.BOLETA),
            metodo_pago=cuerpo.get('metodo_pago', Venta.MetodoPago.EFECTIVO),
            cliente_nombre=cuerpo.get('cliente_nombre', ''),
            cliente_documento=cuerpo.get('cliente_documento', ''),
            cliente_email=cuerpo.get('cliente_email', ''),
            pos_operador=cuerpo.get('pos_operador', ''),
            pos_tipo_tarjeta=cuerpo.get('pos_tipo_tarjeta', ''),
            pos_numero_autorizacion=cuerpo.get('pos_numero_autorizacion', ''),
            pos_ultimos_digitos=cuerpo.get('pos_ultimos_digitos', ''),
        )
        
        # Obtener el estado del comprobante si existe
        estado_fe = 'N/A'
        if hasattr(venta, 'comprobante_electronico'):
            estado_fe = venta.comprobante_electronico.estado_emision
            
        return JsonResponse({
            'exito': True,
            'mensaje': f'Venta {venta.numero_comprobante} registrada correctamente.',
            'url_comprobante': f'/caja/ventas/{venta.id}/',
            'estado_fe': estado_fe
        })

    except ValidationError as error:
        mensaje = error.message if hasattr(error, 'message') else '; '.join(error.messages)
        return JsonResponse({'exito': False, 'mensaje': mensaje}, status=400)
    except (KeyError, Producto.DoesNotExist):
        return JsonResponse({'exito': False, 'mensaje': 'Uno de los productos del carrito ya no existe.'}, status=400)
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse({'exito': False, 'mensaje': 'Los datos de la venta son inválidos.'}, status=400)


@require_GET
@rol_requerido(*ROLES_CAJA)
def consultar_documento(request):
    """Consulta DNI o RUC en la API pública de apis.net.pe."""
    numero = request.GET.get('numero', '').strip()
    if not numero or not numero.isdigit() or len(numero) not in [8, 11]:
        return JsonResponse({'exito': False, 'mensaje': 'El documento debe tener 8 (DNI) o 11 (RUC) dígitos numéricos.'})
    
    endpoint = 'ruc' if len(numero) == 11 else 'dni'
    
    # Obtener el token desde las configuraciones
    from django.conf import settings
    token = getattr(settings, 'APIPERU_TOKEN', '')
    
    url = f'https://dniruc.apisperu.com/api/v1/{endpoint}/{numero}?token={token}'
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json'
        }
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            # apisperu.com puede retornar directamente el objeto o un wrapper
            # Tratamos de extraer el nombre basado en posibles formatos
            nombre = ''
            
            if endpoint == 'dni':
                if 'nombres' in data and 'apellidoPaterno' in data:
                    nombre = f"{data.get('nombres', '')} {data.get('apellidoPaterno', '')} {data.get('apellidoMaterno', '')}".strip()
                elif 'nombre' in data:
                    nombre = data['nombre']
                elif 'nombre_completo' in data:
                    nombre = data['nombre_completo']
            else:
                if 'razonSocial' in data:
                    nombre = data['razonSocial']
                elif 'nombre_o_razon_social' in data:
                    nombre = data['nombre_o_razon_social']
                elif 'nombre' in data:
                    nombre = data['nombre']
                    
            if nombre:
                return JsonResponse({'exito': True, 'nombre': nombre})
            else:
                return JsonResponse({'exito': False, 'mensaje': 'Documento no encontrado.'})
                
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return JsonResponse({'exito': False, 'mensaje': 'Documento no encontrado.'})
        return JsonResponse({'exito': False, 'mensaje': 'Error de conexión o Token inválido.'})
    except Exception:
        return JsonResponse({'exito': False, 'mensaje': 'Error de conexión con el servicio externo.'})


from django.core.paginator import Paginator
from django.db.models import Q
from datetime import datetime

@rol_requerido(*ROLES_CAJA)
def lista_ventas(request):
    """
    Historial de ventas con paginación, búsqueda y filtros.
    """
    ventas = Venta.objects.select_related('cajero').prefetch_related('detalles__producto').all()

    # Búsqueda
    q = request.GET.get('q', '').strip()
    if q:
        ventas = ventas.filter(
            Q(numero_comprobante__icontains=q) |
            Q(cliente_nombre__icontains=q) |
            Q(cliente_documento__icontains=q)
        )

    # Filtro por estado
    estado = request.GET.get('estado', '')
    if estado:
        ventas = ventas.filter(estado=estado)

    # Filtro por rango de fechas
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')
    
    if fecha_inicio:
        try:
            fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            ventas = ventas.filter(fecha_creacion__date__gte=fecha_inicio_obj)
        except ValueError:
            pass
            
    if fecha_fin:
        try:
            fecha_fin_obj = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            ventas = ventas.filter(fecha_creacion__date__lte=fecha_fin_obj)
        except ValueError:
            pass

    # Paginación
    paginator = Paginator(ventas, 20) # 20 ventas por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    contexto = {
        'page_obj': page_obj,
        'q': q,
        'estado_filtro': estado,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    return render(request, 'caja/lista_ventas.html', contexto)


@rol_requerido(*ROLES_CAJA)
def detalle_venta(request, venta_id):
    """Muestra el detalle de una venta específica (ticket) para impresión o revisión."""
    venta = get_object_or_404(
        Venta.objects.select_related('cajero').prefetch_related('detalles__producto'),
        pk=venta_id,
    )
    return render(request, 'caja/detalle_venta.html', {'venta': venta})
