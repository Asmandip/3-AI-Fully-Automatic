# src/trading/exchange.py
import ccxt.async_support as ccxt
from tenacity import retry, stop_after_attempt, wait_exponential
from src.utils.logger import get_logger

logger = get_logger("ExchangeClient")

class ResilientExchangeClient:
    def __init__(self, api_key=None, api_secret=None):
        self.exchange = ccxt.bitget({
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'},
            'apiKey': api_key,
            'secret': api_secret,
        })

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def fetch_ticker(self, symbol):
        try:
            logger.debug(f"Fetching ticker for {symbol}")
            return await self.exchange.fetch_ticker(symbol)
        except Exception as e:
            logger.error(f"Error fetching ticker: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def create_market_order(self, symbol, side, amount):
        try:
            logger.info(f"Creating {side} market order for {amount} of {symbol}")
            return await self.exchange.create_market_order(symbol, side, amount)
        except Exception as e:
            logger.error(f"Order failed: {e}")
            raise