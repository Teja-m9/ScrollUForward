FROM python:3.11-slim

WORKDIR /app

COPY microservices/shared/requirements.txt /tmp/req.txt
RUN pip install --no-cache-dir -r /tmp/req.txt

COPY microservices/shared/ ./microservices/shared/
COPY microservices/services/chat/ ./microservices/services/chat/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8005

# Use --ws websockets for WebSocket support
CMD ["uvicorn", "microservices.services.chat.main:app", "--host", "0.0.0.0", "--port", "8005", "--ws", "websockets"]
