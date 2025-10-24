import json
import logging
from microservice_chassis_grupo2.core.rabbitmq_core import get_channel, declare_exchange
from aio_pika import Message

logger = logging.getLogger(__name__)

async def publish_auth_status(status: str):
    """
    Publica el estado actual del microservicio Auth en RabbitMQ.
    status: puede ser 'running' o 'not_running'
    """
    assert status in ("running", "not_running"), "Estado no válido"

    try:
        connection, channel = await get_channel()
        
        exchange = await declare_exchange(channel)

        message_body = {
            "service": "auth",
            "status": status,
            "message": f"Authentication service is {'running' if status == 'running' else 'not running'}"
        }

        message = Message(
            body=json.dumps(message_body).encode(),
            content_type="application/json",
            delivery_mode=2
        )

        routing_key = f"auth.{status}"
        await exchange.publish(message, routing_key=routing_key)

        logger.info(f"📢 Enviado mensaje a RabbitMQ: {message_body}")
    except Exception as e:
        logger.error(f"❌ Error al publicar estado de auth: {e}")
    finally:
        if 'connection' in locals():
            await connection.close()