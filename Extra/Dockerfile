# Cau truc V10.3: config.py o GOC, ma nguon o Backend/, giao dien o Frontend/.
# Build tu THU MUC GOC cua du an (context = .., khong phai Extra/):
#   docker compose -f Extra\docker-compose.yml up --build
# LUU Y: cau hinh Docker da cap nhat theo cau truc moi nhung CHUA CHAY THU o V10.3.
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

COPY config.py ./config.py
COPY Backend ./Backend
COPY Frontend ./Frontend
COPY Database/schema.sql ./Database/schema.sql
RUN mkdir -p /data /srv/Utility/finetune

EXPOSE 8000 8765

# Mac dinh chay web app; dich vu mcp-search ghi de command trong docker-compose.yml
CMD ["python", "Backend/main.py"]
