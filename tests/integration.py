"""Integration checks for the lab's HTTP/HTTPS, authentication, and firewall behavior."""

import base64
import hashlib
import hmac
import json
import os
import socket
import ssl
import urllib.error
import urllib.request

HOST = "gateway"
USER = os.environ.get("LAB_USER", "aluno")
PASSWORD = os.environ.get("LAB_PASSWORD", "rede-segura-2026")
HMAC_KEY = os.environ.get(
    "LAB_HMAC_KEY", "chave-laboratorio-nao-usar-em-producao"
).encode()
CONTEXT = ssl.create_default_context(cafile="/run/certs/ca.crt")
OPENER = urllib.request.build_opener(urllib.request.HTTPSHandler(context=CONTEXT))
AUTHORIZATION = "Basic " + base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()


def request(url, data=None, authenticated=True):
    """Send an HTTP request and return its status code and decoded response body."""
    req = urllib.request.Request(url, data=data)
    if authenticated:
        req.add_header("Authorization", AUTHORIZATION)
    try:
        with OPENER.open(req, timeout=3) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode()


for scheme, port in (("http", 8080), ("https", 8443)):
    base = f"{scheme}://{HOST}:{port}"
    status, _ = request(f"{base}/protected", authenticated=False)
    assert status == 401, f"{scheme}: unauthenticated access should fail: {status}"
    status, body = request(f"{base}/protected", None)
    assert status == 200 and "Authorized" in body, f"{scheme}: authentication failed"

    message = "mensagem íntegra"
    signature = hmac.new(HMAC_KEY, message.encode(), hashlib.sha256).hexdigest()
    payload = json.dumps({"message": message, "signature": signature}).encode()
    status, body = request(f"{base}/hmac", payload)
    assert status == 200 and "valid" in body, f"{scheme}: valid HMAC was rejected"

    altered = json.dumps(
        {"message": message + " alterada", "signature": signature}
    ).encode()
    status, body = request(f"{base}/hmac", altered)
    assert status == 400 and "invalid" in body, (
        f"{scheme}: message alteration not detected"
    )

try:
    with socket.create_connection((HOST, 9000), timeout=1):
        raise AssertionError("unauthorized port 9000 was reachable")
except (TimeoutError, OSError):
    pass

print("OK: TLS, HTTP/HTTPS, authentication, HMAC, and nftables checks passed")
