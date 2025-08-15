# src/trading/bot.py
import asyncio
import logging

class TradingBot:
    def __init__(self):
        self.running = False
        self.logger = logging.getLogger("TradingBot")

        self.pairs = []
        self.timeframes = []
        self.strategy = 'Scalping'
        self.strategy_mode = 'auto'  # manual or auto
        self.trade_mode = 'paper'    # paper or real

    async def run(self):
        self.running = True
        self.logger.info(f"Bot started with pairs: {self.pairs}, "
                         f"timeframes: {self.timeframes}, strategy: {self.strategy}({self.strategy_mode}), "
                         f"trade_mode: {self.trade_mode}")
        while self.running:
            try:
                # Example scalping logic placeholder
                self.logger.debug(f"Running scalping for {self.pairs} on {self.timeframes}")
                await asyncio.sleep(5)
            except Exception as e:
                self.logger.error(f"Error in trading loop: {e}")

        self.logger.info("Bot stopped.")

    def stop(self):
        if self.running:
            self.running = False
            self.logger.info("Stop signal received.")
