from flask import current_app
from datetime import datetime

class ChatConversation:
    def __init__(self, data=None):
        self.id = str(data.get("_id", "")) if data else ""
        self.user_id = data.get("user_id", "") if data else ""
        self.title = data.get("title", "New Chat") if data else ""
        self.district = data.get("district", "") if data else ""
        self.messages = data.get("messages", []) if data else []
        self.created_at = data.get("created_at", datetime.utcnow()) if data else datetime.utcnow()
        self.updated_at = data.get("updated_at", datetime.utcnow()) if data else datetime.utcnow()

    @staticmethod
    def get_collection():
        return current_app.config["MONGO"]["chat_conversations"]

    @staticmethod
    def find_by_id(conv_id):
        from bson.objectid import ObjectId
        data = ChatConversation.get_collection().find_one({"_id": ObjectId(conv_id)})
        return ChatConversation(data) if data else None

    @staticmethod
    def find_by_user(user_id, limit=20):
        result = ChatConversation.get_collection().find({"user_id": user_id})
        if isinstance(result, list):
            result.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
            result = result[:limit]
        else:
            result = result.sort("updated_at", -1).limit(limit)
        return [ChatConversation(d) for d in result]

    def save(self):
        data = {
            "user_id": self.user_id,
            "title": self.title,
            "district": self.district,
            "messages": self.messages,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        result = ChatConversation.get_collection().insert_one(data)
        self.id = str(result.inserted_id)
        return self.id

    def update(self, data):
        from bson.objectid import ObjectId
        ChatConversation.get_collection().update_one(
            {"_id": ObjectId(self.id)},
            {"$set": data}
        )

    def add_message(self, role, content):
        msg = {"role": role, "content": content, "timestamp": datetime.utcnow().isoformat()}
        self.messages.append(msg)
        self.updated_at = datetime.utcnow()
        from bson.objectid import ObjectId
        ChatConversation.get_collection().update_one(
            {"_id": ObjectId(self.id)},
            {"$push": {"messages": msg}, "$set": {"updated_at": self.updated_at}}
        )

    def generate_title(self):
        if self.messages:
            first_user_msg = next((m["content"] for m in self.messages if m["role"] == "user"), None)
            if first_user_msg:
                self.title = first_user_msg[:60] + ("..." if len(first_user_msg) > 60 else "")
        self.title = self.title.strip() or "New Chat"
        from bson.objectid import ObjectId
        ChatConversation.get_collection().update_one(
            {"_id": ObjectId(self.id)},
            {"$set": {"title": self.title}}
        )

    @staticmethod
    def delete_by_id(conv_id):
        from bson.objectid import ObjectId
        ChatConversation.get_collection().delete_one({"_id": ObjectId(conv_id)})

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "district": self.district,
            "messages": [
                {"role": m["role"], "content": m["content"]}
                for m in self.messages
            ],
            "created_at": self.created_at.isoformat() if hasattr(self.created_at, "isoformat") else str(self.created_at),
            "updated_at": self.updated_at.isoformat() if hasattr(self.updated_at, "isoformat") else str(self.updated_at),
        }
