# Dockerfile for Python Services
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install cryptography

COPY common /app/common
COPY proto /app/proto

# Copy all services source code (optimization: could copy only specific service)
COPY issuance_service /app/issuance_service
COPY subscription_service /app/subscription_service
COPY gateway_service /app/gateway_service
COPY internal_service /app/internal_service

# Pre-compile protos
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/subscription.proto

ENV PYTHONPATH=/app

# Default command (overridden in docker-compose)
CMD ["python", "--version"]
