from microservice_chassis_grupo2.core.rabbitmq_core import get_channel, declare_exchange

async def setup_rabbitmq():
    """
    Configura RabbitMQ creando el exchange y las colas necesarias
    usando aio_pika (asíncrono).
    """
    connection, channel = await get_channel()
        
    exchange = await declare_exchange(channel)
    
    auth_running_queue = await channel.declare_queue("auth_running_queue", durable=True)
    auth_not_running_queue = await channel.declare_queue("auth_not_running_queue", durable=True)
    
    await auth_running_queue.bind(exchange, routing_key="auth.running")
    await auth_not_running_queue.bind(exchange, routing_key="auth.not_running")
    
    print("✅ RabbitMQ configurado correctamente (exchange + colas creadas).")
    
    await connection.close()