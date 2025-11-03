#!/bin/bash
set -e

echo "Service: ${SERVICE_NAME}"
IP=$(hostname -i)
export IP
echo "IP: ${IP}"

terminate() {
  echo "Termination signal received, shutting down..."
  kill -SIGTERM "$UVICORN_PID"
  wait "$UVICORN_PID"
  echo "Uvicorn has been terminated"
}

trap terminate SIGTERM SIGINT

echo "Starting Uvicorn with TLS (mTLS enforced)..."

uvicorn app_auth.main:app \
  --host 0.0.0.0 \
  --port 5004 \
  --ssl-keyfile /certs/auth/auth-key.pem \
  --ssl-certfile /certs/auth/auth-cert.pem \
  --ssl-ca-certs /certs/ca.pem \
  --ssl-cert-reqs 1 &

UVICORN_PID=$!
wait "$UVICORN_PID"