import asyncio
import json
import logging
from aio_pika import connect_robust, Message, ExchangeType
from broker.setup_rabbitmq import RABBITMQ_HOST, EXCHANGE_NAME

logger = logging.getLogger(__name__)

async def publish_auth_status(status: str):
    """
    Publica el estado actual del microservicio Auth en RabbitMQ.
    status: puede ser 'running' o 'not_running'
    """
    assert status in ("running", "not_running"), "Estado no válido"

    try:
        connection = await connect_robust(RABBITMQ_HOST)
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            EXCHANGE_NAME,
            ExchangeType.DIRECT,
            durable=True
        )

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