"""URLs de la app usuarios: autenticación y gestión de cuentas."""

from django.urls import path

from . import views

app_name = 'usuarios'

urlpatterns = [
    path('ingresar/', views.VistaIniciarSesion.as_view(), name='iniciar_sesion'),
    path('salir/', views.cerrar_sesion, name='cerrar_sesion'),
    path('mi-perfil/', views.mi_perfil, name='mi_perfil'),

    path('lista/', views.lista_usuarios, name='lista_usuarios'),
    path('nuevo/', views.crear_usuario, name='crear_usuario'),
    path('<int:usuario_id>/editar/', views.editar_usuario, name='editar_usuario'),
    path('<int:usuario_id>/cambiar-password/', views.cambiar_password_usuario, name='cambiar_password_usuario'),
    path('<int:usuario_id>/alternar-estado/', views.alternar_estado_usuario, name='alternar_estado_usuario'),
]
