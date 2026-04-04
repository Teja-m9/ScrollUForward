FROM python:3.11-slim

WORKDIR /app

# Install shared + gateway deps
COPY microservices/shared/requirements.txt /tmp/shared_req.txt
COPY microservices/gateway/requirements.txt /tmp/gateway_req.txt
RUN pip install --no-cache-dir -r /tmp/shared_req.txt -r /tmp/gateway_req.txt

# Copy shared modules
COPY microservices/shared/ ./microservices/shared/

# Copy gateway
COPY microservices/gateway/ ./microservices/gateway/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "microservices.gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
