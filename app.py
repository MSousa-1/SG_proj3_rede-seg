import base64
import hashlib
import hmac
import json
import os
import ssl
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from socketserver import BaseRequestHandler, ThreadingTCPServer
from urllib.parse import urlparse


LAB_USER = os.environ.get("LAB_USER", "aluno")
LAB_PASSWORD = os.environ.get("LAB_PASSWORD", "rede-segura-2026")
LAB_HMAC_KEY = os.environ.get(
    "LAB_HMAC_KEY", "chave-laboratorio-nao-usar-em-producao"
).encode()


class LabHandler(BaseHTTPRequestHandler):
    server_version = "RedeSeguraLab/1.0"

    def send_text(
        self, status, message, content_type="text/plain; charset=utf-8", headers=()
    ):
        body = message.encode()
        self.send_response(status)
        for name, value in headers:
            self.send_header(name, value)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def authorized(self):
        header = self.headers.get("Authorization", "")
        try:
            scheme, token = header.split(" ", 1)
            supplied = base64.b64decode(token, validate=True).decode()
        except (ValueError, UnicodeDecodeError):
            supplied = ""
            scheme = ""
        expected = f"{LAB_USER}:{LAB_PASSWORD}"
        if scheme.lower() == "basic" and hmac.compare_digest(supplied, expected):
            return True
        self.send_text(
            401,
            "Autenticacao necessaria\n",
            headers=(("WWW-Authenticate", 'Basic realm="Laboratorio"'),),
        )
        return False

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            self.send_text(200, "ok\n")
        elif path == "/":
            self.send_text(
                200,
                "Laboratorio de rede segura\n"
                "HTTP/HTTPS ativo; use /protected para testar autenticacao.\n",
            )
        elif path == "/protected":
            if self.authorized():
                self.send_text(200, "Acesso autorizado\n")
        else:
            self.send_text(404, "Nao encontrado\n")

    def do_POST(self):
        if urlparse(self.path).path != "/hmac":
            self.send_text(404, "Nao encontrado\n")
            return
        if not self.authorized():
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > 65536:
                raise ValueError
            payload = json.loads(self.rfile.read(length))
            message = payload["message"]
            signature = payload["signature"]
            if not isinstance(message, str) or not isinstance(signature, str):
                raise ValueError
        except (ValueError, KeyError, TypeError, json.JSONDecodeError):
            self.send_text(400, "JSON invalido\n")
            return

        expected = hmac.new(
            LAB_HMAC_KEY, message.encode(), hashlib.sha256
        ).hexdigest()
        if hmac.compare_digest(signature, expected):
            self.send_text(200, "HMAC valido: integridade confirmada\n")
        else:
            self.send_text(400, "HMAC invalido: mensagem alterada ou assinatura incorreta\n")


class AuditHandler(BaseRequestHandler):
    def handle(self):
        self.request.sendall(b"Servico nao autorizado\n")


def start_http(port, use_tls=False):
    server = ThreadingHTTPServer(("0.0.0.0", port), LabHandler)
    if use_tls:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain("/run/certs/server.crt", "/run/certs/server.key")
        server.socket = context.wrap_socket(server.socket, server_side=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


if __name__ == "__main__":
    start_http(8080)
    start_http(8443, use_tls=True)
    audit = ThreadingTCPServer(("0.0.0.0", 9000), AuditHandler)
    threading.Thread(target=audit.serve_forever, daemon=True).start()
    threading.Event().wait()
