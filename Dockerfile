# অ্যাপ্লিকেশনের ওয়ার্কিং ডিরেক্টরি
WORKDIR /app

# PYTHONPATH সেট করা
ENV PYTHONPATH=/app/src

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
     "--workers", "1", \
     "--timeout", "120", \
     "--worker-class", "gthread", \
     "--threads", "3", \
     "--preload"]
