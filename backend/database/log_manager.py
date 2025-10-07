from pymongo import MongoClient
from bson import ObjectId
from core.config import settings
from database.log_record import LogRecord, LogRecordAction, LogRecordCategory


class LogManager:
    def __init__(self, client: MongoClient):
        self.client = client
        self.db = client[settings.MONGO_DB]
        self.logs = self.db[settings.MONGO_LOGS_COLLECTION]

    def add_log(self, record: LogRecord):
        # Convert the record to a dictionary and handle enum serialization
        record_dict = record.__dict__.copy()

        # Convert enum values to strings for MongoDB storage
        if isinstance(record_dict["category"], LogRecordCategory):
            record_dict["category"] = record_dict["category"].value
        if isinstance(record_dict["action"], LogRecordAction):
            record_dict["action"] = record_dict["action"].value

        res = self.logs.insert_one(record_dict)
        return str(res.inserted_id)

    def get_log(self, log_id: str) -> LogRecord | None:
        doc = self.logs.find_one({"_id": ObjectId(log_id)})
        if not doc:
            return None

        # Convert string values back to enums and reconstruct LogRecord
        return LogRecord(
            corp_key=doc["corp_key"],
            category=LogRecordCategory(doc["category"]), 
            action=LogRecordAction(doc["action"]),
            details=doc["details"],
            device_info=doc["device_info"],
            browser_info=doc["browser_info"],
            client_ip=doc["client_ip"],
            user_agent=doc["user_agent"],
            timestamp=doc["timestamp"]
        )
