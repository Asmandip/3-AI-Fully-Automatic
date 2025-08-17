# src/api/bot_service.py
from fastapi import FastAPI, BackgroundTasks
from src.trading.bot import TradingBot
from src.database.mongo import MongoDB
from src.utils.logger import get_logger

logger = get_logger("BotService")

app = FastAPI()
db = MongoDB()
bot = TradingBot(db)

@app.on_event("startup")
async def startup_event():
    # Initialize settings on startup
    await bot.update_settings()

@app.post("/start")
async def start_bot(background_tasks: BackgroundTasks):
    if not bot.running:
        background_tasks.add_task(bot.run)
        return {"status": "started"}
    return {"status": "already running"}

@app.post("/stop")
async def stop_bot():
    if bot.running:
        bot.stop()
        return {"status": "stopped"}
    return {"status": "not running"}

@app.get("/health")
async def health():
    return {"status": "ok", "bot_running": bot.running}