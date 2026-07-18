from flask import current_app
from datetime import datetime

class MarketRecord:
    def __init__(self, data=None):
        self.id = str(data.get("_id", "")) if data else ""
        self.user_id = data.get("user_id", "") if data else ""
        self.crop = data.get("crop", "") if data else ""
        self.market = data.get("market", "") if data else ""
        self.price = data.get("price", 0) if data else 0
        self.unit = data.get("unit", "Quintal") if data else "Quintal"
        self.trend = data.get("trend", "stable") if data else "stable"
        self.market_data = data.get("market_data", {}) if data else {}
        self.created_at = data.get("created_at", datetime.utcnow()) if data else datetime.utcnow()

    @staticmethod
    def get_collection():
        return current_app.config["MONGO"]["market_history"]

    @staticmethod
    def find_by_user(user_id):
        data = MarketRecord.get_collection().find({"user_id": user_id}).sort("created_at", -1)
        return [MarketRecord(d) for d in data]

    @staticmethod
    def find_by_id(rid):
        from bson.objectid import ObjectId
        data = MarketRecord.get_collection().find_one({"_id": ObjectId(rid)})
        return MarketRecord(data) if data else None

    @staticmethod
    def search_by_user(user_id, query=""):
        import re
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        data = MarketRecord.get_collection().find({
            "user_id": user_id,
            "$or": [{"crop": pattern}, {"market": pattern}]
        }).sort("created_at", -1)
        return [MarketRecord(d) for d in data]

    def save(self):
        data = {
            "user_id": self.user_id,
            "crop": self.crop,
            "market": self.market,
            "price": self.price,
            "unit": self.unit,
            "trend": self.trend,
            "market_data": self.market_data,
            "created_at": self.created_at,
        }
        result = MarketRecord.get_collection().insert_one(data)
        return str(result.inserted_id)

    def delete(self):
        from bson.objectid import ObjectId
        MarketRecord.get_collection().delete_one({"_id": ObjectId(self.id)})

    def to_dict(self):
        created = self.created_at
        if hasattr(created, "isoformat"):
            created = created.isoformat()
        else:
            created = str(created)
        return {
            "id": self.id,
            "user_id": self.user_id,
            "crop": self.crop,
            "market": self.market,
            "price": self.price,
            "unit": self.unit,
            "trend": self.trend,
            "market_data": self.market_data,
            "created_at": created,
        }


class MarketFavorite:
    def __init__(self, data=None):
        self.id = str(data.get("_id", "")) if data else ""
        self.user_id = data.get("user_id", "") if data else ""
        self.crop = data.get("crop", "") if data else ""
        self.created_at = data.get("created_at", datetime.utcnow()) if data else datetime.utcnow()

    @staticmethod
    def get_collection():
        return current_app.config["MONGO"]["market_favorites"]

    @staticmethod
    def find_by_user(user_id):
        data = MarketFavorite.get_collection().find({"user_id": user_id}).sort("created_at", -1)
        return [MarketFavorite(d) for d in data]

    @staticmethod
    def find_by_user_and_crop(user_id, crop):
        return MarketFavorite.get_collection().find_one({
            "user_id": user_id, "crop": crop
        })

    @staticmethod
    def find_by_id(fid):
        from bson.objectid import ObjectId
        data = MarketFavorite.get_collection().find_one({"_id": ObjectId(fid)})
        return MarketFavorite(data) if data else None

    def save(self):
        data = {
            "user_id": self.user_id,
            "crop": self.crop,
            "created_at": self.created_at,
        }
        result = MarketFavorite.get_collection().insert_one(data)
        return str(result.inserted_id)

    def delete(self):
        from bson.objectid import ObjectId
        MarketFavorite.get_collection().delete_one({"_id": ObjectId(self.id)})

    def to_dict(self):
        created = self.created_at
        if hasattr(created, "isoformat"):
            created = created.isoformat()
        else:
            created = str(created)
        return {
            "id": self.id,
            "user_id": self.user_id,
            "crop": self.crop,
            "created_at": created,
        }
