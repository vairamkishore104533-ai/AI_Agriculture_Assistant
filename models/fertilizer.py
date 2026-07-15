from flask import current_app
from datetime import datetime

class Fertilizer:
    def __init__(self, data=None):
        self.id = str(data.get("_id", "")) if data else ""
        self.user_id = data.get("user_id", "") if data else ""
        self.season = data.get("season", "") if data else ""
        self.crop = data.get("crop", "") if data else ""
        self.growth_stage = data.get("growth_stage", "") if data else ""
        self.irrigation_method = data.get("irrigation_method", "") if data else ""
        self.recommendation = data.get("recommendation", "") if data else ""
        self.language = data.get("language", "en") if data else "en"
        self.district = data.get("district", "") if data else ""
        self.created_at = data.get("created_at", datetime.utcnow()) if data else datetime.utcnow()

    @staticmethod
    def get_collection():
        return current_app.config["MONGO"]["fertilizer"]

    @staticmethod
    def find_by_user(user_id):
        data = Fertilizer.get_collection().find({"user_id": user_id}).sort("created_at", -1)
        return [Fertilizer(d) for d in data]

    @staticmethod
    def find_by_id(rec_id):
        from bson.objectid import ObjectId
        data = Fertilizer.get_collection().find_one({"_id": ObjectId(rec_id)})
        return Fertilizer(data) if data else None

    @staticmethod
    def find_by_season(user_id, season):
        data = Fertilizer.get_collection().find({"user_id": user_id, "season": season}).sort("created_at", -1)
        return [Fertilizer(d) for d in data]

    @staticmethod
    def search_by_user(user_id, query=""):
        import re
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        data = Fertilizer.get_collection().find({
            "user_id": user_id,
            "$or": [{"crop": pattern}, {"season": pattern}]
        }).sort("created_at", -1)
        return [Fertilizer(d) for d in data]

    @staticmethod
    def get_stats(user_id):
        total = Fertilizer.get_collection().count_documents({"user_id": user_id})
        return {
            "total": total,
        }

    def save(self):
        created = self.created_at
        if not isinstance(created, datetime):
            created = datetime.utcnow()
        data = {
            "user_id": self.user_id,
            "season": self.season,
            "crop": self.crop,
            "growth_stage": self.growth_stage,
            "irrigation_method": self.irrigation_method,
            "recommendation": self.recommendation,
            "language": self.language,
            "district": self.district,
            "created_at": created,
        }
        result = Fertilizer.get_collection().insert_one(data)
        return str(result.inserted_id)

    def delete(self):
        from bson.objectid import ObjectId
        Fertilizer.get_collection().delete_one({"_id": ObjectId(self.id)})

    def to_dict(self):
        created = self.created_at
        if hasattr(created, "isoformat"):
            created = created.isoformat()
        else:
            created = str(created)
        return {
            "id": self.id,
            "user_id": self.user_id,
            "season": self.season,
            "crop": self.crop,
            "growth_stage": self.growth_stage,
            "irrigation_method": self.irrigation_method,
            "recommendation": self.recommendation,
            "language": self.language,
            "district": self.district,
            "created_at": created,
        }
