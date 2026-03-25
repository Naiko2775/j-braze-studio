"""J-Braze Studio API -- FastAPI application."""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

app = FastAPI(
    title="J-Braze Studio API",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "modules": {
            "data_model": "available",
            "liquid": "available",
            "migration": "available",
        },
    }


@app.get("/api/health/claude")
def health_claude():
    """Verifie que la cle API Anthropic est configuree."""
    from services.claude_client import get_api_key
    if get_api_key():
        return {"status": "ok", "service": "claude"}
    return {"status": "error", "service": "claude", "detail": "ANTHROPIC_API_KEY non definie"}


@app.post("/api/settings/anthropic-key")
def set_anthropic_key(payload: dict):
    """Definit la cle API Claude depuis l'UI."""
    from services.claude_client import set_runtime_api_key
    key = payload.get("api_key", "").strip()
    if not key:
        return {"status": "error", "detail": "Cle API vide"}
    set_runtime_api_key(key)
    return {"status": "ok", "detail": "Cle API Claude configuree"}


@app.get("/api/settings/anthropic-key")
def get_anthropic_key_status():
    """Verifie si une cle API Claude est configuree (sans la reveler)."""
    from services.claude_client import get_api_key
    key = get_api_key()
    if key:
        masked = key[:7] + "..." + key[-4:] if len(key) > 15 else "***"
        return {"configured": True, "masked_key": masked}
    return {"configured": False, "masked_key": None}


@app.get("/api/health/braze")
def health_braze():
    """Verifie que les cles API Braze sont configurees."""
    braze_key = os.environ.get("BRAZE_API_KEY")
    braze_url = os.environ.get("BRAZE_API_URL")
    if braze_key and braze_url:
        return {"status": "ok", "service": "braze"}
    missing = []
    if not braze_key:
        missing.append("BRAZE_API_KEY")
    if not braze_url:
        missing.append("BRAZE_API_URL")
    return {"status": "error", "service": "braze", "detail": f"{', '.join(missing)} non definie(s)"}


@app.get("/api/health/database")
def health_database():
    """Verifie la connexion a la base de donnees."""
    try:
        from models.db import SessionLocal
        db = SessionLocal()
        try:
            db.execute(__import__("sqlalchemy").text("SELECT 1"))
            return {"status": "ok", "service": "database"}
        finally:
            db.close()
    except Exception as exc:
        return {"status": "error", "service": "database", "detail": str(exc)}


from routers.data_model import router as data_model_router
app.include_router(data_model_router)

from routers.liquid import router as liquid_router
app.include_router(liquid_router)

from routers.migration import router as migration_router
app.include_router(migration_router)

from routers.app_config import router as app_config_router
app.include_router(app_config_router)

from routers.projects import router as projects_router
app.include_router(projects_router)

# Vercel serverless handler
handler = Mangum(app, lifespan="off")
