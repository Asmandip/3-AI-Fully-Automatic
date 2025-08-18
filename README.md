## ট্রেডিং বট – বাংলা README

এই রিপোজিটরিটি একটি অ্যাসিঙ্ক্রোনাস ক্রিপ্টো ট্রেডিং বট, একটি FastAPI ভিত্তিক কন্ট্রোল API এবং একটি Dash/Plotly ভিত্তিক লাইভ ড্যাশবোর্ড নিয়ে তৈরি। আপনি পেপার ট্রেডিং বা লাইভ ট্রেডিং চালাতে পারেন, স্ট্র্যাটেজি কনফিগার করতে পারেন, আর MongoDB-তে ট্রেড ও সেটিংস সংরক্ষণ হয়।

### প্রধান বৈশিষ্ট্য
- **অ্যাসিঙ্ক্রোনাস ট্রেডিং লুপ**: একাধিক পেয়ার ও টাইমফ্রেমে একসাথে সিগনাল প্রসেসিং।
- **স্ট্র্যাটেজি সাপোর্ট**: `Scalping`, `Momentum`, `Mean Reversion` (চয়েস `src/trading/strategies` থেকে `STRATEGY_MAP` দ্বারা)
- **ট্রেড মোড**: **পেপার** (ডিফল্ট) ও **লাইভ** (API Key/Secret প্রয়োজন)
- **রিস্ক ম্যানেজমেন্ট**: ভোলাটিলিটি-ভিত্তিক সাইজিং ও ট্রেড এক্সেপ্টেন্স চেক
- **ড্যাশবোর্ড**: পেয়ার/টাইমফ্রেম/স্ট্র্যাটেজি কনফিগার, বট স্টার্ট/স্টপ, ট্রেড লগ, ক্যান্ডেলস্টিক চার্ট
- **API**: FastAPI এন্ডপয়েন্টের মাধ্যমে বট চালু/বন্ধ ও হেলথ চেক
- **পার্সিস্টেন্স**: MongoDB-তে সেটিংস ও ট্রেড হিস্টোরি সংরক্ষণ
- **ডিপ্লয়মেন্ট রেডি**: Dockerfile, Kubernetes ম্যানিফেস্ট, Render কনফিগ (`render.yaml`)

### আর্কিটেকচার ও কম্পোনেন্টস
- **কোর বট**: `src/trading/bot.py`
  - সেটিংস লোড করে (`MongoDB.get_settings`) পেয়ার, টাইমফ্রেম, স্ট্র্যাটেজি, ট্রেড মোড ইত্যাদি আপডেট করে
  - মার্কেট ডেটা ফেচ করে সিগনাল জেনারেট করে এবং `execute_trade` চালায়
  - পেপার মোডে ব্যালান্স সিমুলেট করে, লাইভ মোডে এক্সচেঞ্জ ক্লায়েন্ট ব্যবহার করে
- **API সার্ভিস**: `src/api/bot_service.py`
  - এন্ডপয়েন্ট: `/start`, `/stop`, `/health`
  - ব্যাকগ্রাউন্ডে বট রান/স্টপ করে
- **ড্যাশবোর্ড**: `src/api/bot_dashboard.py`
  - Dash/Plotly UI, কনফিগ সেভ করে MongoDB-তে, API-র সাথে কথা বলে বট কন্ট্রোল করে
  - `BASE_API_URL` পরিবেশ চলক দ্বারা API টার্গেট নির্ধারণ
- **ডাটাবেস লেয়ার**: `src/database/mongo.py`
  - `MONGO_URI` ব্যবহার করে MongoDB কানেক্ট, `trades` ও `settings` কালেকশন হ্যান্ডেল করে
- **ডিপ্লয়মেন্ট**
  - Docker: `Dockerfile` (ডিফল্টভাবে ড্যাশবোর্ড সার্ভার 8050 পোর্টে চালায়)
  - Kubernetes: `k8s/production/deployment.yaml` (হেলথ চেক 8000 পোর্টে; API কনটেইনারের জন্য উপযুক্ত)

### কাজের ধারা (উচ্চ-স্তরে)
1. বট `MongoDB` থেকে সর্বশেষ সেটিংস পড়ে (পেয়ার, টাইমফ্রেম, স্ট্র্যাটেজি, মোড, ট্রেড সাইজ)
2. প্রতিটি পেয়ার/টাইমফ্রেমের জন্য ইতিহাসগত ডেটা ফেচ করে এবং সিগনাল নির্ণয় করে
3. সিগনাল থাকলে `RiskManager` ভোলাটিলিটি ও ব্যালান্স-ভিত্তিক ফিল্টার চালায়
4. অনুমোদিত হলে পেপার/লাইভ ট্রেড এক্সিকিউট করে এবং রেজাল্ট MongoDB-তে সংরক্ষণ করে
5. ড্যাশবোর্ডের মাধ্যমে কনফিগ আপডেট ও ট্রেড/স্ট্যাটাস ভিজুয়ালাইজ করা যায়

## API সার্ভিস (FastAPI)
- সার্ভার অ্যাপ: `src/api/bot_service.py`
- ডিফল্ট পোর্ট: `8000` (লোকাল রান টাইমে)

### এন্ডপয়েন্টসমূহ
- `POST /start`: ব্যাকগ্রাউন্ডে বট চালু করবে
- `POST /stop`: বট বন্ধ করবে
- `GET /health`: `{ status: 'ok', bot_running: bool }`

### উদাহরণ (cURL)
```bash
curl -X POST http://localhost:8000/start
curl -X POST http://localhost:8000/stop
curl http://localhost:8000/health
```

## ড্যাশবোর্ড (Dash/Plotly)
- অ্যাপ: `src/api/bot_dashboard.py`
- ডিফল্ট পোর্ট: `8050`
- পরিবেশ চলক `BASE_API_URL` সেট করে API সার্ভিসের URL নির্ধারণ করুন (ডিফল্ট: `http://localhost:8000`)
- ফিচার: বট স্টার্ট/স্টপ, পেয়ার/টাইমফ্রেম/স্ট্র্যাটেজি/মোড কনফিগ, ট্রেড লগ, ক্যান্ডেলস্টিক চার্ট

লোকাল রান উদাহরণ:
```bash
python -m src.api.bot_dashboard
# ব্রাউজার: http://localhost:8050
```

## ইনস্টলেশন ও লোকাল রান

### পূর্বশর্ত
- Python 3.12+
- চলমান MongoDB ইনস্ট্যান্স (লোকাল বা রিমোট)

### সেটআপ
```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### .env উদাহরণ
```bash
MONGO_URI=mongodb://localhost:27017
BASE_API_URL=http://localhost:8000
LOG_LEVEL=INFO
```

### সার্ভিসগুলো চালানো
- API (FastAPI, পোর্ট 8000):
```bash
uvicorn src.api.bot_service:app --host 0.0.0.0 --port 8000
```

- ড্যাশবোর্ড (Dash, পোর্ট 8050):
```bash
python -m src.api.bot_dashboard
```

## Docker

### ইমেজ বিল্ড
```bash
docker build -t trading-bot:latest .
```

### ড্যাশবোর্ড কনটেইনার (পোর্ট 8050)
Dockerfile ডিফল্টভাবে Gunicorn দিয়ে ড্যাশবোর্ড সার্ভার চালায়:
```bash
docker run --rm -p 8050:8050 \
  -e MONGO_URI="mongodb://host.docker.internal:27017" \
  -e BASE_API_URL="http://host.docker.internal:8000" \
  trading-bot:latest
```

### API কনটেইনার (পোর্ট 8000)
API চালাতে `CMD`/`ENTRYPOINT` ওভাররাইড করুন:
```bash
docker run --rm -p 8000:8000 \
  -e MONGO_URI="mongodb://host.docker.internal:27017" \
  trading-bot:latest \
  uvicorn src.api.bot_service:app --host 0.0.0.0 --port 8000
```

## Kubernetes (প্রোডাকশন)
- ম্যানিফেস্ট: `k8s/production/deployment.yaml`
- ডিফল্ট `containerPort: 8000` ও readiness/liveness `/health` — তাই এটি API কনটেইনারের জন্য উপযুক্ত।
- ইমেজ আপডেট: `spec.template.spec.containers[0].image` আপনার রেজিস্ট্রির ইমেজ দিয়ে প্রতিস্থাপন করুন।
- প্রয়োজনীয় সিক্রেট: `mongo-secret`-এ `MONGO_URI` কী থাকতে হবে।

ডিপ্লয় উদাহরণ:
```bash
kubectl apply -f k8s/production/deployment.yaml
kubectl rollout status deploy/trading-bot
```

## কনফিগারেশন
- **পেয়ার**: ড্যাশবোর্ড Bitget futures (USDT swap) থেকে পেয়ার লোড করে
- **টাইমফ্রেম**: `['1m','3m','5m','15m','1h','4h','1d']`
- **স্ট্র্যাটেজি**: `Scalping` (ডিফল্ট), `Momentum`, `Mean Reversion`
- **স্ট্র্যাটেজি মোড**: `auto`/`manual`
- **ট্রেড মোড**: `paper`/`live` (লাইভে API Key/Secret বাধ্যতামূলক)
- **ট্রেড সাইজ**: ব্যালান্সের শতাংশ হিসেবে (ড্যাশবোর্ড স্লাইডার)

## লগিং ও মনিটরিং
- `src.utils.logger.get_logger` দ্বারা কনফিগারড লজার ব্যবহার করা হয়েছে
- `LOG_LEVEL` পরিবেশ চলকে লেভেল কনফিগার করুন (যথা `INFO`, `DEBUG`)
- Kubernetes anno সহ Prometheus scrape হিন্ট দেওয়া আছে (প্রয়োজনমতো এক্সপোজ করুন)

## সিকিউরিটি নোট
- API Key/Secret কখনোই রিপোতে কমিট করবেন না; কেবল পরিবেশ চলক/সিক্রেট ম্যানেজারে রাখুন
- `MONGO_URI` সিক্রেট হিসেবে ম্যানেজ করুন (K8s Secret/Render Env)
- লাইভ ট্রেডিং-এর আগে পেপার মোডে পর্যাপ্ত টেস্ট চালান

## ট্রাবলশুটিং
- **ড্যাশবোর্ডে বট স্ট্যাটাস Unknown**: `BASE_API_URL` কি সঠিক? API কি 8000 পোর্টে চলছে?
- **MongoDB কানেকশন ব্যর্থ**: `MONGO_URI` যাচাই করুন; নেটওয়ার্ক/অথ দরকার হলে সেট করুন
- **K8s health probe ফেল করছে**: কনটেইনারে কি API (8000) চলছে, না ড্যাশবোর্ড (8050)? ম্যানিফেস্ট/এন্ট্রিপয়েন্ট মিলিয়ে নিন
- **ডেটা/চার্ট খালি**: এক্সচেঞ্জ/ইন্টারনেট কানেক্টিভিটি ও পেয়ার/টাইমফ্রেম সিলেকশন চেক করুন

## অস্বীকৃতি (Disclaimer)
এই সফটওয়্যার শুধুমাত্র শিক্ষামূলক/গবেষণামূলক উদ্দেশ্যে। এটি আর্থিক পরামর্শ নয়। আপনার নিজ দায়িত্বে ব্যবহার করুন; বাজার ঝুঁকিপূর্ণ এবং ক্ষতির সম্ভাবনা আছে।

## অবদান
PR/ইস্যু স্বাগত। বড় পরিবর্তনের আগে সংক্ষিপ্ত প্রস্তাব দিন।

