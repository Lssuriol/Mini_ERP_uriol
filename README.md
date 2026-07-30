<div align="center">
  <h1>Mini ERP - Punto de Venta & Facturación Electrónica</h1>
  <p><strong>Sistema integral de control de inventario, ventas y facturación electrónica para minimarkets y retail.</strong></p>
  <p>
    <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python" />
    <img src="https://img.shields.io/badge/Django-5.0-092E20.svg?logo=django" alt="Django" />
    <img src="https://img.shields.io/badge/Estado-Producci%C3%B3n-success" alt="Estado" />
  </p>
</div>

---

## 📖 Descripción del Proyecto
**Uriol ERP** es un sistema web robusto y de alto rendimiento desarrollado en **Django**, diseñado específicamente para resolver las necesidades diarias de **Uriol Distribuciones S.A.C.** 
Permite administrar un catálogo de productos, controlar stock en tiempo real mediante transacciones atómicas, registrar ventas a través de un Punto de Venta (POS) intuitivo y emitir comprobantes electrónicos válidos (SUNAT).

## ✨ Características Principales
- **📦 Control de Inventario en Tiempo Real**: Prevención de condiciones de carrera mediante bloqueos de fila (`select_for_update`) y trazabilidad completa de entradas/salidas.
- **🏷️ Gestión por Lotes y Vencimientos (FIFO)**: Trazabilidad por número de lote, descargo automático bajo la regla *First In, First Out* y un dashboard dedicado para el control de productos próximos a vencer o caducados.
- **📷 Escaneo de Códigos de Barras Inteligente**: Uso de lectores láser o cámara web integrada para registrar productos en el POS y Almacén, optimizado para evitar lecturas falsas (ruido).
- **💻 Punto de Venta (POS) Dinámico**: Interfaz asíncrona (AJAX) ultra rápida para la búsqueda y selección de productos sin recargar la página.
- **🧾 Facturación Electrónica**: Integración nativa con proveedores de facturación (PSE/OSE) y envío automático de comprobantes PDF/XML por correo electrónico mediante la API de Brevo.
- **🔐 Gestión de Roles y Permisos**: Roles predefinidos (`Administrador`, `Cajero`, `Inventario`) con control estricto de acceso a vistas mediante decoradores personalizados.
- **📊 Analítica y Reportes (Dashboard)**: Métricas clave de rendimiento (KPIs), estimación de ganancias, y gráficos dinámicos de tendencias históricas de ventas utilizando Chart.js.

## 🏗️ Arquitectura y Tecnologías
- **Backend:** Python 3.10+, Django 5.x
- **Frontend:** Vanilla JavaScript (ES6), HTML5, CSS3 Nativo (Variables CSS, Flexbox/Grid)
- **Base de Datos:** SQLite (Desarrollo) / PostgreSQL (Producción recomendada)
- **Despliegue de Estáticos:** WhiteNoise
- **Integraciones:** Nubefact (SUNAT API), Brevo (Mailing), APIS.net.pe (Consultas DNI/RUC)

---

## 🔌 Integraciones y APIs Externas

Este sistema hace uso de diversas plataformas y APIs de terceros para funcionar eficientemente y automatizar procesos:

* **Supabase (PostgreSQL):** Base de datos relacional principal en producción.
* **Supabase Storage (API S3):** Almacenamiento en la nube (Object Storage) para guardar y distribuir las imágenes de los productos del catálogo.
* **APIs Perú (dniruc.apisperu.com):** Servicio para consultar automáticamente los datos de clientes ingresando su número de DNI o RUC desde el Punto de Venta.
* **Open Food Facts API:** Integración para autocompletar instantáneamente el nombre y fotografía de productos nuevos al escanear su código de barras en el módulo de Almacén.
* **NubeFact:** API de facturación electrónica para enviar los comprobantes emitidos (Boletas/Facturas) a SUNAT de manera automática.
* **Brevo (anteriormente Sendinblue):** Servidor SMTP transaccional para el envío de comprobantes electrónicos a los correos de los clientes.

---

## 🚀 Guía de Instalación (Entorno de Desarrollo)

### 1. Clonar el repositorio y preparar el entorno
```bash
git clone https://github.com/Lssuriol/Mini_ERP_uriol.git
cd uriol_erp
python -m venv venv
```

### 2. Activar el entorno virtual
- **Windows:** `venv\Scripts\activate`
- **Linux/Mac:** `source venv/bin/activate`

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno
Copia el archivo de ejemplo para crear tus configuraciones locales:
```bash
cp .env.example .env
```
Abre `.env` y configura los siguientes valores esenciales:
| Variable | Descripción |
|----------|-------------|
| `DJANGO_DEBUG` | `True` para desarrollo, `False` para producción. |
| `DJANGO_SECRET_KEY` | Llave criptográfica secreta de Django. |
| `DATABASE_URL` | *(Opcional)* URL de conexión a PostgreSQL/Supabase. Si no se define, se usa SQLite. |
| `SUPABASE_STORAGE_BUCKET_NAME` | *(Opcional)* Nombre del bucket en Supabase Storage (o AWS S3) para guardar imágenes de productos. Si no se define, se usa almacenamiento local. |
| `SUPABASE_S3_ENDPOINT_URL` | *(Opcional)* URL de conexión a S3 de Supabase. |
| `SUPABASE_S3_ACCESS_KEY_ID` | *(Opcional)* Access Key ID de Supabase S3. |
| `SUPABASE_S3_SECRET_ACCESS_KEY` | *(Opcional)* Secret Key de Supabase S3. |
| `BREVO_API_KEY` | Credencial para el envío de correos. |
| `NUBEFACT_TOKEN` | Token para emisión de comprobantes a SUNAT. |

### 5. Migraciones y Datos Semilla
Prepara la base de datos y carga los datos de prueba (categorías, productos y usuarios):
```bash
python manage.py migrate
python seed.py
```

### 6. Iniciar Servidor
```bash
python manage.py runserver
```
La aplicación estará disponible en `http://127.0.0.1:8000/`.

---

## 🧑‍💻 Usuarios por Defecto (Creados por `seed.py`)
Para pruebas iniciales, puedes usar las siguientes credenciales (se recomienda cambiarlas inmediatamente en producción):
| Usuario | Contraseña | Rol | Accesos |
|---|---|---|---|
| `admin` | `Admin12345` | Administrador | Acceso total al ERP. El administrador puede crear los demás cajeros y encargados desde la interfaz. |

---

## 🛠️ Notas Técnicas para Desarrolladores
- **Transacciones Atómicas:** El registro de ventas en `caja.servicios.procesar_venta()` se encuentra bajo un decorador `@transaction.atomic`. Esto garantiza que si la validación de inventario falla o la conexión se interrumpe, el comprobante, el detalle y el movimiento de inventario se reviertan de forma íntegra.
- **Consultas Optimizadas (N+1):** Se hace un uso intensivo de `select_related()` y `prefetch_related()` en las vistas de reportes y consultas al POS, reduciendo la carga de la base de datos drásticamente. Las agregaciones (`Sum`, `Count`) se resuelven a nivel de motor de BD.
- **Validación de Identidad:** El sistema se comunica de forma asíncrona para autocompletar la razón social o nombre de clientes consultando los padrones usando RUC/DNI.

---

## 📦 Puesta en Producción
Para desplegar este proyecto en un servidor en la nube (AWS, DigitalOcean, VPS, etc.):
1. Cambiar `DJANGO_DEBUG=False`.
2. Asignar los dominios autorizados en `DJANGO_ALLOWED_HOSTS`.
3. Ejecutar `python manage.py collectstatic` para procesar estáticos.
4. Cambiar el motor de BD a PostgreSQL o MySQL.
5. Utilizar Gunicorn u otro servidor WSGI para levantar la aplicación, en conjunto con un proxy inverso como Nginx.
