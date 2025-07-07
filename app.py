import os
from datetime import datetime, date, time
from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from config import Config
from bson import ObjectId
from pymongo import MongoClient

from datetime import datetime

def parse_datetime_fields(tareas):
    for tarea in tareas:
        # Convertir fecha_recordatorio a datetime.date si es string
        if 'fecha_recordatorio' in tarea and isinstance(tarea['fecha_recordatorio'], str):
            try:
                tarea['fecha_recordatorio'] = datetime.strptime(tarea['fecha_recordatorio'], '%Y-%m-%d').date()
            except Exception:
                tarea['fecha_recordatorio'] = None

        # Convertir hora_recordatorio a datetime.time si es string
        if 'hora_recordatorio' in tarea and isinstance(tarea['hora_recordatorio'], str):
            try:
                tarea['hora_recordatorio'] = datetime.strptime(tarea['hora_recordatorio'], '%H:%M').time()
            except Exception:
                tarea['hora_recordatorio'] = None
    return tareas




app = Flask(__name__)
app.config.from_object(Config)

# Conexión Mongo
client = MongoClient(app.config['MONGO_URI'])
db = client[app.config['MONGO_DBNAME']]

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
from datetime import datetime

def parse_datetime_fields(tareas):
    for tarea in tareas:
        # Convertir fecha_creacion de string a datetime si es necesario
        if isinstance(tarea.get('fecha_creacion'), str):
            try:
                tarea['fecha_creacion'] = datetime.fromisoformat(tarea['fecha_creacion'])
            except Exception:
                tarea['fecha_creacion'] = None

        # Convertir fecha_modificacion
        if isinstance(tarea.get('fecha_modificacion'), str):
            try:
                tarea['fecha_modificacion'] = datetime.fromisoformat(tarea['fecha_modificacion'])
            except Exception:
                tarea['fecha_modificacion'] = None

        # Convertir fecha_recordatorio si existe y es string
        if isinstance(tarea.get('fecha_recordatorio'), str):
            try:
                tarea['fecha_recordatorio'] = datetime.fromisoformat(tarea['fecha_recordatorio']).date()
            except Exception:
                tarea['fecha_recordatorio'] = None

        # Convertir hora_recordatorio si existe y es string
        if isinstance(tarea.get('hora_recordatorio'), str):
            try:
                tarea['hora_recordatorio'] = datetime.strptime(tarea['hora_recordatorio'], '%H:%M:%S').time()
            except Exception:
                tarea['hora_recordatorio'] = None
    return tareas

# Clase de usuario actual para Flask-Login
from flask_login import UserMixin

class UserMongo(UserMixin):
    def __init__(self, data, tipo='usuario'):
        self.data = data
        self.tipo = tipo  # 'usuario' o 'maestro'

    def get_id(self):
        # Devolver el _id como string para que flask-login lo use
        if self.tipo == 'maestro':
            return f"maestro-{str(self.data['_id'])}"
        return str(self.data['_id'])

    @property
    def id(self):
        return str(self.data['_id'])

    @property
    def nombre(self):
        return self.data.get('nombre') if self.tipo == 'usuario' else self.data.get('nombre_maestro')

    @property
    def email(self):
        return self.data.get('email') if self.tipo == 'usuario' else self.data.get('correo')

    @property
    def imagen(self):
        return self.data.get('imagen') if self.tipo == 'usuario' else self.data.get('foto_perfil')

    @property
    def codigo_clase(self):
        if self.tipo == 'maestro':
            return self.data.get('codigo_clase')
        return None

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.data['contrasena'], password)

    def es_maestro(self):
        return self.tipo == 'maestro'


from bson.objectid import ObjectId
from bson.errors import InvalidId

@login_manager.user_loader
def load_user(user_id):
    if str(user_id).startswith('maestro-'):
        maestro_id_str = user_id.split('-', 1)[1]
        try:
            oid = ObjectId(maestro_id_str)
            maestro = db.clase.find_one({"_id": oid})
            if maestro:
                return UserMongo(maestro, tipo='maestro')
        except Exception:
            return None
    else:
        try:
            oid = ObjectId(user_id)
            usuario = db.usuarios.find_one({"_id": oid})
            if usuario:
                return UserMongo(usuario, tipo='usuario')
        except Exception:
            return None
    return None


@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.es_maestro():
            return redirect(url_for('maestros_dashboard'))
        else:
            return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        nombre = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        imagen_archivo = request.files.get('profile_image')

        if not nombre or not email or not password or not confirm_password:
            flash('Todos los campos son obligatorios.', 'error')
            return render_template('register.html')
        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'error')
            return render_template('register.html')
        if db.usuarios.find_one({'nombre': nombre}):
            flash('El nombre de usuario ya existe.', 'error')
            return render_template('register.html')
        if db.usuarios.find_one({'email': email}):
            flash('El email ya está registrado.', 'error')
            return render_template('register.html')

        filename = 'default.jpg'
        if imagen_archivo and imagen_archivo.filename != '':
            filename = secure_filename(imagen_archivo.filename)
            ruta_upload = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            imagen_archivo.save(ruta_upload)

        hashed_password = generate_password_hash(password)
        usuario = {
            'nombre': nombre,
            'email': email,
            'contrasena': hashed_password,
            'imagen': filename
        }
        try:
            result = db.usuarios.insert_one(usuario)
            flash('¡Registro exitoso! Por favor, inicia sesión.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Error al registrar el usuario: {e}', 'error')
            return render_template('register.html')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.es_maestro():
            return redirect(url_for('maestros_dashboard'))
        else:
            return redirect(url_for('dashboard'))

    if request.method == 'POST':
        nombre = request.form['username']
        password = request.form['password']

        if nombre == 'admin' and password == '1234':
            return redirect(url_for('loginmaestro'))

        user = db.usuarios.find_one({'nombre': nombre})
        if not user or not check_password_hash(user['contrasena'], password):
            flash('Usuario o contraseña incorrectos.', 'error')
            return render_template('login.html')

        login_user(UserMongo(user))
        flash('¡Has iniciado sesión exitosamente!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('login'))

from datetime import datetime

from datetime import datetime

from datetime import datetime

from flask import render_template
from flask_login import login_required, current_user
from datetime import datetime
from bson.objectid import ObjectId
from datetime import datetime, timedelta


from flask import render_template, flash
from flask_login import login_required, current_user
from datetime import datetime
from bson import ObjectId

@app.route('/dashboard')
@login_required
def dashboard():
    tareas_cursor = db.tareas.find({
        'usuario_id': str(current_user.data['_id']),
        'papelera': False
    }).sort('fecha_modificacion', -1)

    tareas = []
    for tarea in tareas_cursor:
        tarea['_id'] = str(tarea['_id'])  # MongoDB ObjectId a str
        for campo in ['fecha_creacion', 'fecha_modificacion', 'fecha_recordatorio', 'hora_recordatorio']:
            if campo in tarea and tarea[campo] is not None:
                tarea[campo] = str(tarea[campo])
        tareas.append(tarea)

    return render_template(
        'index.html',
        username=current_user.nombre,
        imagen=current_user.imagen,
        tareas=tareas
    )

@app.route('/search_tasks')
@login_required
def search_tasks():
    query = request.args.get('query', '').strip()
    if not query:
        return redirect(url_for('dashboard'))

    tareas = list(db.tareas.find({
        'usuario_id': str(current_user.data['_id']),
        'papelera': False,
        '$or': [
            {'titulo': {'$regex': query, '$options': 'i'}},
            {'contenido': {'$regex': query, '$options': 'i'}}
        ]
    }).sort('fecha_modificacion', -1))

    return render_template('index.html', tareas=tareas, search_query=query, username=current_user.nombre, imagen=current_user.imagen)

@app.route('/create_task', methods=['POST'])
@login_required
def create_task():
    titulo = request.form['titulo']
    contenido = request.form.get('contenido')
    if not titulo.strip():
        flash('El título de la tarea no puede estar vacío.', 'error')
        return redirect(url_for('dashboard'))

    fecha_recordatorio = request.form.get('fecha_recordatorio')
    hora_recordatorio = request.form.get('hora_recordatorio')

    tarea = {
        'titulo': titulo,
        'contenido': contenido,
        'fecha_creacion': datetime.utcnow(),
        'fecha_modificacion': datetime.utcnow(),
        'fecha_recordatorio': fecha_recordatorio if fecha_recordatorio else None,
        'hora_recordatorio': hora_recordatorio if hora_recordatorio else None,
        'usuario_id': str(current_user.data['_id']),
        'usuario_nombre': current_user.nombre,
        'usuario_email': current_user.email,
        'papelera': False
    }
    try:
        db.tareas.insert_one(tarea)
        flash('Tarea creada exitosamente.', 'success')
    except Exception as e:
        flash(f'Error al crear tarea: {e}', 'error')
    return redirect(url_for('dashboard'))

@app.route('/edit_task/<task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    print(f"Editando tarea con ID: {task_id}")
    tarea = db.tareas.find_one({'_id': ObjectId(task_id), 'usuario_id': str(current_user.data['_id'])})
    if not tarea:
        flash('Tarea no encontrada o no tienes permiso para editarla.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        titulo = request.form['titulo']
        contenido = request.form.get('contenido')
        fecha_recordatorio = request.form.get('fecha_recordatorio') or None
        hora_recordatorio = request.form.get('hora_recordatorio') or None

        if not titulo.strip():
            flash('El título de la tarea no puede estar vacío.', 'error')
            return render_template('edit_task.html', tarea=tarea)

        db.tareas.update_one(
            {'_id': ObjectId(task_id)},
            {'$set': {
                'titulo': titulo,
                'contenido': contenido,
                'fecha_recordatorio': fecha_recordatorio,
                'hora_recordatorio': hora_recordatorio,
                'fecha_modificacion': datetime.utcnow()
            }}
        )
        flash('Tarea actualizada exitosamente.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_task.html', tarea=tarea)

@app.route('/delete_task/<task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    tarea = db.tareas.find_one({'_id': ObjectId(task_id), 'usuario_id': str(current_user.data['_id'])})
    if not tarea:
        flash('Tarea no encontrada o no tienes permiso para eliminarla.', 'error')
        return redirect(url_for('dashboard'))

    db.tareas.update_one({'_id': ObjectId(task_id)}, {'$set': {'papelera': True}})
    flash('Tarea movida a papelera.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/papelera')
@login_required
def papelera():
    tareas_eliminadas = list(db.tareas.find({'usuario_id': str(current_user.data['_id']), 'papelera': True}).sort('fecha_modificacion', -1))
    return render_template('papelera.html', tareas=tareas_eliminadas)

@app.route('/restaurar/<task_id>', methods=['POST'])
@login_required
def restaurar_tarea(task_id):
    db.tareas.update_one({'_id': ObjectId(task_id), 'usuario_id': str(current_user.data['_id'])}, {'$set': {'papelera': False}})
    flash('Tarea restaurada correctamente.', 'success')
    return redirect(url_for('papelera'))

@app.route('/eliminar_permanente/<task_id>', methods=['POST'])
@login_required
def eliminar_permanente(task_id):
    db.tareas.delete_one({'_id': ObjectId(task_id), 'usuario_id': str(current_user.data['_id'])})
    flash('Tarea eliminada permanentemente.', 'success')
    return redirect(url_for('papelera'))

@app.route('/recordatorios')
@login_required
def recordatorios():
    tareas_con_recordatorio = list(db.tareas.find({
        'usuario_id': str(current_user.data['_id']),
        'papelera': False,
        '$or': [
            {'fecha_recordatorio': {'$ne': None}},
            {'hora_recordatorio': {'$ne': None}}
        ]
    }).sort('fecha_modificacion', -1))

    return render_template('recordatorio.html', tareas=tareas_con_recordatorio, username=current_user.nombre, imagen=current_user.imagen)
@app.route('/loginmaestro', methods=['GET', 'POST'])
def loginmaestro():
    if current_user.is_authenticated and current_user.es_maestro():
        return redirect(url_for('maestros_dashboard'))

    if request.method == 'POST':
        correo = request.form['correo']
        password = request.form['password']
        maestro = db.clase.find_one({'correo': correo})

        if not maestro or not check_password_hash(maestro['contrasena'], password):
            flash('Correo o contraseña incorrectos.', 'error')
            return render_template('loginmaestro.html')

        login_user(UserMongo(maestro, tipo='maestro'))
        flash('¡Has iniciado sesión como maestro!', 'success')
        return redirect(url_for('maestros_dashboard'))
    return render_template('loginmaestro.html')

@app.route('/registermaestro', methods=['GET', 'POST'])
def registermaestro():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        codigo_clase = request.form['codigo_clase']
        materia = request.form['materia']
        imagen_archivo = request.files.get('profile_image')

        if not all([nombre, correo, password, confirm_password, codigo_clase, materia]):
            flash('Todos los campos son obligatorios.', 'error')
            return render_template('registermaestro.html')
        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'error')
            return render_template('registermaestro.html')
        if db.clase.find_one({'correo': correo}):
            flash('El correo ya está registrado.', 'error')
            return render_template('registermaestro.html')

        filename = 'default.jpg'
        if imagen_archivo and imagen_archivo.filename != '':
            filename = secure_filename(imagen_archivo.filename)
            ruta_upload = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            imagen_archivo.save(ruta_upload)

        maestro = {
            'nombre_maestro': nombre,
            'correo': correo,
            'contrasena': generate_password_hash(password),
            'codigo_clase': codigo_clase,
            'materia': materia,
            'foto_perfil': filename
        }

        try:
            db.clase.insert_one(maestro)
            flash('¡Registro exitoso de maestro! Por favor inicia sesión.', 'success')
            return redirect(url_for('loginmaestro'))
        except Exception as e:
            flash(f'Error al registrar maestro: {e}', 'error')
            return render_template('registermaestro.html')
    return render_template('registermaestro.html')

@app.route('/maestros')
@login_required
def maestros_dashboard():
    if not current_user.es_maestro():
        flash('Acceso denegado.', 'error')
        return redirect(url_for('dashboard'))

    tareas = list(db.tarea_clase.find({'codigo_clase': current_user.data['codigo_clase']}).sort('fecha_modificacion', -1))
    tareas = parse_datetime_fields(tareas)  # <--- Aquí aplicamos la conversión

    return render_template('maestros.html', nombre=current_user.nombre, imagen=current_user.imagen, tareas=tareas)


from datetime import datetime

@app.route('/create_task_maestro', methods=['POST'])
@login_required
def create_task_maestro():
    # Verificar que el usuario tenga código de clase (es maestro)
    if not hasattr(current_user, 'codigo_clase') or not current_user.codigo_clase:
        flash('Acceso denegado.', 'error')
        return redirect(url_for('dashboard'))

    titulo = request.form['titulo']
    contenido = request.form.get('contenido')
    fecha_recordatorio_str = request.form.get('fecha_recordatorio')
    hora_recordatorio_str = request.form.get('hora_recordatorio')

    fecha_recordatorio_obj = None
    hora_recordatorio_obj = None

    if fecha_recordatorio_str:
        try:
            fecha_recordatorio_obj = datetime.strptime(fecha_recordatorio_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Formato de fecha inválido.', 'error')
            return redirect(url_for('maestros_dashboard'))
    if hora_recordatorio_str:
        try:
            hora_recordatorio_obj = datetime.strptime(hora_recordatorio_str, '%H:%M').time()
        except ValueError:
            flash('Formato de hora inválido.', 'error')
            return redirect(url_for('maestros_dashboard'))

    nueva_tarea = {
        'titulo': titulo,
        'contenido': contenido,
        'fecha_creacion': datetime.utcnow(),
        'fecha_modificacion': datetime.utcnow(),
        'fecha_recordatorio': fecha_recordatorio_obj,
        'hora_recordatorio': hora_recordatorio_obj,
        'codigo_clase': current_user.codigo_clase
    }
    try:
        db.tarea_clase.insert_one(nueva_tarea)
        flash('Tarea creada exitosamente.', 'success')
    except Exception as e:
        flash(f'Error al crear tarea: {e}', 'error')

    return redirect(url_for('maestros_dashboard'))


@app.route('/edit_task_maestro/<task_id>', methods=['GET', 'POST'])
@login_required
def edit_task_maestro(task_id):
    if not current_user.es_maestro():
        flash('Acceso denegado.', 'error')
        return redirect(url_for('dashboard'))

    tarea = db.tarea_clase.find_one({'_id': ObjectId(task_id), 'codigo_clase': current_user.data['codigo_clase']})
    if not tarea:
        flash('Tarea no encontrada o no tienes permiso para editarla.', 'error')
        return redirect(url_for('maestros_dashboard'))

    if request.method == 'POST':
        titulo = request.form['titulo']
        contenido = request.form.get('contenido')
        fecha_recordatorio = request.form.get('fecha_recordatorio') or None
        hora_recordatorio = request.form.get('hora_recordatorio') or None

        if not titulo.strip():
            flash('El título de la tarea no puede estar vacío.', 'error')
            return render_template('edit_task_maestro.html', tarea=tarea)

        db.tarea_clase.update_one(
            {'_id': ObjectId(task_id)},
            {'$set': {
                'titulo': titulo,
                'contenido': contenido,
                'fecha_recordatorio': fecha_recordatorio,
                'hora_recordatorio': hora_recordatorio,
                'fecha_modificacion': datetime.utcnow()
            }}
        )
        flash('Tarea actualizada exitosamente.', 'success')
        return redirect(url_for('maestros_dashboard'))

    return render_template('edit_task_maestro.html', tarea=tarea)

@app.route('/delete_task_maestro/<task_id>', methods=['POST'])
@login_required
def delete_task_maestro(task_id):
    if not current_user.es_maestro():
        flash('Acceso denegado.', 'error')
        return redirect(url_for('dashboard'))

    tarea = db.tarea_clase.find_one({'_id': ObjectId(task_id), 'codigo_clase': current_user.data['codigo_clase']})
    if not tarea:
        flash('Tarea no encontrada o no tienes permiso para eliminarla.', 'error')
        return redirect(url_for('maestros_dashboard'))

    db.tarea_clase.delete_one({'_id': ObjectId(task_id)})
    flash('Tarea eliminada correctamente.', 'success')
    return redirect(url_for('maestros_dashboard'))

@app.route('/clases', methods=['GET', 'POST'])
@login_required
def clases():
    if request.method == 'POST':
        codigo_clase = request.form.get('codigo_clase', '').strip()

        if not codigo_clase:
            flash('Por favor ingresa un código de clase.', 'error')
            return redirect(url_for('clases'))

        # Buscar clase por código
        clase_obj = db.clase.find_one({'codigo_clase': codigo_clase})
        if not clase_obj:
            flash('Código de clase inválido.', 'error')
            return redirect(url_for('clases'))

        # Verificar si ya está unido el usuario a esa clase
        existe_relacion = db.usuario_clase.find_one({
            'usuario_id': ObjectId(current_user.id),
            'codigo_clase': codigo_clase
        })

        if not existe_relacion:
            db.usuario_clase.insert_one({
                'usuario_id': ObjectId(current_user.id),
                'codigo_clase': codigo_clase
            })
            flash(f'Te uniste a la clase {codigo_clase}.', 'success')
        else:
            flash(f'Ya estás unido a la clase {codigo_clase}.', 'info')

        session['clase_activa'] = codigo_clase
        return redirect(url_for('vista_clase', codigo=codigo_clase))

    # Método GET: obtener las clases a las que el usuario está unido
    relaciones = db.usuario_clase.find({'usuario_id': ObjectId(current_user.id)})
    codigos = [rel['codigo_clase'] for rel in relaciones]

    mis_clases = list(db.clase.find({'codigo_clase': {'$in': codigos}}))

    return render_template('clases.html', user=current_user, mis_clases=mis_clases)



@app.route('/vista_clase/<codigo>')
@login_required
def vista_clase(codigo):
    # Validar que el usuario esté unido a la clase
    relacion = db.usuario_clase.find_one({
        'usuario_id': current_user.data['_id'],
        'codigo_clase': codigo
    })
    if not relacion:
        flash('No estás unido a esta clase.', 'error')
        return redirect(url_for('clases'))

    # 🔹 Marcar como clase activa en la sesión
    session['clase_activa'] = codigo

    tareas = list(db.tarea_clase.find({"codigo_clase": codigo}).sort("fecha_modificacion", -1))
    tareas = parse_datetime_fields(tareas)

    relaciones = db.usuario_clase.find({'usuario_id': current_user.data['_id']})
    codigos = [rel['codigo_clase'] for rel in relaciones]
    mis_clases = list(db.clase.find({'codigo_clase': {'$in': codigos}}))
    
    return render_template('vista_clase.html', codigo=codigo, tareas=tareas, user=current_user, mis_clases=mis_clases)


@app.route('/salir_clase', methods=['POST'])
@login_required
def salir_clase():
    codigo_clase = request.form.get('codigo_clase')  # Recibir código de clase a salir

    if not codigo_clase:
        flash('No se especificó la clase a salir.', 'error')
        return redirect(url_for('clases'))

    resultado = db.usuario_clase.delete_one({
        'usuario_id': current_user.data['_id'],
        'codigo_clase': codigo_clase
    })

    if resultado.deleted_count > 0:
        flash(f'Saliste de la clase {codigo_clase}.', 'info')
        # 🔹 Aquí limpias la clase activa
        session.pop('clase_activa', None)
    else:
        flash('No estabas unido a esa clase.', 'warning')

    return redirect(url_for('clases'))

if __name__ == '__main__':
    app.run(debug=True)
