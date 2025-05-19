from app import db
from datetime import datetime

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    contrasena = db.Column(db.String(128), nullable=False)
    mensajes = db.relationship('MensajePublico', backref='usuario', lazy=True)

class MensajePublico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.String(2000), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    # likes, comentarios, republicaciones pueden agregarse luego 