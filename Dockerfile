# Python 3.12 এর ফুল ভার্সন ব্যবহার করুন (স্লিম নয়)
FROM python:3.12

# সিস্টেম প্যাকেজ আপডেট এবং প্রয়োজনীয় বিল্ড টুলস ইনস্টল
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    gfortran \
    libatlas-base-dev \
    libopenblas-dev \
    liblapack-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

# অ্যাপ্লিকেশনের ওয়ার্কিং ডিরেক্টরি সেট করা
WORKDIR /app

# প্রথমে শুধু requirements.txt কপি করা
COPY requirements.txt .

# pip, setuptools, এবং wheel আপগ্রেড করা
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# ডিপেন্ডেন্সি ইনস্টল করা (বিল্ড ক্যাশে সক্ষম করুন)
RUN pip install --no-cache-dir --verbose -r requirements.txt

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