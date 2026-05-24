import hashlib
import functools

from flask import (
    session,
    redirect,
    url_for,
    flash
)

PERMISOS = {

    'ADMIN': {
        'dashboard',
        'clientes',
        'ventas',
        'campanias',
        'reportes'
    },

    'EMPLEADO': {
        'dashboard',
        'clientes',
        'ventas'
    },

    'CLIENTE': {
        'dashboard',
        'mi_perfil'
    }
}


def hash_password(password):

    return hashlib.sha256(
        password.encode()
    ).hexdigest().upper()



def check_password(password, hashed):

    return hash_password(password) == hashed.upper()



def login_user(usuario):

    session['user_id'] = usuario['id_usuario']

    session['nombre'] = usuario['nombre']

    session['rol'] = usuario['nombre_rol']



def logout_user():

    session.clear()



def current_user():

    if 'user_id' not in session:
        return None

    return {
        'id': session['user_id'],
        'nombre': session['nombre'],
        'rol': session['rol']
    }



def login_required(f):

    @functools.wraps(f)
    def wrapper(*args, **kwargs):

        if not current_user():

            flash(
                'Debes iniciar sesión',
                'error'
            )

            return redirect(url_for('login'))

        return f(*args, **kwargs)

    return wrapper



def require_role(*roles):

    def decorator(f):

        @functools.wraps(f)
        @login_required
        def wrapper(*args, **kwargs):

            user = current_user()

            if user['rol'] not in roles:

                flash(
                    'No tienes permisos para ver esta página',
                    'error'
                )

                return redirect(
                    url_for('unauthorized')
                )

            return f(*args, **kwargs)

        return wrapper

    return decorator
