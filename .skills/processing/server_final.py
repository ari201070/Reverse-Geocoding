import http.server
import socketserver
import os
import urllib.parse
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Forzar UTF-8 en Windows
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

PORT = 30000

class MediaHandler(http.server.SimpleHTTPRequestHandler):
    def do_HEAD(self):
        # HEAD debe responder igual que GET pero sin body
        self.do_GET()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)
        
        print(f"[REQUEST] {path}", flush=True)
        
        # /media/... -> F:/...
        if path.startswith('/media/'):
            relative = path[len('/media/'):]
            local_path = os.path.normpath(os.path.join('F:/', relative))
            
            print(f"[MAP] {path} -> {local_path} (exists={os.path.exists(local_path)})", flush=True)
            
            if os.path.isfile(local_path):
                ext = os.path.splitext(local_path)[1].lower()
                content_types = {
                    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                    '.png': 'image/png', '.gif': 'image/gif',
                    '.heic': 'image/heic', '.heif': 'image/heif',
                    '.mp4': 'video/mp4', '.mov': 'video/quicktime',
                }
                content_type = content_types.get(ext, 'application/octet-stream')
                
                try:
                    self.send_response(200)
                    self.send_header('Content-Type', content_type)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    with open(local_path, 'rb') as f:
                        self.wfile.write(f.read())
                    print(f"[OK] Servido: {local_path}", flush=True)
                    return
                except Exception as e:
                    print(f"[ERROR] Sirviendo {local_path}: {e}", flush=True)
                    self.send_error(500)
                    return
        
        # Fallback a archivos locales del proyecto
        print(f"[FALLBACK] {path}", flush=True)
        super().do_GET()

class ReuseServer(socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == '__main__':
    print(f"=== Servidor FINAL en http://localhost:{PORT} ===", flush=True)
    with ReuseServer(("", PORT), MediaHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n=== Servidor detenido ===", flush=True)
