from flask import request, jsonify
from app import app, db
from models import Usuario, MensajePublico

# Simulación de usuario autenticado (para pruebas)
USUARIO_PRUEBA_ID = 1

@app.route('/mensajes', methods=['POST'])
def publicar_mensaje():
    data = request.get_json()
    texto = data.get('texto', '').strip()
    if not texto:
        return jsonify({'error': 'El mensaje no puede estar vacío.'}), 400
    if len(texto) > 2000:
        return jsonify({'error': 'El mensaje supera el máximo de 2000 caracteres.'}), 400
    usuario = Usuario.query.get(USUARIO_PRUEBA_ID)
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado.'}), 404
    mensaje = MensajePublico(texto=texto, usuario=usuario)
    db.session.add(mensaje)
    db.session.commit()
    return jsonify({'mensaje': 'Mensaje publicado exitosamente.'}), 201

@app.route('/mensajes', methods=['GET'])
def listar_mensajes():
    mensajes = MensajePublico.query.order_by(MensajePublico.fecha.desc()).all()
    resultado = []
    for m in mensajes:
        resultado.append({
            'id': m.id,
            'texto': m.texto,
            'fecha': m.fecha.isoformat(),
            'usuario': m.usuario.nombre
        })
    return jsonify(resultado) 