"""Minimal debug endpoint for Vercel — uses http.server handler format."""
from http.server import BaseHTTPRequestHandler
import traceback


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            import sys
            import os

            API_DIR = os.path.dirname(os.path.abspath(__file__))
            if API_DIR not in sys.path:
                sys.path.insert(0, API_DIR)

            lines = [f"Python: {sys.version}", f"CWD: {os.getcwd()}", f"API_DIR: {API_DIR}", ""]

            # Test imports one by one
            for mod_name in ["fastapi", "mangum", "sqlalchemy", "anthropic", "pg8000", "pydantic", "openpyxl", "tenacity", "requests", "dotenv"]:
                try:
                    __import__(mod_name)
                    lines.append(f"{mod_name}: OK")
                except Exception as e:
                    lines.append(f"{mod_name}: FAIL - {e}")

            lines.append("")

            # Test main import
            try:
                from main import handler as h
                lines.append("main.handler: OK")
            except Exception as e:
                lines.append(f"main.handler: FAIL - {e}")
                lines.append(traceback.format_exc())

            body = "\n".join(lines)
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(body.encode())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"FATAL: {e}\n{traceback.format_exc()}".encode())
