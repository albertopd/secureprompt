from database.mongo import get_collection
import time

class Auditor:
    def __init__(self):
        self.col = get_collection("audits")

    def log(self, user: str, action: str, details: dict):
        record = {
            "user": user,
            "action": action,
            "details": details,
            "timestamp": time.time()
        }
        self.col.insert_one(record)
        return str(record.get("_id"))
