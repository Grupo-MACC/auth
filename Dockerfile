FROM python:3.12-slim-bookworm

# Configuration will be done as root
USER root

# Update pip, copy requirements file and install dependencies
RUN pip install --no-cache-dir --upgrade pip;
COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

# We will be working on this folder
WORKDIR /home/pyuser/code
ENV PYTHONPATH=/home/pyuser/code/app_auth
ENV SQLALCHEMY_DATABASE_URL=sqlite+aiosqlite:///./auth.db
ENV RABBITMQ_USER=guest
ENV RABBITMQ_PASSWORD=guest
ENV RABBITMQ_HOST=10.0.11.30
# Claves RSA compartidas entre réplicas (volumen Docker)
ENV PRIVATE_KEY_PATH=/home/pyuser/keys/private.pem
ENV PUBLIC_KEY_PATH=/home/pyuser/keys/public.pem
# Consul Service Discovery
ENV CONSUL_HOST=10.0.11.40
ENV CONSUL_PORT=8500
ENV SERVICE_NAME=auth
ENV SERVICE_PORT=5004
ENV SERVICE_ID=auth


# Create a non root user and keys directory
RUN useradd -u 1000 -d /home/pyuser -m pyuser && \
    mkdir -p /home/pyuser/keys && \
    chown -R pyuser:pyuser /home/pyuser

# Copy the entrypoint script (executed when the container starts) and add execution permissions
COPY entrypoint.sh /home/pyuser/code/entrypoint.sh
RUN chmod +x /home/pyuser/code/entrypoint.sh

# Switch user so container is run as non-root user
USER 1000

# Copy the app to the container
COPY app_auth /home/pyuser/code/app_auth

# Run the application
ENTRYPOINT ["/home/pyuser/code/entrypoint.sh"]