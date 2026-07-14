from flask import current_app
from datetime import datetime

class Diagnosis:
    def __init__(self, data=None):
        self.id = str(data.get("_id", "")) if data else ""
        self.user_id = data.get("user_id", "") if data else ""
        self.crop = data.get("crop", "") if data else ""
        self.symptoms = data.get("symptoms", []) if data else []
        self.disease = data.get("disease", "") if data else ""
        self.severity = data.get("severity", "") if data else ""
        self.confidence = data.get("confidence", "") if data else ""
        self.description = data.get("description", "") if data else ""
        self.causes = data.get("causes", "") if data else ""
        self.spread = data.get("spread", "") if data else ""
        self.treatment_immediate = data.get("treatment_immediate", "") if data else ""
        self.treatment_organic = data.get("treatment_organic", "") if data else ""
        self.treatment_chemical = data.get("treatment_chemical", "") if data else ""
        self.prevention = data.get("prevention", "") if data else ""
        self.emergency = data.get("emergency", "") if data else ""
        self.related_diseases = data.get("related_diseases", "") if data else ""
        self.recovery_time = data.get("recovery_time", "") if data else ""
        self.success_rate = data.get("success_rate", "") if data else ""
        self.district = data.get("district", "") if data else ""
        self.diagnosis = data.get("diagnosis", "") if data else ""
        self.created_at = data.get("created_at", datetime.utcnow()) if data else datetime.utcnow()

    @staticmethod
    def get_collection():
        return current_app.config["MONGO"]["diagnoses"]

    @staticmethod
    def find_by_user(user_id):
        data = Diagnosis.get_collection().find({"user_id": user_id}).sort("created_at", -1)
        return [Diagnosis(d) for d in data]

    @staticmethod
    def find_by_id(diag_id):
        from bson.objectid import ObjectId
        data = Diagnosis.get_collection().find_one({"_id": ObjectId(diag_id)})
        return Diagnosis(data) if data else None

    @staticmethod
    def search_by_user(user_id, query=""):
        import re
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        data = Diagnosis.get_collection().find({
            "user_id": user_id,
            "$or": [{"crop": pattern}, {"disease": pattern}]
        }).sort("created_at", -1)
        return [Diagnosis(d) for d in data]

    @staticmethod
    def get_stats(user_id):
        total = Diagnosis.get_collection().count_documents({"user_id": user_id})
        critical = Diagnosis.get_collection().count_documents({"user_id": user_id, "severity": "Critical"})
        high = Diagnosis.get_collection().count_documents({"user_id": user_id, "severity": "High"})
        healthy = Diagnosis.get_collection().count_documents({"user_id": user_id, "severity": "Low"})
        return {
            "total": total,
            "critical": critical,
            "high": high,
            "healthy": healthy,
            "diseases_detected": total - healthy,
        }

    def save(self):
        data = {
            "user_id": self.user_id,
            "crop": self.crop,
            "symptoms": self.symptoms,
            "disease": self.disease,
            "severity": self.severity,
            "confidence": self.confidence,
            "description": self.description,
            "causes": self.causes,
            "spread": self.spread,
            "treatment_immediate": self.treatment_immediate,
            "treatment_organic": self.treatment_organic,
            "treatment_chemical": self.treatment_chemical,
            "prevention": self.prevention,
            "emergency": self.emergency,
            "related_diseases": self.related_diseases,
            "recovery_time": self.recovery_time,
            "success_rate": self.success_rate,
            "district": self.district,
            "diagnosis": self.diagnosis,
            "created_at": self.created_at,
        }
        result = Diagnosis.get_collection().insert_one(data)
        return str(result.inserted_id)

    def delete(self):
        from bson.objectid import ObjectId
        Diagnosis.get_collection().delete_one({"_id": ObjectId(self.id)})

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "crop": self.crop,
            "symptoms": self.symptoms,
            "disease": self.disease,
            "severity": self.severity,
            "confidence": self.confidence,
            "description": self.description,
            "causes": self.causes,
            "spread": self.spread,
            "treatment_immediate": self.treatment_immediate,
            "treatment_organic": self.treatment_organic,
            "treatment_chemical": self.treatment_chemical,
            "prevention": self.prevention,
            "emergency": self.emergency,
            "related_diseases": self.related_diseases,
            "recovery_time": self.recovery_time,
            "success_rate": self.success_rate,
            "district": self.district,
            "diagnosis": self.diagnosis,
            "created_at": self.created_at,
        }
