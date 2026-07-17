from flask import current_app
from datetime import datetime

class WeatherHistory:
    def __init__(self, data=None):
        self.id = str(data.get("_id", "")) if data else ""
        self.user_id = data.get("user_id", "") if data else ""
        self.district = data.get("district", "") if data else ""
        self.town = data.get("town", "") if data else ""
        self.weather_data = data.get("weather_data", {}) if data else {}
        self.created_at = data.get("created_at", datetime.utcnow()) if data else datetime.utcnow()

    @staticmethod
    def get_collection():
        return current_app.config["MONGO"]["weather_history"]

    @staticmethod
    def find_by_user(user_id):
        data = WeatherHistory.get_collection().find({"user_id": user_id}).sort("created_at", -1)
        return [WeatherHistory(d) for d in data]

    @staticmethod
    def find_by_id(rid):
        from bson.objectid import ObjectId
        data = WeatherHistory.get_collection().find_one({"_id": ObjectId(rid)})
        return WeatherHistory(data) if data else None

    @staticmethod
    def search_by_user(user_id, query=""):
        import re
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        data = WeatherHistory.get_collection().find({
            "user_id": user_id,
            "$or": [{"district": pattern}, {"town": pattern}]
        }).sort("created_at", -1)
        return [WeatherHistory(d) for d in data]

    def save(self):
        data = {
            "user_id": self.user_id,
            "district": self.district,
            "town": self.town,
            "weather_data": self.weather_data,
            "created_at": self.created_at,
        }
        result = WeatherHistory.get_collection().insert_one(data)
        return str(result.inserted_id)

    def delete(self):
        from bson.objectid import ObjectId
        WeatherHistory.get_collection().delete_one({"_id": ObjectId(self.id)})

    def to_dict(self):
        created = self.created_at
        if hasattr(created, "isoformat"):
            created = created.isoformat()
        else:
            created = str(created)
        return {
            "id": self.id,
            "user_id": self.user_id,
            "district": self.district,
            "town": self.town,
            "weather_data": self.weather_data,
            "created_at": created,
        }


class WeatherFavorite:
    def __init__(self, data=None):
        self.id = str(data.get("_id", "")) if data else ""
        self.user_id = data.get("user_id", "") if data else ""
        self.district = data.get("district", "") if data else ""
        self.town = data.get("town", "") if data else ""
        self.created_at = data.get("created_at", datetime.utcnow()) if data else datetime.utcnow()

    @staticmethod
    def get_collection():
        return current_app.config["MONGO"]["weather_favorites"]

    @staticmethod
    def find_by_user(user_id):
        data = WeatherFavorite.get_collection().find({"user_id": user_id}).sort("created_at", -1)
        return [WeatherFavorite(d) for d in data]

    @staticmethod
    def find_by_user_and_location(user_id, district, town):
        return WeatherFavorite.get_collection().find_one({
            "user_id": user_id, "district": district, "town": town
        })

    @staticmethod
    def find_by_id(fid):
        from bson.objectid import ObjectId
        data = WeatherFavorite.get_collection().find_one({"_id": ObjectId(fid)})
        return WeatherFavorite(data) if data else None

    def save(self):
        data = {
            "user_id": self.user_id,
            "district": self.district,
            "town": self.town,
            "created_at": self.created_at,
        }
        result = WeatherFavorite.get_collection().insert_one(data)
        return str(result.inserted_id)

    def delete(self):
        from bson.objectid import ObjectId
        WeatherFavorite.get_collection().delete_one({"_id": ObjectId(self.id)})

    def to_dict(self):
        created = self.created_at
        if hasattr(created, "isoformat"):
            created = created.isoformat()
        else:
            created = str(created)
        return {
            "id": self.id,
            "user_id": self.user_id,
            "district": self.district,
            "town": self.town,
            "created_at": created,
        }
