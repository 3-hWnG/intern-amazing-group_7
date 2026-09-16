FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000 \
    RUNTIME_DIR=/data

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
RUN mkdir -p /data /srv/finetune

EXPOSE 8000 8765

# Mặc định chạy web app; dịch vụ mcp-search ghi đè command trong docker-compose.yml
CMD ["python", "app/main.py"]
