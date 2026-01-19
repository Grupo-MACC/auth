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
ENV RABBITMQ_USER=guest
ENV RABBITMQ_PASSWORD=guest
# Claves RSA compartidas entre réplicas (volumen Docker)
ENV PRIVATE_KEY_PATH=/home/pyuser/keys/private.pem
ENV PUBLIC_KEY_PATH=/home/pyuser/keys/public.pem
# Consul Service Discovery
ENV SERVICE_PORT=5004
ENV CONSUL_PORT=8501
ENV CONSUL_SCHEME=https
ENV CONSUL_CA_FILE=/certs/ca.pem
ENV CONSUL_REGISTRATION_EVENT_URL=http://54.225.33.0:8081/restart
ENV SERVICE_CERT_FILE=/certs/auth/auth-cert.pem
ENV SERVICE_KEY_FILE=/certs/auth/auth-key.pem
ENV DB_NAME=auth_db
ENV CONSUL_HOST=10.1.11.40

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