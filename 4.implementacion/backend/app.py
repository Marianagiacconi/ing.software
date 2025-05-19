from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# Configuración
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mensajes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

db = SQLAlchemy(app)

# Modelos
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    contrasena = db.Column(db.String(200), nullable=False)
    mensajes = db.relationship('Mensaje', backref='autor', lazy=True)

class Mensaje(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    likes = db.relationship('Like', backref='mensaje', lazy=True)
    comentarios = db.relationship('Comentario', backref='mensaje', lazy=True)
    republicaciones = db.relationship('Republicacion', backref='mensaje', lazy=True)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    mensaje_id = db.Column(db.Integer, db.ForeignKey('mensaje.id'), nullable=False)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Comentario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    mensaje_id = db.Column(db.Integer, db.ForeignKey('mensaje.id'), nullable=False)

class Republicacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    mensaje_id = db.Column(db.Integer, db.ForeignKey('mensaje.id'), nullable=False)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# Crear tablas
with app.app_context():
    db.create_all()

# Middleware para verificar autenticación
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            return jsonify({'error': 'No autorizado'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Rutas de autenticación
@app.route('/api/registro', methods=['POST'])
def registro():
    datos = request.get_json()
    required = ['nombre', 'apellido', 'email', 'fecha_nacimiento', 'contrasena']
    for campo in required:
        if campo not in datos or not datos[campo]:
            return jsonify({'error': f'El campo {campo} es obligatorio'}), 400
    if Usuario.query.filter_by(email=datos['email']).first():
        return jsonify({'error': 'El email ya está registrado'}), 400
    try:
        fecha_nacimiento = datetime.strptime(datos['fecha_nacimiento'], '%Y-%m-%d').date()
    except Exception:
        return jsonify({'error': 'Fecha de nacimiento inválida'}), 400
    usuario = Usuario(
        nombre=datos['nombre'],
        apellido=datos['apellido'],
        email=datos['email'],
        fecha_nacimiento=fecha_nacimiento,
        contrasena=generate_password_hash(datos['contrasena'])
    )
    db.session.add(usuario)
    db.session.commit()
    return jsonify({'mensaje': 'Usuario registrado exitosamente'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    datos = request.get_json()
    print(f"Login intento: {datos}")  # Log para depuración
    usuario = Usuario.query.filter((Usuario.email==datos['email']) | ((Usuario.nombre + ' ' + Usuario.apellido)==datos['email'])).first()
    if not usuario:
        print(f"Usuario no encontrado: {datos['email']}")  # Log para depuración
        return jsonify({'error': 'Credenciales inválidas'}), 401
    if not check_password_hash(usuario.contrasena, datos['contrasena']):
        print(f"Contraseña incorrecta para usuario: {usuario.email}")  # Log para depuración
        return jsonify({'error': 'Credenciales inválidas'}), 401
    session['usuario_id'] = usuario.id
    return jsonify({
        'mensaje': 'Login exitoso',
        'usuario': {
            'id': usuario.id,
            'nombre': usuario.nombre,
            'apellido': usuario.apellido,
            'email': usuario.email,
            'fecha_nacimiento': usuario.fecha_nacimiento.strftime('%Y-%m-%d')
        }
    })

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('usuario_id', None)
    return jsonify({'mensaje': 'Logout exitoso'})

@app.route('/api/usuario/actual', methods=['GET'])
@login_required
def obtener_usuario_actual():
    usuario = Usuario.query.get(session['usuario_id'])
    return jsonify({
        'id': usuario.id,
        'nombre': usuario.nombre,
        'apellido': usuario.apellido,
        'email': usuario.email,
        'fecha_nacimiento': usuario.fecha_nacimiento.strftime('%Y-%m-%d')
    })

# Rutas de mensajes
@app.route('/api/mensajes', methods=['GET'])
@login_required
def obtener_mensajes():
    mensajes = Mensaje.query.order_by(Mensaje.fecha.desc()).all()
    usuario_actual = session['usuario_id']
    
    resultado = []
    for mensaje in mensajes:
        autor = Usuario.query.get(mensaje.usuario_id)
        likes = Like.query.filter_by(mensaje_id=mensaje.id).all()
        comentarios = Comentario.query.filter_by(mensaje_id=mensaje.id).all()
        republicaciones = Republicacion.query.filter_by(mensaje_id=mensaje.id).all()
        
        resultado.append({
            'id': mensaje.id,
            'texto': mensaje.texto,
            'fecha': mensaje.fecha.isoformat(),
            'authorName': f"{autor.nombre} {autor.apellido}",
            'username': autor.email,
            'likes': {
                'total': len(likes),
                'dio_like': any(like.usuario_id == usuario_actual for like in likes)
            },
            'comentarios': [{
                'id': c.id,
                'texto': c.texto,
                'fecha': c.fecha.isoformat(),
                'usuario': Usuario.query.get(c.usuario_id).nombre
            } for c in comentarios],
            'republicaciones': {
                'total': len(republicaciones),
                'republico': any(r.usuario_id == usuario_actual for r in republicaciones)
            }
        })
    
    return jsonify(resultado)

@app.route('/api/mensajes', methods=['POST'])
@login_required
def crear_mensaje():
    datos = request.get_json()
    mensaje = Mensaje(
        texto=datos['texto'],
        usuario_id=session['usuario_id']
    )
    
    db.session.add(mensaje)
    db.session.commit()
    
    return jsonify({
        'id': mensaje.id,
        'texto': mensaje.texto,
        'fecha': mensaje.fecha.isoformat(),
        'usuario': Usuario.query.get(session['usuario_id']).nombre,
        'likes': {'total': 0, 'dio_like': False},
        'comentarios': [],
        'republicaciones': {'total': 0, 'republico': False}
    }), 201

@app.route('/api/mensajes/<int:id>', methods=['DELETE'])
@login_required
def eliminar_mensaje(id):
    mensaje = Mensaje.query.get_or_404(id)
    
    if mensaje.usuario_id != session['usuario_id']:
        return jsonify({'error': 'No autorizado'}), 403
    
    db.session.delete(mensaje)
    db.session.commit()
    
    return jsonify({'mensaje': 'Mensaje eliminado'})

@app.route('/api/mensajes/<int:id>/like', methods=['POST'])
@login_required
def dar_like(id):
    mensaje = Mensaje.query.get_or_404(id)
    like_existente = Like.query.filter_by(
        usuario_id=session['usuario_id'],
        mensaje_id=id
    ).first()
    
    if like_existente:
        db.session.delete(like_existente)
    else:
        like = Like(
            usuario_id=session['usuario_id'],
            mensaje_id=id
        )
        db.session.add(like)
    
    db.session.commit()
    
    likes = Like.query.filter_by(mensaje_id=id).all()
    return jsonify({
        'total': len(likes),
        'dio_like': not like_existente
    })

@app.route('/api/mensajes/<int:id>/comentarios', methods=['POST'])
@login_required
def comentar(id):
    datos = request.get_json()
    comentario = Comentario(
        texto=datos['texto'],
        usuario_id=session['usuario_id'],
        mensaje_id=id
    )
    
    db.session.add(comentario)
    db.session.commit()
    
    return jsonify({
        'id': comentario.id,
        'texto': comentario.texto,
        'fecha': comentario.fecha.isoformat(),
        'usuario': Usuario.query.get(session['usuario_id']).nombre
    }), 201

@app.route('/api/mensajes/<int:id>/republicar', methods=['POST'])
@login_required
def republicar(id):
    mensaje = Mensaje.query.get_or_404(id)
    republicacion_existente = Republicacion.query.filter_by(
        usuario_id=session['usuario_id'],
        mensaje_id=id
    ).first()
    
    if republicacion_existente:
        db.session.delete(republicacion_existente)
    else:
        republicacion = Republicacion(
            usuario_id=session['usuario_id'],
            mensaje_id=id
        )
        db.session.add(republicacion)
    
    db.session.commit()
    
    republicaciones = Republicacion.query.filter_by(mensaje_id=id).all()
    return jsonify({
        'total': len(republicaciones),
        'republico': not republicacion_existente
    })

print(app.url_map)

if __name__ == '__main__':
    app.run(debug=True) 