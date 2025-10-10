from pymongo import MongoClient
from bson import ObjectId

from core.config import settings


class FileManager:
    def __init__(self, client: MongoClient):
        self.client = client
        self.db = client[settings.MONGO_DB]
        self.files = self.db[settings.MONGO_FILES_COLLECTION]

    def get_file(self, file_id: str):
        return self.files.find_one({"_id": ObjectId(file_id)})

    def add_file(self, filename: str, data: bytes, corp_key: str) -> str:
        res = self.files.insert_one({"corp_key": corp_key, "filename": filename, "data": data})
        return str(res.inserted_id)
