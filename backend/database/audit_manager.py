from datetime import datetime, timezone
from pymongo import MongoClient
from bson import ObjectId
from core.config import settings
from dataclasses import dataclass


@dataclass
class AuditLog:
    corp_key: str
    category: str
    action: str
    details: dict
    device_info: str
    browser_info: str
    client_ip: str
    user_agent: str
    timestamp: datetime = datetime.now(timezone.utc)


class AuditManager:
    def __init__(self, client: MongoClient):
        self.client = client
        self.db = client[settings.MONGO_DB]
        self.audits = self.db[settings.MONGO_AUDITS_COLLECTION]

    def log(self, record: AuditLog):
        res = self.audits.insert_one(record.__dict__)
        return str(res.inserted_id)

    def get_log(self, audit_id: str) -> AuditLog | None:
        return self.audits.find_one({"_id": ObjectId(audit_id)})
