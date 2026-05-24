import csv
import io
import os
from datetime import date, timedelta

from flask import (
    Flask,
    Response,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from backend import (
    fetchone,
    fetchall,
    execute
)

from auth import (
    login_user,
    logout_user,
    current_user,
    login_required,
    require_role,
    check_password,
    hash_password
)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'zimbra_secret_key_2026')


def format_currency(value):
    try:
        return f"${float(value):,.2f}"
    except Exception:
        return "$0.00"


app.jinja_env.filters['currency'] = format_currency


# =====================================================
# LOGIN
# =====================================================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        correo = request.form['correo']

        password = request.form['password']

        usuario = fetchone("""
        SELECT
            u.id_usuario,
            u.nombre,
            u.correo,
            u.password_hash,
            r.nombre_rol
        FROM usuarios u
        INNER JOIN roles r
        ON u.id_rol = r.id_rol
        WHERE u.correo = ? OR u.nombre = ?
        """, (correo, correo))

        if not usuario:

            flash(
                'Usuario no encontrado',
                'error'
            )

            return redirect(url_for('login'))

        if not check_password(
            password,
            usuario['password_hash']
        ):

            flash(
                'Contraseña incorrecta',
                'error'
            )

            return redirect(url_for('login'))

        login_user(usuario)

        flash(
            'Bienvenido al sistema',
            'success'
        )

        return redirect(url_for('dashboard'))

    return render_template('login.html')

# =====================================================
# LOGOUT
# =====================================================

@app.route('/logout')
def logout():

    logout_user()

    return redirect(url_for('login'))


@app.route('/unauthorized')
def unauthorized():
    return render_template('unauthorized.html', current_user=current_user())


# =====================================================
# DASHBOARD
# =====================================================

@app.route('/')
@login_required
def dashboard():

    user = current_user()

    if user['rol'] == 'CLIENTE':
        servicios_adquiridos = fetchall("""
        SELECT
            s.nombre AS servicio,
            s.precio,
            cs.fecha_inicio,
            cs.fecha_fin,
            cs.estado
        FROM cliente_servicios cs
        INNER JOIN clientes c
            ON cs.id_cliente = c.id_cliente
        INNER JOIN usuarios u
            ON c.id_usuario = u.id_usuario
        INNER JOIN servicios s
            ON cs.id_servicio = s.id_servicio
        WHERE u.id_usuario = ?
        ORDER BY cs.fecha_inicio DESC
        """, (user['id'],))

        for servicio in servicios_adquiridos:
            if servicio.get('fecha_inicio'):
                try:
                    servicio['fecha_inicio'] = servicio['fecha_inicio'].strftime('%Y-%m-%d')
                except Exception:
                    servicio['fecha_inicio'] = str(servicio['fecha_inicio'])[:10]
            if servicio.get('fecha_fin'):
                try:
                    servicio['fecha_fin'] = servicio['fecha_fin'].strftime('%Y-%m-%d')
                except Exception:
                    servicio['fecha_fin'] = str(servicio['fecha_fin'])[:10]

        return render_template(
            'dashboard.html',
            current_user=user,
            user_services=servicios_adquiridos
        )

    total_ventas = fetchone(
        "SELECT ISNULL(SUM(total),0) AS total FROM ventas"
    )

    total_clientes = fetchone(
        "SELECT COUNT(*) AS total FROM clientes"
    )

    total_servicios = fetchone(
        "SELECT COUNT(*) AS total FROM servicios"
    )

    ventas = fetchall("""
    SELECT TOP 5
        v.id_venta,
        u.nombre,
        v.total,
        v.fecha,
        v.estado_pago
    FROM ventas v
    INNER JOIN clientes c
        ON v.id_cliente = c.id_cliente
    INNER JOIN usuarios u
        ON c.id_usuario = u.id_usuario
    ORDER BY v.fecha DESC
    """)

    ventas_por_mes = fetchall("""
    SELECT
        YEAR(fecha) AS anio,
        MONTH(fecha) AS mes,
        SUM(total) AS total
    FROM ventas
    GROUP BY YEAR(fecha), MONTH(fecha)
    ORDER BY YEAR(fecha), MONTH(fecha)
    """)

    ventas_por_campania = fetchall("""
    SELECT
        c.nombre,
        ISNULL(SUM(v.total), 0) AS total
    FROM campanias c
    LEFT JOIN ventas v
        ON c.id_campania = v.id_campania
    GROUP BY c.nombre
    ORDER BY total DESC
    """)

    month_labels = [f"{row['mes']:02d}/{row['anio']}" for row in ventas_por_mes]
    month_values = [float(row['total']) for row in ventas_por_mes]
    campaign_labels = [row['nombre'] for row in ventas_por_campania]
    campaign_values = [float(row['total']) for row in ventas_por_campania]

    return render_template(
        'dashboard.html',
        total_ventas=total_ventas,
        total_clientes=total_clientes,
        total_servicios=total_servicios,
        ventas=ventas,
        current_user=user,
        chart_labels=month_labels,
        chart_values=month_values,
        campaign_labels=campaign_labels,
        campaign_values=campaign_values
    )

@app.route('/servicios')
@require_role('CLIENTE')
def servicios():

    user = current_user()
    cliente = fetchone(
        "SELECT id_cliente FROM clientes WHERE id_usuario = ?",
        (user['id'],)
    )

    servicios_disponibles = fetchall(
        "SELECT * FROM servicios WHERE estado = 'ACTIVO' ORDER BY nombre"
    )

    servicios_comprados = fetchall("""
    SELECT
        cs.id_cliente_servicio,
        s.nombre,
        s.precio,
        cs.fecha_inicio,
        cs.fecha_fin,
        cs.estado
    FROM cliente_servicios cs
    INNER JOIN servicios s
        ON cs.id_servicio = s.id_servicio
    WHERE cs.id_cliente = ?
    ORDER BY cs.fecha_inicio DESC
    """, (cliente['id_cliente'],))

    total_disponibles = len(servicios_disponibles)
    total_comprados = len(servicios_comprados)
    total_activos = sum(1 for s in servicios_comprados if s.get('estado') == 'ACTIVO')
    total_suspendidos = sum(1 for s in servicios_comprados if s.get('estado') == 'SUSPENDIDO')

    for servicio in servicios_comprados:
        if servicio.get('fecha_inicio'):
            try:
                servicio['fecha_inicio'] = servicio['fecha_inicio'].strftime('%Y-%m-%d')
            except Exception:
                servicio['fecha_inicio'] = str(servicio['fecha_inicio'])[:10]
        if servicio.get('fecha_fin'):
            try:
                servicio['fecha_fin'] = servicio['fecha_fin'].strftime('%Y-%m-%d')
            except Exception:
                servicio['fecha_fin'] = str(servicio['fecha_fin'])[:10]

    return render_template(
        'servicios.html',
        servicios=servicios_disponibles,
        comprados=servicios_comprados,
        total_disponibles=total_disponibles,
        total_comprados=total_comprados,
        total_activos=total_activos,
        total_suspendidos=total_suspendidos,
        current_user=user
    )

@app.route('/servicios/<int:id>')
@require_role('CLIENTE')
def servicio_detalle(id):
    servicio = fetchone(
        "SELECT * FROM servicios WHERE id_servicio = ?",
        (id,)
    )

    if servicio is None:
        flash('Servicio no encontrado', 'error')
        return redirect(url_for('servicios'))

    return render_template(
        'servicio_detalle.html',
        servicio=servicio,
        current_user=current_user()
    )

@app.route('/servicios/comprar', methods=['POST'])
@require_role('CLIENTE')
def comprar_servicio():

    user = current_user()
    cliente = fetchone(
        "SELECT id_cliente FROM clientes WHERE id_usuario = ?",
        (user['id'],)
    )

    id_servicio = request.form['id_servicio']
    fecha_inicio = date.today()
    fecha_fin = fecha_inicio + timedelta(days=30)

    try:
        execute("""
        INSERT INTO cliente_servicios(
            id_cliente,
            id_servicio,
            estado,
            fecha_inicio,
            fecha_fin
        )
        VALUES(?, ?, 'ACTIVO', ?, ?)
        """, (
            cliente['id_cliente'],
            id_servicio,
            fecha_inicio,
            fecha_fin
        ))

        flash('Servicio comprado correctamente. Revisa tu panel de servicios.', 'success')
    except Exception as e:
        flash(str(e), 'error')

    return redirect(url_for('servicios'))

# =====================================================
# CLIENTES
# =====================================================

@app.route('/clientes')
@require_role('ADMIN', 'EMPLEADO')
def clientes():

    lista = fetchall("""
    SELECT
        c.id_cliente,
        u.nombre,
        u.correo,
        c.telefono,
        c.empresa,
        n.nombre AS nivel
    FROM clientes c
    INNER JOIN usuarios u
        ON c.id_usuario = u.id_usuario
    INNER JOIN niveles_cliente n
        ON c.id_nivel = n.id_nivel
    ORDER BY u.nombre
    """)

    return render_template(
        'clientes.html',
        clientes=lista,
        current_user=current_user()
    )

@app.route('/clientes/editar/<int:id>', methods=['GET', 'POST'])
@require_role('ADMIN')
def editar_cliente(id):

    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        empresa = request.form['empresa']
        telefono = request.form['telefono']

        try:
            execute("""
            UPDATE usuarios
            SET nombre = ?, correo = ?
            WHERE id_usuario = (
                SELECT id_usuario FROM clientes WHERE id_cliente = ?
            )
            """, (nombre, correo, id))

            execute("""
            UPDATE clientes
            SET empresa = ?, telefono = ?
            WHERE id_cliente = ?
            """, (empresa, telefono, id))

            flash('Cliente actualizado correctamente', 'success')
            return redirect(url_for('clientes'))
        except Exception as e:
            flash(str(e), 'error')

    cliente_editar = fetchone("""
    SELECT
        c.id_cliente,
        u.nombre,
        u.correo,
        c.empresa,
        c.telefono
    FROM clientes c
    INNER JOIN usuarios u
        ON c.id_usuario = u.id_usuario
    WHERE c.id_cliente = ?
    """, (id,))

    lista = fetchall("""
    SELECT
        c.id_cliente,
        u.nombre,
        u.correo,
        c.telefono,
        c.empresa,
        n.nombre AS nivel
    FROM clientes c
    INNER JOIN usuarios u
        ON c.id_usuario = u.id_usuario
    INNER JOIN niveles_cliente n
        ON c.id_nivel = n.id_nivel
    ORDER BY u.nombre
    """)

    return render_template(
        'clientes.html',
        clientes=lista,
        cliente_editar=cliente_editar,
        current_user=current_user()
    )

@app.route('/clientes/eliminar/<int:id>', methods=['POST'])
@require_role('ADMIN')
def eliminar_cliente(id):

    try:
        usuario = fetchone(
            "SELECT id_usuario FROM clientes WHERE id_cliente = ?",
            (id,)
        )

        if usuario is None:
            flash('Cliente no encontrado', 'error')
            return redirect(url_for('clientes'))

        execute("DELETE FROM detalle_venta WHERE id_venta IN (SELECT id_venta FROM ventas WHERE id_cliente = ?)", (id,))
        execute("DELETE FROM ventas WHERE id_cliente = ?", (id,))
        execute("DELETE FROM cliente_servicios WHERE id_cliente = ?", (id,))
        execute("DELETE FROM historial_niveles_cliente WHERE id_cliente = ?", (id,))
        execute("DELETE FROM clientes WHERE id_cliente = ?", (id,))
        execute("DELETE FROM usuarios WHERE id_usuario = ?", (usuario['id_usuario'],))

        flash('Cliente eliminado correctamente', 'success')
    except Exception as e:
        flash(str(e), 'error')

    return redirect(url_for('clientes'))

# =====================================================
# REGISTRAR CLIENTE
# =====================================================

@app.route('/clientes/registrar', methods=['POST'])
@require_role('ADMIN')
def registrar_cliente():

    nombre = request.form['nombre']

    correo = request.form['correo']

    password = request.form['password']

    empresa = request.form['empresa']

    telefono = request.form['telefono']

    try:

        execute("""
        INSERT INTO usuarios(
            nombre,
            correo,
            password_hash,
            id_rol
        )
        VALUES(
            ?,
            ?,
            ?,
            3
        )
        """, (
            nombre,
            correo,
            hash_password(password),
        ))

        usuario = fetchone(
            "SELECT id_usuario FROM usuarios WHERE correo = ?",
            (correo,)
        )

        execute("""
        INSERT INTO clientes(
            id_usuario,
            empresa,
            telefono
        )
        VALUES(
            ?,
            ?,
            ?
        )
        """, (
            usuario['id_usuario'],
            empresa,
            telefono
        ))

        flash(
            'Cliente registrado correctamente',
            'success'
        )

    except Exception as e:

        flash(
            str(e),
            'error'
        )

    return redirect(url_for('clientes'))

# =====================================================
# EMPLEADOS
# =====================================================

@app.route('/empleados')
@require_role('ADMIN')
def empleados():

    lista = fetchall("""
    SELECT
        e.id_empleado,
        u.nombre,
        u.correo,
        d.nombre AS departamento,
        e.cargo,
        e.salario
    FROM empleados e
    INNER JOIN usuarios u
        ON e.id_usuario = u.id_usuario
    INNER JOIN departamentos d
        ON e.id_departamento = d.id_departamento
    ORDER BY u.nombre
    """)

    departamentos = fetchall(
        "SELECT id_departamento, nombre FROM departamentos ORDER BY nombre"
    )

    return render_template(
        'empleados.html',
        empleados=lista,
        departamentos=departamentos,
        current_user=current_user()
    )

@app.route('/empleados/registrar', methods=['POST'])
@require_role('ADMIN')
def registrar_empleado():

    nombre = request.form['nombre']
    correo = request.form['correo']
    password = request.form['password']
    id_departamento = request.form['id_departamento']
    cargo = request.form['cargo']
    salario = request.form['salario']

    try:
        execute("""
        INSERT INTO usuarios(
            nombre,
            correo,
            password_hash,
            id_rol
        ) VALUES(?, ?, ?, 2)
        """, (
            nombre,
            correo,
            hash_password(password)
        ))

        usuario = fetchone(
            "SELECT id_usuario FROM usuarios WHERE correo = ?",
            (correo,)
        )

        execute("""
        INSERT INTO empleados(
            id_usuario,
            id_departamento,
            cargo,
            salario
        ) VALUES(?, ?, ?, ?)
        """, (
            usuario['id_usuario'],
            id_departamento,
            cargo,
            salario
        ))

        flash('Empleado registrado correctamente', 'success')
    except Exception as e:
        flash(str(e), 'error')

    return redirect(url_for('empleados'))

# =====================================================
# VENTAS
# =====================================================

@app.route('/ventas')
@require_role('ADMIN', 'EMPLEADO')
def ventas():

    lista = fetchall("""
    SELECT
        v.id_venta,
        u.nombre AS cliente,
        s.nombre AS servicio,
        s.precio AS precio_servicio,
        dv.cantidad,
        v.total,
        v.fecha,
        v.estado_pago
    FROM ventas v
    INNER JOIN clientes c
        ON v.id_cliente = c.id_cliente
    INNER JOIN usuarios u
        ON c.id_usuario = u.id_usuario
    INNER JOIN detalle_venta dv
        ON v.id_venta = dv.id_venta
    INNER JOIN servicios s
        ON dv.id_servicio = s.id_servicio
    ORDER BY v.fecha DESC
    """)

    for venta in lista:
        fecha = venta.get('fecha')
        if fecha is not None:
            try:
                venta['fecha'] = fecha.strftime('%Y-%m-%d')
            except Exception:
                venta['fecha'] = str(fecha)[:10]

    clientes = fetchall("""
    SELECT
        c.id_cliente,
        u.nombre
    FROM clientes c
    INNER JOIN usuarios u
        ON c.id_usuario = u.id_usuario
    ORDER BY u.nombre
    """)

    servicios = fetchall(
        "SELECT * FROM servicios"
    )

    campanias = fetchall(
        "SELECT * FROM campanias"
    )

    return render_template(
        'ventas.html',
        ventas=lista,
        clientes=clientes,
        servicios=servicios,
        campanias=campanias,
        current_user=current_user()
    )

# =====================================================
# REGISTRAR VENTA
# =====================================================

@app.route('/ventas/registrar', methods=['POST'])
@require_role('ADMIN', 'EMPLEADO')
def registrar_venta():

    id_cliente = request.form['id_cliente']

    id_campania = request.form['id_campania']

    id_servicio = request.form['id_servicio']

    cantidad = request.form['cantidad']

    try:

        execute(
            "EXEC registrar_venta ?, ?, ?, ?",
            (
                id_cliente,
                id_campania,
                id_servicio,
                cantidad
            )
        )

        flash(
            'Venta registrada correctamente',
            'success'
        )

    except Exception as e:

        flash(
            str(e),
            'error'
        )

    return redirect(url_for('ventas'))

# =====================================================
# CAMPANIAS
# =====================================================

@app.route('/campanias')
@require_role('ADMIN')
def campanias():

    lista = fetchall("""
    SELECT
        id_campania,
        nombre,
        medio_contacto,
        presupuesto,
        fecha_inicio,
        fecha_fin,
        objetivo
    FROM campanias
    ORDER BY fecha_inicio DESC
    """)

    return render_template(
        'campanias.html',
        campanias=lista,
        current_user=current_user()
    )


@app.route('/campanias/registrar', methods=['POST'])
@require_role('ADMIN')
def registrar_campania():

    nombre = request.form['nombre']
    medio_contacto = request.form['medio_contacto']
    presupuesto = request.form['presupuesto']
    fecha_inicio = request.form['fecha_inicio']
    fecha_fin = request.form['fecha_fin']
    objetivo = request.form['objetivo']

    try:
        execute("""
        INSERT INTO campanias(
            nombre,
            medio_contacto,
            presupuesto,
            fecha_inicio,
            fecha_fin,
            objetivo
        )
        VALUES(
            ?, ?, ?, ?, ?, ?
        )
        """, (
            nombre,
            medio_contacto,
            presupuesto,
            fecha_inicio,
            fecha_fin,
            objetivo
        ))

        flash('Campaña registrada correctamente', 'success')
    except Exception as e:
        flash(str(e), 'error')

    return redirect(url_for('campanias'))

@app.route('/campanias/editar/<int:id>', methods=['GET', 'POST'])
@require_role('ADMIN')
def editar_campania(id):

    if request.method == 'POST':
        nombre = request.form['nombre']
        medio_contacto = request.form['medio_contacto']
        presupuesto = request.form['presupuesto']
        fecha_inicio = request.form['fecha_inicio']
        fecha_fin = request.form['fecha_fin']
        objetivo = request.form['objetivo']

        try:
            execute("""
            UPDATE campanias
            SET nombre = ?, medio_contacto = ?, presupuesto = ?, fecha_inicio = ?, fecha_fin = ?, objetivo = ?
            WHERE id_campania = ?
            """, (
                nombre,
                medio_contacto,
                presupuesto,
                fecha_inicio,
                fecha_fin,
                objetivo,
                id
            ))

            flash('Campaña actualizada correctamente', 'success')
            return redirect(url_for('campanias'))
        except Exception as e:
            flash(str(e), 'error')

    campania_editar = fetchone("""
    SELECT
        id_campania,
        nombre,
        medio_contacto,
        presupuesto,
        fecha_inicio,
        fecha_fin,
        objetivo
    FROM campanias
    WHERE id_campania = ?
    """, (id,))

    campanias = fetchall("""
    SELECT
        id_campania,
        nombre,
        medio_contacto,
        presupuesto,
        fecha_inicio,
        fecha_fin,
        objetivo
    FROM campanias
    ORDER BY fecha_inicio DESC
    """)

    return render_template(
        'campanias.html',
        campanias=campanias,
        campania_editar=campania_editar,
        current_user=current_user()
    )

@app.route('/campanias/eliminar/<int:id>', methods=['POST'])
@require_role('ADMIN')
def eliminar_campania(id):

    try:
        execute("UPDATE ventas SET id_campania = NULL WHERE id_campania = ?", (id,))
        execute("DELETE FROM campanias WHERE id_campania = ?", (id,))
        flash('Campaña eliminada correctamente', 'success')
    except Exception as e:
        flash(str(e), 'error')

    return redirect(url_for('campanias'))


# =====================================================
# REPORTES
# =====================================================

def _parse_report_filters():
    fecha_inicio = request.args.get('fecha_inicio') or '1900-01-01'
    fecha_fin = request.args.get('fecha_fin') or '2100-12-31'
    campania = request.args.get('campania')

    return fecha_inicio, fecha_fin, campania


@app.route('/reportes')
@require_role('ADMIN')
def reportes():

    fecha_inicio, fecha_fin, campania = _parse_report_filters()

    params = [fecha_inicio, fecha_fin]
    where_campania = ''
    if campania:
        where_campania = 'AND v.id_campania = ?'
        params.append(campania)

    mejores_clientes = fetchall(f"""
    SELECT
        c.id_cliente,
        u.nombre,
        n.nombre AS nivel,
        SUM(v.total) AS total_compras
    FROM clientes c
    INNER JOIN usuarios u ON c.id_usuario = u.id_usuario
    INNER JOIN niveles_cliente n ON c.id_nivel = n.id_nivel
    INNER JOIN ventas v ON c.id_cliente = v.id_cliente
    WHERE v.fecha BETWEEN ? AND ?
    {where_campania}
    GROUP BY c.id_cliente, u.nombre, n.nombre
    """, tuple(params))

    ventas_mensuales = fetchall(f"""
    SELECT
        YEAR(v.fecha) AS anio,
        MONTH(v.fecha) AS mes,
        SUM(v.total) AS total_ventas
    FROM ventas v
    WHERE v.fecha BETWEEN ? AND ?
    {where_campania}
    GROUP BY YEAR(v.fecha), MONTH(v.fecha)
    ORDER BY YEAR(v.fecha) DESC, MONTH(v.fecha) DESC
    """, tuple(params))

    rendimiento_params = [fecha_inicio, fecha_fin]
    rendimiento_where = ''
    if campania:
        rendimiento_where = 'WHERE c.id_campania = ?'
        rendimiento_params.append(campania)

    rendimiento = fetchall(f"""
    SELECT
        c.id_campania,
        c.nombre,
        c.medio_contacto,
        COUNT(v.id_venta) AS ventas_generadas,
        SUM(v.total) AS ingresos
    FROM campanias c
    LEFT JOIN ventas v ON c.id_campania = v.id_campania
        AND v.fecha BETWEEN ? AND ?
    {rendimiento_where}
    GROUP BY c.id_campania, c.nombre, c.medio_contacto
    ORDER BY ingresos DESC
    """, tuple(rendimiento_params))

    campanias = fetchall(
        "SELECT id_campania, nombre FROM campanias ORDER BY nombre"
    )

    return render_template(
        'reportes.html',
        mejores_clientes=mejores_clientes,
        ventas_mensuales=ventas_mensuales,
        rendimiento=rendimiento,
        campanias=campanias,
        filters={
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'campania': campania
        },
        current_user=current_user()
    )


@app.route('/reportes/export/<report_type>')
@require_role('ADMIN')
def export_report(report_type):

    fecha_inicio, fecha_fin, campania = _parse_report_filters()

    if report_type == 'clientes':
        params = [fecha_inicio, fecha_fin]
        sql = """
        SELECT
            c.id_cliente,
            u.nombre,
            n.nombre AS nivel,
            SUM(v.total) AS total_compras
        FROM clientes c
        INNER JOIN usuarios u ON c.id_usuario = u.id_usuario
        INNER JOIN niveles_cliente n ON c.id_nivel = n.id_nivel
        INNER JOIN ventas v ON c.id_cliente = v.id_cliente
        WHERE v.fecha BETWEEN ? AND ?
        """
        if campania:
            sql += ' AND v.id_campania = ?'
            params.append(campania)
        sql += ' GROUP BY c.id_cliente, u.nombre, n.nombre'

    elif report_type == 'mensuales':
        params = [fecha_inicio, fecha_fin]
        sql = """
        SELECT
            YEAR(fecha) AS anio,
            MONTH(fecha) AS mes,
            SUM(total) AS total_ventas
        FROM ventas
        WHERE fecha BETWEEN ? AND ?
        GROUP BY YEAR(fecha), MONTH(fecha)
        ORDER BY YEAR(fecha) DESC, MONTH(fecha) DESC
        """

    elif report_type == 'campanias':
        params = [fecha_inicio, fecha_fin]
        sql = """
        SELECT
            c.id_campania,
            c.nombre,
            c.medio_contacto,
            COUNT(v.id_venta) AS ventas_generadas,
            SUM(v.total) AS ingresos
        FROM campanias c
        LEFT JOIN ventas v ON c.id_campania = v.id_campania
            AND v.fecha BETWEEN ? AND ?
        """
        if campania:
            sql += ' WHERE c.id_campania = ?'
            params.append(campania)
        sql += ' GROUP BY c.id_campania, c.nombre, c.medio_contacto ORDER BY ingresos DESC'

    else:
        flash('Tipo de reporte no válido', 'error')
        return redirect(url_for('reportes'))

    rows = fetchall(sql, tuple(params))

    output = io.StringIO()
    writer = csv.writer(output)
    if rows:
        writer.writerow(rows[0].keys())
        for row in rows:
            writer.writerow([row[col] for col in row.keys()])

    content = output.getvalue()
    filename = f'reporte_{report_type}.csv'
    return Response(
        content,
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename={filename}'
        }
    )


# =====================================================
# PERFIL
# =====================================================

@app.route('/mi_perfil')
@login_required
def mi_perfil():

    user = current_user()
    perfil = None

    if user['rol'] == 'CLIENTE':
        perfil = fetchone("""
        SELECT
            u.nombre,
            u.correo,
            r.nombre_rol AS rol,
            c.empresa,
            c.telefono,
            n.nombre AS nivel,
            u.fecha_registro,
            u.estado
        FROM clientes c
        INNER JOIN usuarios u
            ON c.id_usuario = u.id_usuario
        INNER JOIN niveles_cliente n
            ON c.id_nivel = n.id_nivel
        INNER JOIN roles r
            ON u.id_rol = r.id_rol
        WHERE u.id_usuario = ?
        """, (user['id'],))
    else:
        perfil = fetchone("""
        SELECT
            u.nombre,
            u.correo,
            r.nombre_rol AS rol,
            NULL AS empresa,
            NULL AS telefono,
            NULL AS nivel,
            u.fecha_registro,
            u.estado
        FROM usuarios u
        INNER JOIN roles r
            ON u.id_rol = r.id_rol
        WHERE u.id_usuario = ?
        """, (user['id'],))

    if perfil and perfil['fecha_registro'] is not None:
        try:
            perfil['fecha_registro'] = perfil['fecha_registro'].strftime('%d/%m/%Y')
        except AttributeError:
            perfil['fecha_registro'] = str(perfil['fecha_registro'])

    return render_template(
        'mi_perfil.html',
        perfil=perfil,
        current_user=current_user()
    )

# =====================================================
# MAIN
# =====================================================

if __name__ == '__main__':

    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000
    )