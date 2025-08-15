# src/api/bot_service.py
from fastapi import FastAPI, BackgroundTasks
from src.trading.bot import TradingBot

app = FastAPI()
bot = TradingBot()

@app.post("/start")
async def start_bot(background_tasks: BackgroundTasks):
    if not bot.running:
        background_tasks.add_task(bot.run)
        return {"status": "started"}
    return {"status": "already running"}

@app.post("/stop")
def stop_bot():
    if bot.running:
        bot.stop()
        return {"status": "stopped"}
    return {"status": "not running"}

@app.get("/health")
def health():
    return {"status": "ok"}
  
