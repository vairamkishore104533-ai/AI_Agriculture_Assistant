from flask import current_app
from datetime import datetime

class Crop:
    def __init__(self, data=None):
        self.id = str(data.get("_id", "")) if data else ""
        self.user_id = data.get("user_id", "") if data else ""
        self.crop_name = data.get("crop_name", "") if data else ""
        self.district = data.get("district", "") if data else ""
        self.village = data.get("village", "") if data else ""
        self.soil_type = data.get("soil_type", "") if data else ""
        self.land_size = data.get("land_size", 0) if data else 0
        self.planting_date = data.get("planting_date", "") if data else ""
        self.harvest_date = data.get("harvest_date", "") if data else ""
        self.status = data.get("status", "active") if data else "active"
        self.created_at = data.get("created_at", datetime.utcnow()) if data else datetime.utcnow()

    @staticmethod
    def get_collection():
        return current_app.config["MONGO"]["crops"]

    @staticmethod
    def find_by_user(user_id):
        crops_data = Crop.get_collection().find({"user_id": user_id}).sort("created_at", -1)
        return [Crop(c) for c in crops_data]

    @staticmethod
    def find_by_id(crop_id):
        from bson.objectid import ObjectId
        data = Crop.get_collection().find_one({"_id": ObjectId(crop_id)})
        return Crop(data) if data else None

    @staticmethod
    def count_by_user(user_id):
        return Crop.get_collection().count_documents({"user_id": user_id})

    @staticmethod
    def count_all():
        return Crop.get_collection().count_documents({})

    def save(self):
        data = {
            "user_id": self.user_id,
            "crop_name": self.crop_name,
            "district": self.district,
            "village": self.village,
            "soil_type": self.soil_type,
            "land_size": self.land_size,
            "planting_date": self.planting_date,
            "harvest_date": self.harvest_date,
            "status": self.status,
            "created_at": self.created_at,
        }
        result = Crop.get_collection().insert_one(data)
        return str(result.inserted_id)

    def update(self, data):
        from bson.objectid import ObjectId
        Crop.get_collection().update_one(
            {"_id": ObjectId(self.id)},
            {"$set": data}
        )

    def delete(self):
        from bson.objectid import ObjectId
        Crop.get_collection().delete_one({"_id": ObjectId(self.id)})

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "crop_name": self.crop_name,
            "district": self.district,
            "village": self.village,
            "soil_type": self.soil_type,
            "land_size": self.land_size,
            "planting_date": self.planting_date,
            "harvest_date": self.harvest_date,
            "status": self.status,
            "created_at": self.created_at,
        }
