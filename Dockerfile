# Python 3.12 বেস ইমেজ ব্যবহার
FROM python:3.12-slim

# অ্যাপ্লিকেশনের ওয়ার্কিং ডিরেক্টরি সেট করুন
WORKDIR /app

# PYTHONPATH সেট করুন, যাতে src ফোল্ডার মডিউলখুঁজতে পারে
ENV PYTHONPATH=/app/src

# system deps for scientific libs and build tools
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --upgrade pip setuptools wheel

# requirements.txt কপি করুন
COPY requirements.txt .

# Python dependencies ইনস্টল করুন
RUN pip install --no-cache-dir -r requirements.txt

# অ্যাপ্লিকেশনের সোর্স কোড কপি করুন
COPY src/ ./src/

# পোর্ট এক্সপোজ করুন
EXPOSE 8050

# Gunicorn সার্ভার চালানোর নির্দেশ দিন
CMD ["gunicorn", "src.api.bot_dashboard:server", "--bind", "0.0.0.0:8050", "--workers", "1", "--timeout", "120", "--worker-class", "gthread", "--threads", "3", "--preload"]
