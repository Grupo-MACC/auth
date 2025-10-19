from aio_pika import connect_robust, ExchangeType

RABBITMQ_HOST = "amqp://guest:guest@rabbitmq/"
EXCHANGE_NAME = "auth_active_exchange"

async def setup_rabbitmq():
    """
    Configura RabbitMQ creando el exchange y las colas necesarias
    usando aio_pika (asíncrono).
    """
    connection = await connect_robust(RABBITMQ_HOST)
    channel = await connection.channel()
    
    exchange = await channel.declare_exchange(
        EXCHANGE_NAME,
        ExchangeType.DIRECT,
        durable=True
    )
    
    auth_running_queue = await channel.declare_queue("auth_running_queue", durable=True)
    auth_not_running_queue = await channel.declare_queue("auth_not_running_queue", durable=True)
    
    await auth_running_queue.bind(exchange, routing_key="auth.running")
    await auth_not_running_queue.bind(exchange, routing_key="auth.not_running")
    
    print("✅ RabbitMQ configurado correctamente (exchange + colas creadas).")
    
    await connection.close()