from datetime import datetime, timezone
from pymongo import MongoClient
from core.config import settings


class AuditManager:
    def __init__(self, client: MongoClient):
        self.client = client
        self.db = client[settings.MONGO_DB]
        self.audits = self.db[settings.MONGO_AUDITS_COLLECTION]

    def log(self, corp_key: str, action: str, details: dict):
        record = {
            "timestamp": datetime.now(timezone.utc),
            "corp_key": corp_key,
            "action": action,
            "details": details,
        }
        res = self.audits.insert_one(record)
        return str(res.inserted_id)
