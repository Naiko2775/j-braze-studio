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
import json
import asyncio
from urllib.parse import urlparse, unquote


# Import FastAPI app
from main import app as fastapi_app


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

            self.send_response(status_code)
            for k, v in resp_headers.items():
                self.send_header(k, v)
            self.end_headers()

            if isinstance(resp_body, str):
                self.wfile.write(resp_body.encode("utf-8"))
            elif isinstance(resp_body, bytes):
                self.wfile.write(resp_body)

        except Exception as e:
            import traceback
            error_body = json.dumps({"error": str(e), "trace": traceback.format_exc()})
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(error_body.encode("utf-8"))

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass
