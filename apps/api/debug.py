"""Minimal debug endpoint for Vercel."""
import traceback

def handler(request, context=None):
    """HTTP handler for debugging imports."""
    try:
        import sys
        import os

        API_DIR = os.path.dirname(os.path.abspath(__file__))
        if API_DIR not in sys.path:
            sys.path.insert(0, API_DIR)

        errors = []

        # Test basic imports
        try:
            from fastapi import FastAPI
            errors.append("fastapi: OK")
        except Exception as e:
            errors.append(f"fastapi: FAIL - {e}")

        try:
            from mangum import Mangum
            errors.append("mangum: OK")
        except Exception as e:
            errors.append(f"mangum: FAIL - {e}")

        try:
            from sqlalchemy import create_engine
            errors.append("sqlalchemy: OK")
        except Exception as e:
            errors.append(f"sqlalchemy: FAIL - {e}")

        try:
            import anthropic
            errors.append("anthropic: OK")
        except Exception as e:
            errors.append(f"anthropic: FAIL - {e}")

        try:
            import pg8000
            errors.append("pg8000: OK")
        except Exception as e:
            errors.append(f"pg8000: FAIL - {e}")

        try:
            from main import handler as h
            errors.append("main.handler: OK")
        except Exception as e:
            errors.append(f"main.handler: FAIL - {e}")
            errors.append(traceback.format_exc())

        body = "\n".join(errors)
        return {
            "statusCode": 200,
            "headers": {"content-type": "text/plain"},
            "body": body,
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"content-type": "text/plain"},
            "body": f"FATAL: {e}\n{traceback.format_exc()}",
        }
