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
    # avoid blocking startup if DB is slow
    try:
        await bot.update_settings()
    except Exception:
        pass

@app.post("/start")
async def start_bot(background_tasks: BackgroundTasks):
    try:
        if not bot.running:
            background_tasks.add_task(bot.run)
            return {"status": "started"}
        return {"status": "already running"}
    except Exception as e:
        logger.error(f"Start failed: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.post("/stop")
async def stop_bot():
    try:
        if bot.running:
            bot.stop()
            return {"status": "stopped"}
        return {"status": "not running"}
    except Exception as e:
        logger.error(f"Stop failed: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/health")
async def health():
    try:
        return {"status": "ok", "bot_running": bot.running}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "error", "message": str(e)}