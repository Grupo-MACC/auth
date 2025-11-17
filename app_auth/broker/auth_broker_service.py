import json
import logging
from microservice_chassis_grupo2.core.rabbitmq_core import get_channel, declare_exchange, declare_exchange_logs
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
    await publish_to_logger(
        message=message_body,
        topic=f"auth.info" if status == "running" else "auth.error"
    )

async def publish_user_registered(user_id: str):
    try:
        connection, channel = await get_channel()
        
        exchange = await declare_exchange(channel)
        
        message_body = {
            "message": "User has been created",
            "user_id": user_id
        }
        
        message = Message(
            body=json.dumps(message_body).encode(),
            content_type="application/json",
            delivery_mode=2
        )
        
        routing_key = "user.created"
        await exchange.publish(message, routing_key)
        logger.info(f"📢 Enviado mensaje a RabbitMQ: {message_body}")
    except Exception as e:
        logger.error(f"❌ Error al publicar la creacion de un nuevo usuario: {e}")
    finally:
        if "connection" in locals():
            await connection.close()
    await publish_to_logger(
        message={"message": "Nuevo usuario creado", "user_id": user_id},
        topic="auth.info"
    )

async def publish_to_logger(message: dict, topic: str):
    """
    Envía un log estructurado al sistema de logs.
    topic: 'auth.info', 'auth.error', 'auth.debug', etc.
    """
    connection = None
    try:
        connection, channel = await get_channel()
        exchange = await declare_exchange_logs(channel)

        log_data = {
            "measurement": "logs",
            "service": topic.split(".")[0],   # 'auth'
            "severity": topic.split(".")[1],  # 'info', 'error', etc.
            **message,
        }

        msg = Message(
            body=json.dumps(log_data).encode(),
            content_type="application/json",
            delivery_mode=2,
        )

        await exchange.publish(message=msg, routing_key=topic)

    except Exception as e:
        print(f"[AUTH] Error publishing to logger: {e}")
    finally:
        if connection:
            await connection.close()
