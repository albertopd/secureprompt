"""
File Management Module

This module provides MongoDB-based file storage and retrieval capabilities for the SecurePrompt
banking application.
"""

from pymongo import MongoClient
from bson import ObjectId

from core.config import settings


class FileManager:
    """
    Secure file storage and retrieval manager with multi-tenant isolation.

    This class provides comprehensive file management capabilities for the SecurePrompt
    banking application.
    """

    def __init__(self, client: MongoClient):
        """
        Initialize FileManager with MongoDB client and database connections.

        Sets up the file management infrastructure with proper database and
        collection references for file storage and retrieval operations.

        Args:
            client (MongoClient): Configured MongoDB client for database access

        Attributes:
            client: MongoDB client for database operations
            db: Database instance for file storage
            files: Collection for file documents and metadata
        """
        self.client = client
        self.db = client[settings.MONGO_DB]
        self.files = self.db[settings.MONGO_FILES_COLLECTION]

    def get_file(self, file_id: str):
        """
        Retrieve a file document by its unique identifie.

        This method provides access to stored files with MongoDB ObjectId-based
        identification.

        Args:
            file_id (str): MongoDB ObjectId as string for file identification

        Returns:
            dict | None: Complete file document including metadata and binary data,
                        or None if file not found

        File Document Structure:
            ```python
            {
                "_id": ObjectId("507f1f77bcf86cd799439011"),
                "corp_key": "COMPANY_001",
                "filename": "processed_document.pdf",
                "data": b"binary_file_content...",
                # Additional metadata fields as needed
            }
            ```

        Example Usage:
            ```python
            file_doc = file_manager.get_file("507f1f77bcf86cd799439011")
            if file_doc and file_doc["corp_key"] == user_corp_key:
                filename = file_doc["filename"]
                file_data = file_doc["data"]
                # Process authorized file access
            else:
                # Handle unauthorized access or missing file
            ```
        """
        return self.files.find_one({"_id": ObjectId(file_id)})

    def add_file(self, filename: str, data: bytes, corp_key: str) -> str:
        """
        Store a new file with corporate key isolation and secure binary data handling.

        This method provides secure file storage with multi-tenant isolation through
        corporate key association. 

        Args:
            filename (str): Original filename for identification and reference
            data (bytes): Binary file content to be stored securely
            corp_key (str): Corporate identifier for multi-tenant access control

        Returns:
            str: Unique MongoDB ObjectId as string for file identification and retrieval

        Example Usage:
            ```python
            # Store processed document with organizational context
            with open("processed_file.pdf", "rb") as file:
                file_data = file.read()

            file_id = file_manager.add_file(
                filename="anonymized_contract.pdf",
                data=file_data,
                corp_key="COMPANY_001"
            )

            # Use file_id for download URL generation
            download_url = f"/file/download/{file_id}"
            ```
        """
        res = self.files.insert_one(
            {"corp_key": corp_key, "filename": filename, "data": data}
        )
        return str(res.inserted_id)
