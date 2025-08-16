# src/database/mongo.py

import os
import motor.motor_asyncio
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("MongoDB")

class MongoDB:
    def __init__(self):
        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
        self.db = self.client["trading_bot_db"]
        logger.debug(f"Connected to MongoDB at {mongo_uri}")

    async def insert_trade(self, trade_data):
        logger.debug(f"Inserting trade: {trade_data}")
        result = await self.db.trades.insert_one(trade_data)
        logger.debug(f"Inserted trade with id {result.inserted_id}")
        return result

    async def get_trades(self, filter_query={}):
        logger.debug(f"Fetching trades with filter: {filter_query}")
        cursor = self.db.trades.find(filter_query)
        result = await cursor.to_list(length=100)
        logger.debug(f"Fetched {len(result)} trades")
        return result

    async def get_settings(self):
        logger.debug("Fetching settings")
        result = await self.db.settings.find_one({})
        logger.debug(f"Settings fetched: {result}")
        return result

    async def save_settings(self, settings_dict):
        logger.debug(f"Saving settings: {settings_dict}")
        result = await self.db.settings.replace_one({}, settings_dict, upsert=True)
        logger.debug("Settings saved")
        return result
