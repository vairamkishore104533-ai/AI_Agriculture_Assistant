from flask import current_app
from datetime import datetime

class Irrigation:
    def __init__(self, data=None):
        self.id = str(data.get("_id", "")) if data else ""
        self.user_id = data.get("user_id", "") if data else ""
        self.crop = data.get("crop", "") if data else ""
        self.district = data.get("district", "") if data else ""
        self.season = data.get("season", "") if data else ""
        self.irrigation_method = data.get("irrigation_method", "") if data else ""
        self.recommendation = data.get("recommendation", "") if data else ""
        self.language = data.get("language", "en") if data else "en"
        self.created_at = data.get("created_at", datetime.utcnow()) if data else datetime.utcnow()

    @staticmethod
    def get_collection():
        return current_app.config["MONGO"]["irrigation"]

    @staticmethod
    def find_by_user(user_id):
        data = Irrigation.get_collection().find({"user_id": user_id}).sort("created_at", -1)
        return [Irrigation(d) for d in data]

    @staticmethod
    def find_by_id(rec_id):
        from bson.objectid import ObjectId
        data = Irrigation.get_collection().find_one({"_id": ObjectId(rec_id)})
        return Irrigation(data) if data else None

    @staticmethod
    def search_by_user(user_id, query=""):
        import re
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        data = Irrigation.get_collection().find({
            "user_id": user_id,
            "$or": [{"crop": pattern}, {"district": pattern}, {"season": pattern}]
        }).sort("created_at", -1)
        return [Irrigation(d) for d in data]

    @staticmethod
    def get_stats(user_id):
        total = Irrigation.get_collection().count_documents({"user_id": user_id})
        return {"total": total}

    def save(self):
        created = self.created_at
        if not isinstance(created, datetime):
            created = datetime.utcnow()
        data = {
            "user_id": self.user_id,
            "crop": self.crop,
            "district": self.district,
            "season": self.season,
            "irrigation_method": self.irrigation_method,
            "recommendation": self.recommendation,
            "language": self.language,
            "created_at": created,
        }
        result = Irrigation.get_collection().insert_one(data)
        return str(result.inserted_id)

    def delete(self):
        from bson.objectid import ObjectId
        Irrigation.get_collection().delete_one({"_id": ObjectId(self.id)})

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
            "district": self.district,
            "season": self.season,
            "irrigation_method": self.irrigation_method,
            "recommendation": self.recommendation,
            "language": self.language,
            "created_at": created,
        }
