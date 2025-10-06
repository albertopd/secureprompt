import os
from datetime import datetime, timezone
from pymongo import MongoClient


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB", "secureprompt")
MONGO_DB_AUDITS_COLLECTION = os.getenv("MONGO_DB_AUDITS_COLLECTION", "audits")


class AuditsDatabase:
    def __init__(self, uri: str = MONGO_URI, db_name: str = MONGO_DB_NAME):
        self.uri = uri
        self.db_name = db_name
        self.client = None
        self.db = None
        self.users = None

    def __enter__(self):
        self.client = MongoClient(self.uri)
        self.db = self.client[self.db_name]
        self.audits = self.db[MONGO_DB_AUDITS_COLLECTION]
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            self.client.close()

    def log(self, corp_key: str, action: str, details: dict):
        record = {
            "timestamp": datetime.now(timezone.utc),
            "corp_key": corp_key,
            "action": action,
            "details": details,

        }
        self.audits.insert_one(record)
        return str(record.get("_id"))