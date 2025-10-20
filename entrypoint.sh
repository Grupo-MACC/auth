#!/bin/bash

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

uvicorn app_auth.main:app \
  --host 0.0.0.0 \
  --port 5004 &

UVICORN_PID=$!

wait "$UVICORN_PID"
