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
from consul_client import create_consul_client

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

# App Lifespan
@asynccontextmanager
async def lifespan(__app: FastAPI):
    """Lifespan context manager."""
    consul_client = create_consul_client()
    # Generar ID único para cada réplica
    service_id = os.getenv("SERVICE_ID", f"auth-{uuid.uuid4().hex[:8]}")
    service_name = os.getenv("SERVICE_NAME", "auth")
    service_port = int(os.getenv("SERVICE_PORT", 5004))
    # Obtener IP real del contenedor para Consul
    container_ip = get_container_ip()

    try:
        logger.info(f"Starting up replica {service_id} at {container_ip}")
        
        # Register with Consul using container IP
        result = await consul_client.register_service(
    
            service_name=service_name,
            service_id=service_id,
            service_port=service_port,
            service_address=container_ip,  # IP real del contenedor
            tags=["fastapi", service_name],
            meta={"version": "2.0.0"},
            health_check_url=f"http://{container_ip}:{service_port}/docs"
        )
        logger.info(f"✅ Consul service registration: {result}")

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
        yield
    finally:
        logger.info("Shutting down database")
        await database.engine.dispose()
        try:
            await auth_broker_service.publish_auth_status("not_running")
        except Exception as e:
            logger.error(f"Could not publish 'not_running' status: {e}")
        
        # Deregister from Consul
        result = await consul_client.deregister_service(service_id)
        logger.info(f"✅ Consul service deregistration: {result}")

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
    uvicorn.run("main:app", host="0.0.0.0", port=5004, reload=True)
