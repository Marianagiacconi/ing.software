from app import app, db
from models import Usuario

with app.app_context():
    db.create_all()

    # Crear usuario de prueba si no existe
    if not Usuario.query.filter_by(email='prueba@demo.com').first():
        usuario = Usuario(nombre='UsuarioPrueba', email='prueba@demo.com', contrasena='1234')
        db.session.add(usuario)
        db.session.commit()
        print('Usuario de prueba creado.')
    else:
        print('Usuario de prueba ya existe.') 