# Python 3.12 এর স্লিম ভার্সন ব্যবহার করুন
FROM python:3.12-slim

# সিস্টেম প্যাকেজ আপডেট এবং build-essential ইনস্টল করুন
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# অ্যাপ্লিকেশনের ওয়ার্কিং ডিরেক্টরি সেট করা
WORKDIR /app

# প্রথমে শুধু requirements.txt কপি করা
COPY requirements.txt .

# সেটআপটুলস এবং পিপ ইনস্টল/আপগ্রেড করা
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# ডিপেন্ডেন্সি ইনস্টল করা
RUN pip install --no-cache-dir -r requirements.txt

# বাকি অ্যাপ্লিকেশন কোড কপি করা
COPY src/ ./src/

# পোর্ট এক্সপোজ করা
EXPOSE 8050

# Gunicorn সার্ভার চালানোর কমান্ড
CMD ["gunicorn", "src.api.bot_dashboard:server", \
     "--bind", "0.0.0.0:8050", \
     "--workers", "4", \
     "--timeout", "120", \
     "--worker-class", "gthread", \
     "--threads", "3"]