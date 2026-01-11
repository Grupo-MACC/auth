# -*- coding: utf-8 -*-
"""Broker RabbitMQ del microservicio Auth.

Responsabilidades (solo publicación):
    - Publicar el estado del microservicio Auth:
        * auth.running
        * auth.not_running
    - Publicar evento de usuario creado:
        * user.created
"""

from __future__ import annotations

import json
import logging
from typing import Literal

from aio_pika import Message

from microservice_chassis_grupo2.core.rabbitmq_core import get_channel, declare_exchange

logger = logging.getLogger(__name__)

# =============================================================================
# Constantes RabbitMQ (routing keys / colas / topics)
# =============================================================================

# Estados válidos publicados por Auth
AUTH_STATUS_RUNNING = "running"
AUTH_STATUS_NOT_RUNNING = "not_running"
AuthStatus = Literal["running", "not_running"]

# Routing keys
RK_AUTH_RUNNING = "auth.running"
RK_AUTH_NOT_RUNNING = "auth.not_running"
RK_USER_CREATED = "user.created"

# Nombre de servicio (incluido en payload)
SERVICE_NAME = "auth"


# =============================================================================
# Helpers internos
# =============================================================================
#region 0. HELPERS
def _build_json_message(payload: dict) -> Message:
    """Construye un mensaje JSON persistente.

    Reglas:
        - content_type='application/json'
        - delivery_mode=2 (persistente)
    """
    return Message(
        body=json.dumps(payload).encode(),
        content_type="application/json",
        delivery_mode=2,
    )


def _auth_status_to_routing_key(status: str) -> str:
    """Mapea el status de auth a su routing key.

    Args:
        status: 'running' o 'not_running'

    Returns:
        Routing key correspondiente: 'auth.running' o 'auth.not_running'
    """
    if status == AUTH_STATUS_RUNNING:
        return RK_AUTH_RUNNING
    if status == AUTH_STATUS_NOT_RUNNING:
        return RK_AUTH_NOT_RUNNING
    raise ValueError(f"Estado no válido: {status!r}")


async def _publish(exchange, routing_key: str, payload: dict) -> None:
    """Publica un payload JSON en el exchange indicado con routing_key."""
    await exchange.publish(_build_json_message(payload), routing_key=routing_key)


# =============================================================================
# API pública (la usa el microservicio Auth)
# =============================================================================
#region 1. PUBLISHERS
async def publish_auth_status(status: AuthStatus) -> None:
    """Publica el estado actual del microservicio Auth en RabbitMQ.

    Mantiene la funcionalidad original:
        - Publica a exchange general (declare_exchange)
        - routing_key:
            * auth.running
            * auth.not_running
        - Si hay error, log + re-raise (para que el caller se entere)

    Args:
        status: 'running' o 'not_running'
    """
    connection = None
    try:
        routing_key = _auth_status_to_routing_key(status)

        connection, channel = await get_channel()
        exchange = await declare_exchange(channel)

        payload = {
            "service": SERVICE_NAME,
            "status": status,
            "message": f"Authentication service is {'running' if status == AUTH_STATUS_RUNNING else 'not running'}",
        }

        await _publish(exchange=exchange, routing_key=routing_key, payload=payload)
        logger.info("[AUTH] 📢 Publicado %s → %s", routing_key, payload)

    except Exception:
        logger.exception("[AUTH] ❌ Error al publicar estado de auth: %s", status)
        raise
    finally:
        if connection:
            await connection.close()


async def publish_user_registered(user_id: str | int) -> None:
    """Publica el evento user.created cuando un usuario se registra/crea.

    Mantiene la funcionalidad original:
        - routing_key: user.created
        - Si hay error: log (sin re-raise, como tenías)

    Args:
        user_id: id del usuario creado
    """
    connection = None
    try:
        connection, channel = await get_channel()
        exchange = await declare_exchange(channel)

        payload = {
            "message": "User has been created",
            "user_id": str(user_id),
        }

        await _publish(exchange=exchange, routing_key=RK_USER_CREATED, payload=payload)
        logger.info("[AUTH] 📢 Publicado %s → %s", RK_USER_CREATED, payload)

    except Exception:
        logger.exception("[AUTH] ❌ Error al publicar user.created (user_id=%s)", user_id)
    finally:
        if connection:
            await connection.close()
