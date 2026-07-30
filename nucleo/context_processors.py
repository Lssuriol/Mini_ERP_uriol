"""Context processors: inyectan datos disponibles en todos los templates."""

from django.conf import settings


def datos_globales(request):
    """Expone datos de la empresa y alertas de stock a todos los templates."""
    contexto = {
        'nombre_empresa': settings.NOMBRE_EMPRESA,
        'ruc_empresa': settings.RUC_EMPRESA,
    }

    if request.user.is_authenticated:
        from almacen.models import Producto
        contexto['total_alertas_stock'] = Producto.objects.filter(
            activo=True,
            stock_actual__lte=settings.STOCK_MINIMO_ALERTA,
        ).count()

    return contexto
