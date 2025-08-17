# src/trading/bot.py
import asyncio
import random
import ccxt
from src.utils.logger import get_logger
from src.trading.data_fetcher import AsyncDataFetcher
from src.trading.exchange import ResilientExchangeClient
from src.trading.risk_manager import RiskManager
from src.trading.strategies import STRATEGY_MAP
from src.database.mongo import MongoDB

logger = get_logger("TradingBot")

class TradingBot:
    def __init__(self, db: MongoDB):
        self.running = False
        self.db = db
        self.pairs = []
        self.timeframes = []
        self.strategy_name = 'Scalping'
        self.strategy = None
        self.strategy_mode = 'auto'
        self.trade_mode = 'paper'
        self.balance = 1000.0
        self.data_fetcher = AsyncDataFetcher()
        self.exchange = None
        self.risk_manager = RiskManager()
        self.api_key = None
        self.api_secret = None
        self.trade_size = 0.01  # Default trade size (1% of balance)
        self.min_balance = 100.0

    async def update_settings(self):
        settings = await self.db.get_settings()
        if settings:
            self.pairs = settings.get("pairs", [])
            self.timeframes = settings.get("timeframes", [])
            self.strategy_name = settings.get("strategy", "Scalping")
            self.strategy_mode = settings.get("strategy_mode", "auto")
            self.trade_mode = settings.get("trade_mode", "paper")
            self.api_key = settings.get("api_key")
            self.api_secret = settings.get("api_secret")
            self.trade_size = settings.get("trade_size", 0.01)
            self.min_balance = settings.get("min_balance", 100.0)
            
            # Initialize strategy
            strategy_class = STRATEGY_MAP.get(self.strategy_name)
            if strategy_class:
                self.strategy = strategy_class()
            else:
                logger.error(f"Invalid strategy: {self.strategy_name}")
                self.strategy = STRATEGY_MAP["Scalping"]()
            
            # Initialize exchange for live trading
            if self.trade_mode == 'live' and not self.exchange and self.api_key and self.api_secret:
                self.exchange = ResilientExchangeClient(self.api_key, self.api_secret)

    async def run(self):
        self.running = True
        logger.info(f"Bot started with balance: {self.balance} USD in {self.trade_mode} mode")
        
        while self.running:
            try:
                # Update settings from database
                await self.update_settings()
                
                if not self.pairs or not self.timeframes:
                    await asyncio.sleep(5)
                    continue
                
                # Process each pair and timeframe
                for pair in self.pairs:
                    for timeframe in self.timeframes:
                        # Fetch historical data
                        try:
                            hist_data = await self.data_fetcher.fetch_historical_data(
                                pair, timeframe=timeframe, limit=50
                            )
                            
                            if not hist_data or len(hist_data) < 10:
                                continue
                            
                            # Get signal from strategy
                            signal = self.strategy.analyze(hist_data)
                            
                            if signal != 0:
                                logger.info(f"Signal detected for {pair} @ {timeframe}: "
                                            f"{'BUY' if signal > 0 else 'SELL'}")
                                
                                # Execute trade
                                await self.execute_trade(pair, signal)
                            
                        except Exception as e:
                            logger.error(f"Error processing {pair}@{timeframe}: {e}")
                
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(30)
        
        logger.info("Bot stopped.")

    async def execute_trade(self, pair, signal):
        # Calculate trade size based on percentage of balance
        amount = self.balance * self.trade_size
        
        # Risk management check
        volatility = self.risk_manager.calculate_volatility(
            await self.data_fetcher.fetch_historical_data(pair, '5m', 100)
        )
        
        if not self.risk_manager.should_accept_trade(amount, volatility, self.balance):
            logger.warning("Trade rejected by risk manager")
            return
        
        side = "buy" if signal > 0 else "sell"
        
        if self.trade_mode == 'paper':
            # Paper trading logic
            if self.balance >= amount:
                self.balance -= amount
                # Simulate profit/loss
                profit = amount * (random.uniform(-0.01, 0.02))
                self.balance += amount + profit
                
                trade_data = {
                    "pair": pair,
                    "side": side,
                    "amount": amount,
                    "price": "N/A",
                    "profit": profit,
                    "balance": self.balance,
                    "mode": "paper",
                    "timestamp": datetime.datetime.utcnow()
                }
                await self.db.insert_trade(trade_data)
                logger.info(f"PAPER TRADE: {side} {amount} USD of {pair}. "
                            f"Profit: ${profit:.2f}, Balance: ${self.balance:.2f}")
            else:
                logger.warning("Insufficient balance for paper trade")
        else:
            # Live trading
            try:
                if self.exchange is None:
                    logger.error("Exchange not configured for live trading!")
                    return
                
                # Fetch current price for accurate sizing
                ticker = await self.data_fetcher.fetch_ticker(pair)
                current_price = ticker['last']
                
                # Calculate amount in crypto terms
                crypto_amount = amount / current_price
                
                # Execute order
                order = await self.exchange.create_market_order(pair, side, crypto_amount)
                
                trade_data = {
                    "pair": pair,
                    "side": side,
                    "amount": amount,
                    "price": current_price,
                    "order_id": order['id'],
                    "mode": "live",
                    "timestamp": datetime.datetime.utcnow()
                }
                await self.db.insert_trade(trade_data)
                logger.info(f"LIVE TRADE executed: {order}")
            except Exception as e:
                logger.error(f"Live trade failed: {e}")

    def stop(self):
        self.running = False
        logger.info("Stop signal received")