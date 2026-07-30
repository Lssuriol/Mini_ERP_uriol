"""
Configuración principal del proyecto Mini ERP - Uriol Distribuciones S.A.C.

Este archivo centraliza la configuración de Django para los 5 módulos
de la aplicación: usuarios, almacen, caja, reportes y nucleo.
"""

from pathlib import Path
from decouple import config, Csv
import dj_database_url

# ---------------------------------------------------------------------------
# Rutas base del proyecto
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Seguridad
# ---------------------------------------------------------------------------
SECRET_KEY = config('DJANGO_SECRET_KEY', default='django-insecure-cambiar-esta-clave-en-produccion')

DEBUG = config('DJANGO_DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('DJANGO_ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())

# ---------------------------------------------------------------------------
# Aplicaciones instaladas
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Aplicaciones propias del Mini ERP (orden de dependencia)
    'nucleo.apps.NucleoConfig',
    'usuarios.apps.UsuariosConfig',
    'almacen.apps.AlmacenConfig',
    'caja.apps.CajaConfig',
    'facturacion.apps.FacturacionConfig',
    'reportes.apps.ReportesConfig',
]

# ---------------------------------------------------------------------------
# Facturación Electrónica (Nubefact)
# ---------------------------------------------------------------------------
NUBEFACT_URL = config('NUBEFACT_URL', default='https://api.nubefact.com/api/v1/fe/comprobantes')
NUBEFACT_TOKEN = config('NUBEFACT_TOKEN', default='')
SERIE_BOLETA = config('SERIE_BOLETA', default='B001')
SERIE_FACTURA = config('SERIE_FACTURA', default='F001')

# ---------------------------------------------------------------------------
# Envío de correos electrónicos (Brevo API)
# ---------------------------------------------------------------------------
BREVO_API_KEY = config('BREVO_API_KEY', default='')
BREVO_SENDER_EMAIL = config('BREVO_SENDER_EMAIL', default='facturacion@uriol.com')
BREVO_SENDER_NAME = config('BREVO_SENDER_NAME', default='Uriol Distribuciones SAC')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Sirve archivos estáticos en producción
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'configuracion.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'nucleo.context_processors.datos_globales',
            ],
        },
    },
]

WSGI_APPLICATION = 'configuracion.wsgi.application'

# ---------------------------------------------------------------------------
# Base de datos
# ---------------------------------------------------------------------------
DATABASE_URL = config('DATABASE_URL', default=None)

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=True)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ---------------------------------------------------------------------------
# Modelo de usuario personalizado (con roles)
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = 'usuarios.Usuario'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = 'usuarios:iniciar_sesion'
LOGIN_REDIRECT_URL = 'reportes:panel_principal'
LOGOUT_REDIRECT_URL = 'usuarios:iniciar_sesion'

# ---------------------------------------------------------------------------
# Internacionalización
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'es-pe'
TIME_ZONE = 'America/Lima'
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Archivos estáticos (CSS, JS) - servidos con WhiteNoise en producción
# ---------------------------------------------------------------------------
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ---------------------------------------------------------------------------
# Configuración opcional de Supabase Storage (S3 API)
# Si SUPABASE_STORAGE_BUCKET_NAME está definido, reemplaza el storage local.
# ---------------------------------------------------------------------------
SUPABASE_BUCKET = config('SUPABASE_STORAGE_BUCKET_NAME', default=None)

if SUPABASE_BUCKET:
    AWS_STORAGE_BUCKET_NAME = SUPABASE_BUCKET
    AWS_S3_ENDPOINT_URL = config('SUPABASE_S3_ENDPOINT_URL')
    AWS_ACCESS_KEY_ID = config('SUPABASE_S3_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = config('SUPABASE_S3_SECRET_ACCESS_KEY')
    AWS_S3_REGION_NAME = config('SUPABASE_S3_REGION_NAME', default='us-east-1')
    AWS_DEFAULT_ACL = 'public-read'
    AWS_S3_FILE_OVERWRITE = False
    
    # Desactivar URLs firmadas para que use URLs públicas directas
    AWS_QUERYSTRING_AUTH = False
    
    # Construir el dominio personalizado para la URL pública nativa de Supabase
    # Supabase S3 endpoint es: https://<ref>.supabase.co/storage/v1/s3
    # La URL pública es: https://<ref>.supabase.co/storage/v1/object/public/<bucket>
    endpoint_domain = AWS_S3_ENDPOINT_URL.replace('https://', '').replace('/s3', '')
    AWS_S3_CUSTOM_DOMAIN = f"{endpoint_domain}/object/public/{SUPABASE_BUCKET}"
    
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------------
# Configuración propia del negocio (Uriol Distribuciones S.A.C.)
# ---------------------------------------------------------------------------
NOMBRE_EMPRESA = config('NOMBRE_EMPRESA', default='Uriol Distribuciones S.A.C.')
RUC_EMPRESA = config('RUC_EMPRESA', default='20123456789')
DIRECCION_EMPRESA = config('DIRECCION_EMPRESA', default='Trujillo, La Libertad, Perú')
IGV_PORCENTAJE = config('IGV_PORCENTAJE', default=0.18, cast=float)
STOCK_MINIMO_ALERTA = config('STOCK_MINIMO_ALERTA', default=5, cast=int)
