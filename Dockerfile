# Dockerfile

FROM python:3.12-slim  # Python 3.12 ব্যবহার করুন

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

EXPOSE 8050

CMD ["gunicorn", "src.api.bot_dashboard:server", "--bind", "0.0.0.0:8050", "--workers", "4", "--timeout", "120", "--worker-class", "gthread", "--threads", "3"]
