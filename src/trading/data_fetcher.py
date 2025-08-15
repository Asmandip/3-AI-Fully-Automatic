# src/trading/data_fetcher.py
import ccxt.async_support as ccxt

class AsyncDataFetcher:
    def __init__(self):
        self.exchange = ccxt.bitget({
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })

    async def fetch_ticker(self, symbol):
        return await self.exchange.fetch_ticker(symbol)

    async def fetch_historical_data(self, symbol, timeframe='1m', limit=100):
        return await self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
