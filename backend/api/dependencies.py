from fastapi import Depends
from pymongo import MongoClient

from database.connection import get_mongo_client
from database.user_manager import UserManager
from database.log_manager import LogManager
from scrubbers.text_scrubber import TextScrubber
from scrubbers.file_scrubber import FileScrubber


def get_mongo_client_dep() -> MongoClient:
    """Get MongoDB client dependency"""
    return get_mongo_client()


def get_user_manager_dep(
    client: MongoClient = Depends(get_mongo_client_dep),
) -> UserManager:
    """Get UserManager instance with MongoDB client"""
    return UserManager(client)


def get_log_manager_dep(
    client: MongoClient = Depends(get_mongo_client_dep),
) -> LogManager:
    """Get LogManager instance with MongoDB client"""
    return LogManager(client)


def get_text_scrubber_dep() -> TextScrubber:
    """Get TextScrubber instance"""
    return TextScrubber()


def get_file_scrubber_dep() -> FileScrubber:
    """Get FileScrubber instance"""
    return FileScrubber()
