# src/trading/bot.py

import asyncio
import logging
import random
import ccxt

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("TradingBot")

class TradingBot:
    def __init__(self):
        self.running = False
        self.logger = logger
        self.pairs = []
        self.timeframes = []
        self.strategy = 'Scalping'
        self.strategy_mode = 'auto'
        self.trade_mode = 'paper'
        self.balance = 100.0
        self.exchange = None

    async def run(self):
        self.running = True
        self.logger.info(f"Bot started with balance: {self.balance} USD in {self.trade_mode} mode")
        while self.running:
            try:
                for pair in self.pairs:
                    for tf in self.timeframes:
                        trade_signal = random.choice([True, False])
                        if trade_signal:
                            self.logger.info(f"Trade signal detected for {pair} @ {tf}")
                            await self.execute_trade(pair)
                await asyncio.sleep(5)
            except Exception as e:
                self.logger.error(f"Error in trading loop: {e}")
        self.logger.info("Bot stopped.")

    async def execute_trade(self, pair):
        if self.trade_mode == 'paper':
            trade_amount = 1.0
            if self.balance >= trade_amount:
                self.balance -= trade_amount
                self.logger.info(f"PAPER TRADE executed on {pair} for {trade_amount} USD. Remaining balance: {self.balance}")
            else:
                self.logger.warning("Insufficient balance for paper trade.")
        else:
            try:
                if self.exchange is None:
                    self.logger.warning("Live trading selected but exchange not configured!")
                    return
                order = await asyncio.get_event_loop().run_in_executor(None, self.exchange.create_market_buy_order, pair, 0.001)
                self.logger.info(f"LIVE TRADE executed on {pair}: {order}")
            except Exception as e:
                self.logger.error(f"Failed live trade on {pair}: {e}")

    def stop(self):
        self.running = False
        self.logger.info("Stop signal received to stop bot.")
