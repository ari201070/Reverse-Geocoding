import http.server
import socketserver
import os
import urllib.parse
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Forzar salida en UTF-8 para evitar UnicodeEncodeError en Windows (cp1255)
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

PORT = 19999
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)
        
        # Mapeo de rutas robusto para Windows
        # /media/2025/Septiembre/... -> F:\2025\Septiembre\...
        if path.startswith('/media/'):
            relative_path = path[len('/media/'):]
            local_path = os.path.join('F:\\', relative_path)
        elif path.startswith('/2025/'):
            relative_path = path[len('/2025/'):]
            local_path = os.path.join('F:\\2025', relative_path)
        else:
            local_path = os.path.join(BASE_DIR, path.lstrip('/'))
        
        local_path = os.path.normpath(local_path)

        # Imprimir de manera segura
        try:
            print(f"[OK] URL: {path} -> Local: {local_path}", flush=True)
        except Exception:
            # Si aún falla la consola por codificación, ignoramos el print para no caer el servidor
            pass
        
        if os.path.isfile(local_path):
            ext = os.path.splitext(local_path)[1].lower()
            content_types = {
                '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                '.png': 'image/png', '.gif': 'image/gif',
                '.heic': 'image/heic', '.heif': 'image/heif',
                '.mp4': 'video/mp4', '.mov': 'video/quicktime',
                '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript'
            }
            content_type = content_types.get(ext, 'application/octet-stream')
            
            try:
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                with open(local_path, 'rb') as f:
                    self.wfile.write(f.read())
                return
            except Exception as e:
                try:
                    print(f"[ERROR] Al servir {local_path}: {e}", flush=True)
                except:
                    pass
                self.send_error(500, "Internal Server Error")
                return
        
        super().do_GET()

class ReuseAddrServer(socketserver.TCPServer):
    allow_reuse_address = True

print(f"Servidor activo y blindado en http://localhost:{PORT}", flush=True)
try:
    with ReuseAddrServer(("", PORT), CustomHandler) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\nServidor detenido.", flush=True)
