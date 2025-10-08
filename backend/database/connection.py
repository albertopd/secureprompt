"""
Database connection management for the FastAPI application.
"""

from typing import Optional
from pymongo import MongoClient
from core.config import settings


class DatabaseManager:
    """Singleton MongoDB connection manager"""

    _instance: Optional["DatabaseManager"] = None
    _client: Optional[MongoClient] = None

    def __new__(cls) -> "DatabaseManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self) -> None:
        """Initialize MongoDB connection"""
        if self._client is None:
            self._client = MongoClient(settings.MONGO_URI)

    def close(self) -> None:
        """Close MongoDB connection"""
        if self._client is not None:
            self._client.close()
            self._client = None

    @property
    def client(self) -> MongoClient:
        """Get MongoDB client"""
        if self._client is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._client


# Global database manager instance
db_manager = DatabaseManager()


def get_mongo_client() -> MongoClient:
    """Get MongoDB client dependency"""
    return db_manager.client
