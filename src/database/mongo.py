# src/database/mongo.py
import os
import motor.motor_asyncio

class MongoDB:
    def __init__(self):
        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
        self.db = self.client["trading_bot_db"]

    async def insert_trade(self, trade_data):
        result = await self.db.trades.insert_one(trade_data)
        return result

    async def get_trades(self, filter_query={}):
        cursor = self.db.trades.find(filter_query)
        return await cursor.to_list(length=100)
