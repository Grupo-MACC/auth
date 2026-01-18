# -*- coding: utf-8 -*-
"""Main file to start FastAPI application."""
import logging.config
import os
import socket
import uuid
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
import asyncio
from routers import auth_router, user_router
from sql import models, database
from sql import init_db 
from sqlalchemy.ext.asyncio import async_sessionmaker
from broker import auth_broker_service
from consul_client import get_consul_client

# Configure logging
logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "logging.ini"))
logger = logging.getLogger(__name__)

def get_container_ip():
    """Get the container's IP address."""
    try:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)
    except Exception:
        return "127.0.0.1"

async def _publish_running_delayed() -> None:
    """
    Publica auth.running cuando el servidor ya debería estar aceptando requests.

    Por qué:
        - Dentro del lifespan antes del yield, FastAPI aún no sirve HTTP.
        - Los consumidores consultan Consul passing=true y pueden fallar si Auth no está ready.
    """
    await asyncio.sleep(1.0)
    await auth_broker_service.publish_auth_status("running")


# App Lifespan
@asynccontextmanager
async def lifespan(__app: FastAPI):
    """Lifespan context manager."""
    consul = get_consul_client()
    # Generar ID único para cada réplica
    service_id = os.getenv("SERVICE_ID", f"auth-{uuid.uuid4().hex[:8]}")

    container_ip = get_container_ip()

    try:
        logger.info(f"Starting up replica {service_id} at {container_ip}")
        
        # Registro "auto" (usa SERVICE_* y CONSUL_* desde entorno)
        ok = await consul.register_self()
        logger.info("✅ Consul register_self: %s", ok)
        
        try:
            logger.info("Creating database tables")
            async with database.engine.begin() as conn:
                await conn.run_sync(models.Base.metadata.create_all)
        except Exception as e:
            logger.exception("Could not create tables at startup: %s", e)
            raise

        # 🔧 Inicializar roles y admin
        async_session = async_sessionmaker(database.engine, expire_on_commit=False)
        async with async_session() as session:
            await init_db(session)
        
        try:
            logger.info("📤 Intentando publicar auth.running...")
            await auth_broker_service.publish_auth_status("running")
            logger.info("✅ Mensaje auth.running publicado correctamente")
        except Exception as e:
            logger.error(f"❌ Could not publish 'running' status: {e}", exc_info=True)
        
        asyncio.create_task(_publish_running_delayed())
        
        yield
    finally:
        logger.info("Shutting down database")
        await database.engine.dispose()
        try:
            await auth_broker_service.publish_auth_status("not_running")
        except Exception as e:
            logger.error(f"Could not publish 'not_running' status: {e}")
        
        # Deregistro (auto) + cierre del cliente HTTP
        try:
            ok = await consul.deregister_self()
            logger.info("✅ Consul deregister_self: %s", ok)
        except Exception:
            logger.exception("Error desregistrando en Consul")

        try:
            await consul.aclose()
        except Exception:
            logger.exception("Error cerrando cliente Consul")

# OpenAPI Documentation
APP_VERSION = os.getenv("APP_VERSION", "2.0.0")
logger.info("Running app version %s", APP_VERSION)

app = FastAPI(
    redoc_url=None,
    version=APP_VERSION,
    servers=[{"url": "/", "description": "Development"}],
    license_info={
        "name": "MIT License",
        "url": "https://choosealicense.com/licenses/mit/",
    },
    lifespan=lifespan,
)

app.include_router(auth_router.router)
app.include_router(user_router.router)

if __name__ == "__main__":
    """
    Application entry point. Starts the Uvicorn server with SSL configuration.
    Runs the FastAPI application on host.
    """
    cert_file = os.getenv("SERVICE_CERT_FILE", "/certs/auth/auth-cert.pem")
    key_file = os.getenv("SERVICE_KEY_FILE", "/certs/auth/auth-key.pem")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("SERVICE_PORT", "5004")),
        reload=True,
        ssl_certfile=cert_file,
        ssl_keyfile=key_file,
    )
