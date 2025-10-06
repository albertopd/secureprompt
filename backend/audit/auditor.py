#from backend.database.users_db import get_collection
from datetime import datetime, timezone

class Auditor:
    def __init__(self):
        self.col = None #get_collection("audits")

    def log(self, corp_key: str, action: str, details: dict):
        record = {
            "timestamp": datetime.now(timezone.utc),
            "corp_key": corp_key,
            "action": action,
            "details": details,

        }
        #self.col.insert_one(record)
        return str(record.get("_id"))
