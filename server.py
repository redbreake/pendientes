import http.server
import socketserver
import json
import urllib.parse
import secrets
import os

PORT = 8080
DIRECTORY = "."

# Configuración del login
ADMIN_PASSWORD = "kaladmin" # Contraseña por defecto
SESSION_TOKEN = secrets.token_hex(16) # Token que cambia cada vez que se reinicia el server

class AnimeTrackerHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_POST(self):
        # /api/login => Validar contraseña
        if self.path == '/api/login':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(post_data)
                if data.get("password") == ADMIN_PASSWORD:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True, "token": SESSION_TOKEN}).encode())
                else:
                    self.send_response(401)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "error": "Contraseña incorrecta"}).encode())
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "Bad Request"}).encode())
            return

        # /api/update => Guardar datos en data.json
        if self.path == '/api/update':
            # Verificar auth
            auth_header = self.headers.get('Authorization')
            if auth_header != f"Bearer {SESSION_TOKEN}":
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "No autorizado. Inicia sesión de nuevo."}).encode())
                return

            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            try:
                new_data = json.loads(post_data)
                # Guardar en data.json
                with open('data.json', 'w', encoding='utf-8') as f:
                    json.dump(new_data, f, indent=2, ensure_ascii=False)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode())
            return
            
        # /api/upload => Guardar imagen subida
        if self.path == '/api/upload':
            # Verificar auth
            auth_header = self.headers.get('Authorization')
            if auth_header != f"Bearer {SESSION_TOKEN}":
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "No autorizado."}).encode())
                return

            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(post_data)
                filename = data.get("filename")
                b64_data = data.get("data") # Formato: "data:image/png;base64,iVBORw0KGgo..."
                
                if not filename or not b64_data:
                    raise Exception("Faltan datos de la imagen.")
                
                import base64
                # Separar el header del base64 ("data:image/png;base64,")
                header, encoded = b64_data.split(",", 1)
                
                # Crear carpeta si no existe
                if not os.path.exists('imagenes'):
                    os.makedirs('imagenes')
                
                # Nombre de archivo seguro
                safe_name = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in (' ', '.', '-', '_')]).rstrip()
                file_path = os.path.join('imagenes', safe_name)
                
                with open(file_path, "wb") as fh:
                    fh.write(base64.b64decode(encoded))
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                # Devolvemos la ruta relativa de la imagen para guardarla en el JSON
                self.wfile.write(json.dumps({"success": True, "path": "imagenes/" + safe_name}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode())
            return
            
        # Si no es ninguna API, devolver 404
        self.send_error(404, "File not found")

    def end_headers(self):
        # Desactivar caché para evitar problemas al actualizar
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

def run(server_class=http.server.HTTPServer, handler_class=AnimeTrackerHandler):
    # Asegúrate de usar allow_reuse_address para evitar el error "Address already in use"
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("", PORT), handler_class)
    print(f"Servidor backend iniciado en http://localhost:{PORT}")
    print(f"Contraseña de Admin: {ADMIN_PASSWORD}")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
