from flask import Flask, request, jsonify, send_from_directory
import json
import os
import base64
import secrets

# Configurar Flask para que sirva los archivos de esta misma carpeta
app = Flask(__name__, static_folder='.', static_url_path='')

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "kaladmin")
# PythonAnywhere reinicia la app de vez en cuando, para que las sesiones de los mods 
# no se caigan a cada rato al reiniciarse, podríamos usar algo fijo o simplemente 
# aceptar que tengan que loguearse de nuevo. Aquí generamos un token al iniciar app.
SESSION_TOKEN = secrets.token_hex(16)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if data and data.get("password") == ADMIN_PASSWORD:
        return jsonify({"success": True, "token": SESSION_TOKEN})
    return jsonify({"success": False, "error": "Contraseña incorrecta"}), 401

@app.route('/api/update', methods=['POST'])
def update_data():
    auth_header = request.headers.get('Authorization')
    if auth_header != f"Bearer {SESSION_TOKEN}":
        return jsonify({"success": False, "error": "No autorizado. Inicia sesión de nuevo."}), 401
    
    new_data = request.get_json()
    try:
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(new_data, f, indent=2, ensure_ascii=False)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_image():
    auth_header = request.headers.get('Authorization')
    if auth_header != f"Bearer {SESSION_TOKEN}":
        return jsonify({"success": False, "error": "No autorizado."}), 401

    data = request.get_json()
    filename = data.get("filename")
    b64_data = data.get("data")
    
    if not filename or not b64_data:
        return jsonify({"success": False, "error": "Faltan datos de la imagen."}), 400
        
    try:
        header, encoded = b64_data.split(",", 1)
        if not os.path.exists('imagenes'):
            os.makedirs('imagenes')
            
        safe_name = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in (' ', '.', '-', '_')]).rstrip()
        file_path = os.path.join('imagenes', safe_name)
        
        with open(file_path, "wb") as fh:
            fh.write(base64.b64decode(encoded))
            
        return jsonify({"success": True, "path": "imagenes/" + safe_name})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Ruta catch-all para servir cualquier archivo estático si se pide (css, js, json)
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    # Ejecución local de prueba
    app.run(host='0.0.0.0', port=8080, debug=True)
