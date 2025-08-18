# src/trading/data_fetcher.py
import ccxt.async_support as ccxt
from src.utils.logger import get_logger
from tenacity import retry, stop_after_attempt, wait_exponential

logger = get_logger("DataFetcher")

class AsyncDataFetcher:
    def __init__(self):
        self.exchange = ccxt.bitget({
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def fetch_ticker(self, symbol):
        logger.debug(f"Fetching ticker for {symbol}")
        return await self.exchange.fetch_ticker(symbol)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def fetch_historical_data(self, symbol, timeframe='1m', limit=100):
        logger.debug(f"Fetching {limit} {timeframe} candles for {symbol}")
        return await self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    async def close(self):
        try:
            await self.exchange.close()
        except Exception:
            pass