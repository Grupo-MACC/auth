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
from sql import models
from microservice_chassis_grupo2.sql import database
from sql import init_db 
from sqlalchemy.ext.asyncio import async_sessionmaker
from broker import auth_broker_service
# Configure logging
logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "logging.ini"))
logger = logging.getLogger(__name__)

# App Lifespan
@asynccontextmanager
async def lifespan(__app: FastAPI):
    """Lifespan context manager."""


    try:
        try:
            logger.info("Initializing database connection")
            await database.init_database()
            logger.info("Database connection initialized")
        except Exception as e:
            logger.error(f"Could not initialize database connection: {e}", exc_info=True)
            with open("/home/pyuser/code/error.txt", "w") as f:
                f.write(f"{e}\n")
            raise e
        
        try:
            logger.info("Creating database tables")
            async with database.engine.begin() as conn:
                await conn.run_sync(models.Base.metadata.create_all)
        except Exception:
            logger.error("Could not create tables at startup")

        # 🔧 Inicializar roles y admin
        async_session = async_sessionmaker(database.engine, expire_on_commit=False)
        async with async_session() as session:
            await init_db(session)
        
        # Publicar auth.running con delay para asegurar que uvicorn está listo
        # El yield marca que el startup completó, pero uvicorn no escucha hasta después
        async def _publish_running_delayed():
            await asyncio.sleep(10.0)  # Esperar para que uvicorn esté completamente listo
            try:
                logger.info("📤 Intentando publicar auth.running...")
                await auth_broker_service.publish_auth_status("running")
                logger.info("✅ Mensaje auth.running publicado correctamente")
            except Exception as e:
                logger.error(f"❌ Could not publish 'running' status: {e}", exc_info=True)
        
        # Lanzamos la tarea en background - se ejecutará después de que uvicorn esté listo
        publish_task = asyncio.create_task(_publish_running_delayed())
        
        yield
    finally:
        logger.info("Shutting down database")
        await database.engine.dispose()
        try:
            await auth_broker_service.publish_auth_status("not_running")
        except Exception as e:
            logger.error(f"Could not publish 'not_running' status: {e}")

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
