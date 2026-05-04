import http.server
import socketserver
import socket
import datetime
import os

LOG_FILE = r"C:\Marc_max_20gb\.bago\tools\lenovo_http.log"
IP_FILE = r"C:\Marc_max_20gb\.bago\tools\lenovo_ip.txt"

class BAGOHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        client_ip = self.client_address[0]
        ts = datetime.datetime.now().isoformat()
        msg = f"CONEXION DESDE: {client_ip} - {ts}\n"
        print(msg, end='')
        with open(LOG_FILE, 'a') as f:
            f.write(msg)
        # Si no es nuestra propia IP, guardar como IP del Lenovo
        if client_ip not in ('169.254.31.155', '127.0.0.1', '::1'):
            with open(IP_FILE, 'w') as f:
                f.write(client_ip)
            print(f"!!! IP LENOVO DETECTADA: {client_ip} !!!")
        # Respuesta HTML
        html = f"<html><body><h1>BAGO Framework</h1><p>Tu IP: {client_ip}</p></body></html>"
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def log_message(self, format, *args):
        pass  # Silenciar logs por defecto

# Bind en todas las interfaces (incluyendo 169.254.31.155)
server = socketserver.TCPServer(('0.0.0.0', 8080), BAGOHandler)
print(f"HTTP server en 0.0.0.0:8080 - esperando conexion del Lenovo...")
print(f"Lenovo debe acceder a: http://169.254.31.155:8080")
server.serve_forever()
