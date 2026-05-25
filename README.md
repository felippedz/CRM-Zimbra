# CRM Zimbra

Aplicación web Flask para la gestión de clientes, ventas, campañas y reportes, integrada con SQL Server.

---

## Índice

- [Descripción](#descripción)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Configuración técnica](#configuración-técnica)
- [Base de datos](#base-de-datos)
- [Ejecución](#ejecución)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Manual técnico](#manual-técnico)
- [Manual de uso](#manual-de-uso)
- [Capturas de pantalla](#capturas-de-pantalla)
- [Soporte](#soporte)

---

## Descripción

CRM Zimbra es un sistema básico para administrar:

- Usuarios y roles.
- Clientes y sus niveles.
- Ventas con detalle de servicios.
- Campañas comerciales.
- Reportes de mejores clientes, ventas mensuales y rendimiento de campañas.

La aplicación opera sobre una base de datos SQL Server y contiene una interfaz de plantillas Jinja.

---

## Requisitos

- Python 3.11+.
- Docker y Docker Compose.
- SQL Server (se puede levantar vía Docker).
- Dependencias de Python en `requirements.txt`.

---

## Instalación

1. Clonar o copiar el proyecto en el equipo.
2. Crear un entorno virtual (opcional pero recomendado):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. Instalar dependencias:
   ```powershell
   python -m pip install -r requirements.txt
   ```

---

## Configuración técnica

El proyecto usa variables de entorno opcionales en `backend.py` y `app.py`:

- `SQL_SERVER` - servidor SQL Server, por defecto `localhost,1433`.
- `SQL_DATABASE` - base de datos, por defecto `zimbra_crm`.
- `ODBC_DRIVER` - controlador ODBC, por defecto `ODBC Driver 18 for SQL Server`.
- `SECRET_KEY` - clave secreta Flask para sesiones y seguridad.

Ejemplo de uso:

```powershell
$env:SQL_SERVER = 'localhost,1433'
$env:SQL_DATABASE = 'zimbra_crm'
$env:ODBC_DRIVER = 'ODBC Driver 18 for SQL Server'
$env:SECRET_KEY = 'mi_clave_segura'
```

---

## Base de datos

El archivo `script.sql` crea la base de datos, tablas, datos iniciales y objetos necesarios para la aplicación:

- Tablas: `roles`, `usuarios`, `clientes`, `servicios`, `ventas`, `detalle_venta`, `campanias`, `cliente_servicios`, `auditoria_ventas`, `historial_niveles_cliente`, entre otras.
- Vistas: `vista_ventas_mensuales`, `vista_mejores_clientes`, `vista_rendimiento_campanias`, `vista_departamentos`.
- Procedimientos y triggers.

> Importante: `script.sql` está adaptado para SQL Server.

---

## Ejecución

1. Levantar SQL Server:
   ```powershell
   docker compose up -d
   ```
2. Ejecutar la aplicación Flask:
   ```powershell
   python app.py
   ```
3. Abrir en el navegador:
   ```text
   http://127.0.0.1:5000
   ```

---

## Estructura del proyecto

- `app.py` - punto de entrada y definiciones de rutas.
- `backend.py` - conexión y funciones de acceso a la base de datos.
- `auth.py` - lógica de autenticación, permisos y sesiones.
- `templates/` - vistas HTML para la interfaz.
- `docker-compose.yml` - servicio SQL Server.
- `script.sql` - creación de base de datos y carga inicial.
- `requirements.txt` - dependencias de Python.
- `README.md` - este manual.

---

## Manual técnico

### Flujo de la aplicación

1. El usuario inicia sesión en `/login`.
2. Si está autenticado, accede al dashboard y a las secciones según su rol.
3. Las rutas están protegidas por decoradores en `auth.py`:
   - `login_required` para cualquier usuario autenticado.
   - `require_role(...)` para validar permisos por rol.

### Seguridad y autenticación

- Las contraseñas se almacenan como hash SHA-256 en la base de datos.
- `auth.py` ofrece:
  - `hash_password(password)` para generar el hash.
  - `check_password(password, hashed)` para validar la contraseña.
  - `login_user(usuario)` para guardar datos en sesión.
  - `logout_user()` para limpiar la sesión.
  - `current_user()` para recuperar el usuario autenticado.

### Rutas importantes

- `/login` - inicio de sesión.
- `/logout` - cerrar sesión.
- `/` - dashboard.
- `/clientes` - listado de clientes.
- `/clientes/registrar` - registra un nuevo cliente.
- `/clientes/editar/<id>` - editar la información de un cliente.
- `/ventas` - listado de ventas.
- `/ventas/registrar` - registra una nueva venta.
- `/campanias` - listado de campañas.
- `/niveles` - listado de niveles de cliente, creación, edición y eliminación (solo ADMIN).
- `/reportes` - muestra reportes.
- `/servicios` - lista de servicios disponibles y servicios comprados.
- `/servicios/<id>` - detalle de servicio.
- `/servicios/comprar` - compra un servicio para el cliente autenticado.
- `/empleados` - listado y registro de empleados (solo ADMIN).
- `/mi_perfil` - perfil del cliente.

### Acceso a datos

- `backend.py` usa `pyodbc` para conectarse a SQL Server.
- Funciones:
  - `fetchone(query, params)`
  - `fetchall(query, params)`
  - `execute(query, params)`

### Desarrollo

Para mantener ordenado el proyecto:

- Modifica rutas en `app.py` si se amplía la funcionalidad.
- Extiende `auth.py` para nuevos roles o permisos.
- Añade consultas en `backend.py` o nuevos helpers si necesitas lógica de datos.

---

## Manual de uso

### Inicio de sesión

- Accede a `/login`.
- Ingresa correo y contraseña.
- El sistema validará credenciales y redirigirá al `dashboard`.

### Dashboard

- Muestra totales clave: ventas, clientes y servicios.
- Presenta las últimas ventas registradas con fechas en formato corto `dd/mm/YYYY`.
- Incluye gráficos de ventas mensuales e ingresos por campaña para los roles administrativos.

### Clientes

- En `/clientes` se muestra la lista de clientes.
- Puedes registrar un nuevo cliente desde el formulario disponible.
- El cliente se crea como usuario con rol `CLIENTE`.

### Ventas

- En `/ventas` se listan las ventas existentes.
- Para registrar una venta selecciona cliente, servicio, campaña y cantidad.
- El proceso invoca el procedimiento almacenado `registrar_venta`.

### Campañas

- En `/campanias` se visualiza la lista de campañas comerciales.
- Solo usuarios `ADMIN` pueden ver esta sección.

### Niveles

- En `/niveles` se administran los niveles de cliente.
- Los usuarios `ADMIN` pueden crear, editar y eliminar niveles.
- No se permite eliminar un nivel que esté asignado a clientes.

### Reportes

- En `/reportes` se cargan:
  - Mejores clientes.
  - Ventas mensuales.
  - Rendimiento de campañas.
- Los datos provienen de vistas SQL.

### Mi perfil

- En `/mi_perfil` el cliente ve su información personal y de empresa.
- Solo los usuarios con rol `CLIENTE` pueden acceder.

### Servicios

- En `/servicios` el cliente puede ver servicios disponibles y servicios ya adquiridos.
- Se puede ver el detalle de un servicio con `/servicios/<id>` y comprarlo con el botón de compra.
- Los servicios activados se registran con fechas de inicio y fin automáticas.

### Empleados

- En `/empleados` el administrador puede ver la lista de empleados y registrar nuevos usuarios de tipo empleado.
- El formulario crea el usuario en `usuarios` y el perfil de empleado en `empleados`.

### Permisos de roles

- `ADMIN`: acceso total al dashboard, clientes, ventas, campañas y reportes.
- `EMPLEADO`: acceso a dashboard, clientes y ventas.
- `CLIENTE`: acceso al dashboard y a `mi_perfil`.

---

## Capturas de pantalla

Agrega aquí los pantallazos de la funcionalidad una vez que los tengas.

- `Login`
- `Dashboard`
- `Clientes`
- `Ventas`
- `Campañas`
- `Reportes`
- `Mi perfil`

> Consejo: crea una carpeta `docs/screenshots` y coloca las imágenes allí.

---

## Soporte

Para dudas o mejoras, revisa las rutas de `app.py` y el archivo `script.sql` para la estructura de datos.

---
