"""
URLs raíz del proyecto Mini ERP - Uriol Distribuciones S.A.C.

Cada módulo de negocio expone sus propias URLs bajo un prefijo dedicado.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', RedirectView.as_view(pattern_name='reportes:panel_principal', permanent=False)),

    path('usuarios/', include('usuarios.urls')),
    path('almacen/', include('almacen.urls')),
    path('caja/', include('caja.urls')),
    path('facturacion/', include('facturacion.urls')),
    path('reportes/', include('reportes.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
