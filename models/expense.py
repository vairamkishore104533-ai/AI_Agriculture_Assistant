from flask import current_app
from datetime import datetime

class Expense:
    def __init__(self, data=None):
        self.id = str(data.get("_id", "")) if data else ""
        self.user_id = data.get("user_id", "") if data else ""
        self.type = data.get("type", "expense") if data else "expense"
        self.category = data.get("category", "") if data else ""
        self.amount = data.get("amount", 0) if data else 0
        self.description = data.get("description", "") if data else ""
        self.date = data.get("date", datetime.utcnow().strftime("%Y-%m-%d")) if data else datetime.utcnow().strftime("%Y-%m-%d")
        self.created_at = data.get("created_at", datetime.utcnow()) if data else datetime.utcnow()

    @staticmethod
    def get_collection():
        return current_app.config["MONGO"]["expenses"]

    @staticmethod
    def find_by_user(user_id):
        expenses_data = Expense.get_collection().find({"user_id": user_id}).sort("date", -1)
        return [Expense(e) for e in expenses_data]

    @staticmethod
    def find_by_id(expense_id):
        from bson.objectid import ObjectId
        data = Expense.get_collection().find_one({"_id": ObjectId(expense_id)})
        return Expense(data) if data else None

    def save(self):
        data = {
            "user_id": self.user_id,
            "type": self.type,
            "category": self.category,
            "amount": self.amount,
            "description": self.description,
            "date": self.date,
            "created_at": self.created_at,
        }
        result = Expense.get_collection().insert_one(data)
        return str(result.inserted_id)

    def delete(self):
        from bson.objectid import ObjectId
        Expense.get_collection().delete_one({"_id": ObjectId(self.id)})

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "category": self.category,
            "amount": self.amount,
            "description": self.description,
            "date": self.date,
            "created_at": self.created_at,
        }

    @staticmethod
    def get_summary(user_id):
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": "$type",
                "total": {"$sum": "$amount"},
                "count": {"$sum": 1}
            }}
        ]
        results = Expense.get_collection().aggregate(pipeline)
        summary = {"income": 0, "expense": 0}
        for r in results:
            summary[r["_id"]] = r["total"]
        return summary

    @staticmethod
    def get_category_breakdown(user_id):
        pipeline = [
            {"$match": {"user_id": user_id, "type": "expense"}},
            {"$group": {
                "_id": "$category",
                "total": {"$sum": "$amount"},
                "count": {"$sum": 1}
            }}
        ]
        return list(Expense.get_collection().aggregate(pipeline))

    @staticmethod
    def get_monthly_summary(user_id, year, month):
        month_str = f"{year}-{month:02d}"
        pipeline = [
            {"$match": {
                "user_id": user_id,
                "date": {"$regex": f"^{month_str}"}
            }},
            {"$group": {
                "_id": "$type",
                "total": {"$sum": "$amount"}
            }}
        ]
        return list(Expense.get_collection().aggregate(pipeline))
