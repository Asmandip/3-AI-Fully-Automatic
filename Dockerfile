# Python 3.12 full version ব্যবহার
FROM python:3.12

# সিস্টেম প্যাকেজ আপডেট এবং প্রয়োজনীয় build tools ইনস্টল
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

# অ্যাপ্লিকেশনের ওয়ার্কিং ডিরেক্টরি
WORKDIR /app

# pip, setuptools, wheel আপগ্রেড
RUN python -m pip install --upgrade pip setuptools wheel

# requirements.txt কপি করা
COPY requirements.txt .

# Python dependencies ইনস্টল করা
RUN pip install --no-cache-dir --verbose -r requirements.txt

# বাকি অ্যাপ্লিকেশন কোড কপি করা
COPY src/ ./src/

# পোর্ট এক্সপোজ করা
EXPOSE 8050

# Gunicorn সার্ভার চালানোর কমান্ড
CMD ["gunicorn", "src.api.bot_dashboard:server", \
     "--bind", "0.0.0.0:8050", \
     "--workers", "2", \
     "--timeout", "120", \
     "--worker-class", "gthread", \
     "--threads", "3"]