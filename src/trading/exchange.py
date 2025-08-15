# src/trading/exchange.py
import ccxt.async_support as ccxt
import asyncio

class ResilientExchangeClient:
    def __init__(self):
        self.exchange = ccxt.bitget({
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })

    async def fetch_ticker(self, symbol):
        try:
            return await self.exchange.fetch_ticker(symbol)
        except Exception as e:
            # Log or fallback
            raise e
