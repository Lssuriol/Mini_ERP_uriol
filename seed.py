"""
Script de siembra (seed) de datos iniciales para el Mini ERP.

Crea los usuarios principales del sistema (Administrador, Cajero e
Inventario) y un catálogo básico de categorías y productos, para poder
probar el sistema inmediatamente después de instalarlo.

Las credenciales de los usuarios se leen desde el archivo `.env`
(ver `.env.example`), de modo que puedan modificarse fácilmente sin
tocar el código.

Uso:
    python seed.py
"""

import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configuracion.settings')
django.setup()

from decouple import config  # noqa: E402

from almacen.models import Categoria, MovimientoInventario, Producto  # noqa: E402
from almacen.servicios import registrar_movimiento  # noqa: E402
from usuarios.models import Usuario  # noqa: E402


def crear_usuarios_principales():
    """Crea (o actualiza) el usuario administrador principal del sistema."""
    usuarios_a_crear = [
        {
            'username': config('ADMIN_USERNAME', default='admin'),
            'password': config('ADMIN_PASSWORD', default='Admin12345'),
            'first_name': 'Administrador',
            'last_name': 'General',
            'rol': Usuario.Rol.ADMINISTRADOR,
            'es_superusuario': True,
        },
    ]

    for datos in usuarios_a_crear:
        usuario, creado = Usuario.objects.get_or_create(
            username=datos['username'],
            defaults={
                'first_name': datos['first_name'],
                'last_name': datos['last_name'],
                'rol': datos['rol'],
                'is_staff': datos['es_superusuario'],
                'is_superuser': datos['es_superusuario'],
                'activo_en_sistema': True,
            },
        )
        usuario.set_password(datos['password'])
        usuario.is_staff = datos['es_superusuario'] or usuario.is_staff
        usuario.is_superuser = datos['es_superusuario']
        usuario.save()

        accion = 'creado' if creado else 'actualizado'
        print(f'  Usuario "{usuario.username}" ({usuario.get_rol_display()}) {accion}.')

    return Usuario.objects.get(username=usuarios_a_crear[0]['username'])


def crear_categorias():
    """Crea el catálogo básico de categorías de un minimarket."""
    nombres_categorias = [
        ('Abarrotes', 'Productos de primera necesidad y despensa'),
        ('Bebidas', 'Gaseosas, jugos, agua y bebidas en general'),
        ('Lácteos', 'Leche, yogurt, quesos y derivados'),
        ('Limpieza', 'Productos de limpieza para el hogar'),
        ('Cuidado Personal', 'Higiene y cuidado personal'),
        ('Snacks', 'Galletas, golosinas y piqueos'),
    ]

    categorias = {}
    for nombre, descripcion in nombres_categorias:
        categoria, _ = Categoria.objects.get_or_create(nombre=nombre, defaults={'descripcion': descripcion})
        categorias[nombre] = categoria

    print(f'  {len(categorias)} categorías disponibles.')
    return categorias


def crear_productos(categorias, usuario_responsable):
    """Crea un catálogo de ejemplo con productos típicos de un minimarket."""
    # (codigo, nombre, categoria, p_compra, p_venta, stock_inicial, stock_min, es_perecedero)
    productos_ejemplo = [
        ('AB001', 'Arroz Costeño 5kg', 'Abarrotes', 16.90, 21.90, 40, 10, False),
        ('AB002', 'Aceite Primor 1L', 'Abarrotes', 9.50, 12.90, 35, 8, False),
        ('AB003', 'Azúcar Rubia Bella Bolsa 1kg', 'Abarrotes', 3.60, 5.20, 50, 12, False),
        ('AB004', 'Fideos Don Vittorio 500g', 'Abarrotes', 2.80, 4.00, 60, 15, False),
        ('BE001', 'Inca Kola 1.5L', 'Bebidas', 4.80, 7.00, 45, 10, False),
        ('BE002', 'Agua San Luis 625ml', 'Bebidas', 1.20, 2.00, 80, 20, False),
        ('BE003', 'Jugo Frugos Naranja 1L', 'Bebidas', 3.50, 5.50, 30, 8, True),
        ('LA001', 'Leche Gloria Evaporada 400g', 'Lácteos', 3.90, 5.20, 55, 12, True),
        ('LA002', 'Yogurt Gloria Fresa 1L', 'Lácteos', 6.20, 8.90, 20, 6, True),
        ('LI001', 'Detergente Ariel 500g', 'Limpieza', 5.10, 7.50, 25, 6, False),
        ('LI002', 'Lejía Clorox 1L', 'Limpieza', 3.20, 4.80, 30, 8, False),
        ('CP001', 'Jabón Protex 90g', 'Cuidado Personal', 2.10, 3.20, 40, 10, False),
        ('CP002', 'Shampoo Sedal 350ml', 'Cuidado Personal', 8.50, 12.50, 18, 5, False),
        ('SN001', 'Galletas Oreo 118g', 'Snacks', 2.60, 4.00, 50, 12, False),
        ('SN002', 'Papitas Lays 45g', 'Snacks', 2.20, 3.50, 45, 10, False),
    ]

    from datetime import date, timedelta
    
    productos_creados = 0
    for codigo, nombre, nombre_categoria, precio_compra, precio_venta, stock_inicial, stock_minimo, es_perecedero in productos_ejemplo:
        producto, creado = Producto.objects.get_or_create(
            codigo=codigo,
            defaults={
                'nombre': nombre,
                'categoria': categorias[nombre_categoria],
                'precio_compra': precio_compra,
                'precio_venta': precio_venta,
                'stock_minimo': stock_minimo,
                'unidad_medida': 'UND',
                'es_perecedero': es_perecedero,
            },
        )

        if creado:
            productos_creados += 1
            
            # Si es perecedero, le asignamos un lote inicial y fecha de vencimiento (20 dias desde hoy)
            kwargs_adicionales = {}
            if es_perecedero:
                kwargs_adicionales['numero_lote'] = f"LOTE-INI-{codigo}"
                kwargs_adicionales['fecha_vencimiento'] = date.today() + timedelta(days=20)
            
            # Registra el stock inicial como un movimiento de ENTRADA, para
            # mantener la trazabilidad completa desde el primer momento.
            registrar_movimiento(
                producto=producto,
                tipo_movimiento=MovimientoInventario.TipoMovimiento.ENTRADA,
                cantidad=stock_inicial,
                usuario=usuario_responsable,
                motivo='Carga inicial de inventario (seed)',
                **kwargs_adicionales
            )

    print(f'  {productos_creados} productos nuevos creados con su stock inicial.')


def ejecutar_seed():
    print('Sembrando datos iniciales del Mini ERP - Uriol Distribuciones S.A.C.\n')

    print('1. Usuarios principales:')
    usuario_admin = crear_usuarios_principales()

    print('\n2. Categorías de productos:')
    categorias = crear_categorias()

    print('\n3. Catálogo de productos y stock inicial:')
    crear_productos(categorias, usuario_admin)

    print('\nProceso de siembra finalizado correctamente.')


if __name__ == '__main__':
    ejecutar_seed()
