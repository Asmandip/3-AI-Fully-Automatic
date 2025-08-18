import os
import motor.motor_asyncio
from src.utils.logger import get_logger
from pymongo.errors import PyMongoError

logger = get_logger("MongoDB")


class MongoDB:
    def __init__(self):
        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
        self.db = self.client["trading_bot_db"]
        logger.info(f"Connected to MongoDB at {mongo_uri}")

    async def insert_trade(self, trade_data: dict):
        """Insert a trade into the trades collection"""
        try:
            logger.debug(f"Inserting trade: {trade_data}")
            result = await self.db.trades.insert_one(trade_data)
            logger.info(f"Inserted trade with id {result.inserted_id}")
            return result
        except PyMongoError as e:
            logger.error(f"Mongo insert_trade error: {e}")
            return None

    async def get_trades(self, filter_query: dict = None, limit: int = 100):
        """Fetch recent trades, sorted by timestamp desc"""
        try:
            filter_query = filter_query or {}
            logger.debug(f"Fetching trades with filter: {filter_query}")
            cursor = (
                self.db.trades.find(filter_query)
                .sort("timestamp", -1)
                .limit(limit)
            )
            result = await cursor.to_list(length=limit)
            logger.debug(f"Fetched {len(result)} trades")
            return result
        except PyMongoError as e:
            logger.error(f"Mongo get_trades error: {e}")
            return []

    async def get_settings(self):
        """Fetch the latest settings (only one settings document exists)"""
        try:
            logger.debug("Fetching settings")
            result = await self.db.settings.find_one({})
            logger.debug(f"Settings fetched: {result}")
            return result or {}
        except PyMongoError as e:
            logger.error(f"Mongo get_settings error: {e}")
            return {}

    async def save_settings(self, settings_dict: dict):
        """Save/replace settings document"""
        try:
            logger.debug(f"Saving settings: {settings_dict}")
            result = await self.db.settings.replace_one(
                {}, settings_dict, upsert=True
            )
            logger.info("Settings saved")
            return result
        except PyMongoError as e:
            logger.error(f"Mongo save_settings error: {e}")
            return None