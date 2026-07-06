import os

DB_TYPE = os.environ.get("DB_TYPE") or "mock"

if DB_TYPE == "mongodb":
    from bson.objectid import ObjectId
else:
    import uuid
    class ObjectId:
        def __init__(self, oid=None):
            self.oid = oid if oid else str(uuid.uuid4()).replace("-", "")[:24]
        def __str__(self):
            return self.oid
        def __repr__(self):
            return f"ObjectId('{self.oid}')"
