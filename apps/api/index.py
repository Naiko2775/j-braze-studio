"""Vercel serverless entry point.

Vercel @vercel/python looks for a class named `handler` that extends
BaseHTTPRequestHandler, OR a WSGI app. We use a thin wrapper that
delegates to FastAPI via a synchronous ASGI-to-WSGI bridge.
"""
import os
import sys

# Ensure the api directory is on the Python path
API_DIR = os.path.dirname(os.path.abspath(__file__))
if API_DIR not in sys.path:
    sys.path.insert(0, API_DIR)

from http.server import BaseHTTPRequestHandler
import base64
import json
import asyncio
import logging
from urllib.parse import urlparse, unquote


# Import FastAPI app
from main import app as fastapi_app

logger = logging.getLogger(__name__)


class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler that proxies to FastAPI."""

    def do_GET(self):
        self._handle()

    def do_POST(self):
        self._handle()

    def do_PUT(self):
        self._handle()

    def do_DELETE(self):
        self._handle()

    def do_PATCH(self):
        self._handle()

    def _handle(self):
        try:
            import asyncio
            # Ensure there is an event loop for Mangum/ASGI
            try:
                asyncio.get_event_loop()
            except RuntimeError:
                asyncio.set_event_loop(asyncio.new_event_loop())

            from mangum import Mangum
            mangum_handler = Mangum(fastapi_app, lifespan="off")

            # Build AWS Lambda-like event from the HTTP request
            parsed = urlparse(self.path)
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else b""

            # Build headers dict
            headers = {}
            for key, value in self.headers.items():
                headers[key.lower()] = value

            event = {
                "version": "2.0",
                "routeKey": f"{self.command} {parsed.path}",
                "rawPath": unquote(parsed.path),
                "rawQueryString": parsed.query or "",
                "headers": headers,
                "requestContext": {
                    "http": {
                        "method": self.command,
                        "path": unquote(parsed.path),
                        "sourceIp": "127.0.0.1",
                    },
                    "stage": "$default",
                },
                "body": body.decode("utf-8") if body else None,
                "isBase64Encoded": False,
            }

            # Add queryStringParameters
            if parsed.query:
                params = {}
                for param in parsed.query.split("&"):
                    if "=" in param:
                        k, v = param.split("=", 1)
                        params[unquote(k)] = unquote(v)
                event["queryStringParameters"] = params

            context = type("Context", (), {"function_name": "vercel", "memory_limit_in_mb": 1024})()

            response = mangum_handler(event, context)

            status_code = response.get("statusCode", 200)
            resp_headers = response.get("headers", {})
            resp_body = response.get("body", "")

            # Mangum encode en base64 tout corps dont le Content-Type n'est pas
            # textuel : c'est le cas de l'export Excel (.xlsx). Sans ce decodage,
            # la chaine base64 etait ecrite telle quelle dans le fichier et Excel
            # refusait de l'ouvrir. Le CSV passait car "text/csv" reste en clair.
            if response.get("isBase64Encoded"):
                out_bytes = base64.b64decode(resp_body or "")
            elif isinstance(resp_body, bytes):
                out_bytes = resp_body
            else:
                out_bytes = (resp_body or "").encode("utf-8")

            self.send_response(status_code)
            for k, v in resp_headers.items():
                # Le Content-Length de Mangum porte sur le corps encode : on le
                # recalcule sur les octets reellement emis.
                if k.lower() == "content-length":
                    continue
                self.send_header(k, v)
            self.send_header("Content-Length", str(len(out_bytes)))
            self.end_headers()

            self.wfile.write(out_bytes)

        except Exception:
            # La stacktrace reste cote serveur (logs Vercel) : la renvoyer au
            # client exposait l'arborescence du projet et les variables d'appel.
            logger.exception("Erreur non geree dans le handler serverless")
            error_body = json.dumps(
                {"error": "Erreur interne du serveur"}
            ).encode("utf-8")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(error_body)))
            self.end_headers()
            self.wfile.write(error_body)

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass
