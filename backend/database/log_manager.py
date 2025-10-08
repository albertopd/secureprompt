from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
from core.config import settings
from database.log_record import LogRecord, LogRecordAction, LogRecordCategory


# TODO: Use append-only, tamper-proof logs (integrity must be ensured)
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
            timestamp=doc["timestamp"],
        )

    def list_logs(self, page: int = 1, page_size: int = 20) -> dict:
        """List all logs with pagination (no filtering)"""
        skip = (page - 1) * page_size

        # Get total count for pagination info
        total_count = self.logs.count_documents({})

        # Get paginated results, sorted by timestamp descending (newest first)
        cursor = self.logs.find({}).sort("timestamp", -1).skip(skip).limit(page_size)

        # Convert documents to LogRecord objects
        logs = []
        for doc in cursor:
            try:
                log_record = {
                    "id": str(doc["_id"]),
                    "corp_key": doc["corp_key"],
                    "category": doc["category"],
                    "action": doc["action"],
                    "details": doc["details"],
                    "device_info": doc["device_info"],
                    "browser_info": doc["browser_info"],
                    "client_ip": doc["client_ip"],
                    "user_agent": doc["user_agent"],
                    "timestamp": doc["timestamp"]
                }
                logs.append(log_record)
            except (KeyError, ValueError) as e:
                # Skip malformed documents
                continue

        return {
            "logs": logs,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": (total_count + page_size - 1) // page_size,
                "has_next": page * page_size < total_count,
                "has_prev": page > 1,
            },
        }

    def search_logs(
        self,
        page: int = 1,
        page_size: int = 20,
        corp_key: str | None = None,
        category: str | None = None,
        action: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ):
        """Search logs with multiple criteria and pagination"""
        skip = (page - 1) * page_size

        # Build query filter
        query = {}

        if corp_key:
            query["corp_key"] = corp_key

        if category:
            query["category"] = category

        if action:
            query["action"] = action

        # Date range filtering
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = datetime.fromisoformat(
                    start_date.replace("Z", "+00:00")
                )
            if end_date:
                date_query["$lte"] = datetime.fromisoformat(
                    end_date.replace("Z", "+00:00")
                )
            query["timestamp"] = date_query

        # Get total count for pagination info
        total_count = self.logs.count_documents(query)

        # Get paginated results, sorted by timestamp descending (newest first)
        cursor = self.logs.find(query).sort("timestamp", -1).skip(skip).limit(page_size)

        # Convert documents to LogRecord objects
        logs = []
        for doc in cursor:
            try:
                log_record = {
                    "id": str(doc["_id"]),
                    "corp_key": doc["corp_key"],
                    "category": doc["category"],
                    "action": doc["action"],
                    "details": doc["details"],
                    "device_info": doc["device_info"],
                    "browser_info": doc["browser_info"],
                    "client_ip": doc["client_ip"],
                    "user_agent": doc["user_agent"],
                    "timestamp": doc["timestamp"]
                }
                logs.append(log_record)
            except (KeyError, ValueError) as e:
                # Skip malformed documents
                continue

        return {
            "logs": logs,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": (total_count + page_size - 1) // page_size,
                "has_next": page * page_size < total_count,
                "has_prev": page > 1,
            },
            "filters": {
                "corp_key": corp_key,
                "category": category,
                "action": action,
                "start_date": start_date,
                "end_date": end_date,
            },
        }
