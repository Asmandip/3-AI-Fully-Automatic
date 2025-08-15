# Dockerfile
FROM python:3.11-slim


ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app/src"

RUN apt-get update && apt-get install -y curl build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8050/health || exit 1

EXPOSE 8050

CMD ["gunicorn", "src.api.bot_dashboard:server", "--bind", "0.0.0.0:8050", "--workers", "4"]
