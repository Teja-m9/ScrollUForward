FROM python:3.11-slim

WORKDIR /app

COPY microservices/shared/requirements.txt /tmp/req.txt
RUN pip install --no-cache-dir -r /tmp/req.txt

COPY microservices/shared/ ./microservices/shared/
COPY microservices/services/discussion/ ./microservices/services/discussion/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8003

CMD ["uvicorn", "microservices.services.discussion.main:app", "--host", "0.0.0.0", "--port", "8003"]
