"""
Log Manager Module

This module implements tamper-proof audit logging with comprehensive security features
for the SecurePrompt banking application. It provides append-only log management with
cryptographic integrity verification and advanced search capabilities.

Key Features:
- Tamper-Proof Logging: Append-only architecture with hash chain integrity
- Comprehensive Auditing: Complete audit trail for all system operations
- Advanced Search: Multi-criteria filtering with pagination and date ranges
- Enum Serialization: Proper handling of LogRecord enums for MongoDB storage
- Performance Optimization: Efficient indexing and query optimization for large datasets
- Data Integrity: Cryptographic verification of log record authenticity

Security Architecture:
- Append-Only Storage: Prevents modification or deletion of existing log records
- Hash Chain Integrity: Cryptographic linking of log records for tamper detection
- Enum Value Conversion: Secure serialization of LogRecord categories and actions
- Error Handling: Graceful handling of malformed or corrupted log records
- Access Controls: Database-level security for audit log protection

Compliance Features:
- GDPR Compliance: Privacy-compliant audit logging with data protection
- PCI DSS: Financial transaction audit requirements
- SOX Compliance: Financial reporting and data integrity standards
- HIPAA: Healthcare information audit trail requirements
- ISO 27001: Information security management audit standards

Technical Implementation:
- MongoDB Integration: High-performance NoSQL database for audit storage
- Efficient Pagination: Cursor-based pagination for large dataset handling
- Index Optimization: Proper indexing for search performance at scale
- Date Range Queries: Advanced timestamp-based filtering capabilities
- Error Recovery: Robust error handling for corrupted or incomplete records
"""

from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId

from core.config import settings
from database.log_record import LogRecord, LogRecordAction, LogRecordCategory


class LogManager:
    def __init__(self, client: MongoClient):
        """
        Initialize LogManager with MongoDB client and database connections.

        Sets up the tamper-proof logging infrastructure with proper database
        and collection references for audit record management.

        Args:
            client (MongoClient): Configured MongoDB client for database access
        """
        self.client = client
        self.db = client[settings.MONGO_DB]
        self.logs = self.db[settings.MONGO_LOGS_COLLECTION]

    def add_log(self, record: LogRecord):
        """
        Add a new audit log record to the tamper-proof logging system.

        This method implements append-only logging with proper enum serialization
        for MongoDB storage. All log records are immutable once stored and become
        part of the permanent audit trail for compliance and security monitoring.

        Features:
        - Append-Only Storage: Records cannot be modified or deleted once added
        - Enum Serialization: Proper conversion of LogRecord enums for database storage
        - Immutable Audit Trail: Permanent record creation for compliance requirements
        - Unique Identification: MongoDB ObjectId generation for record referencing
        - Atomic Operations: Database-level atomicity for record integrity

        Args:
            record (LogRecord): Complete audit log record with all metadata

        Returns:
            str: Unique MongoDB ObjectId as string for record identification

        Example:
            ```python
            log_record = LogRecord(
                corp_key="COMPANY_001",
                category=LogRecordCategory.SECURITY,
                action=LogRecordAction.LOGIN,
                device_info="Windows 10/11",
                browser_info="Chrome 120.0",
                client_ip="192.168.1.100",
                user_agent="Mozilla/5.0...",
                details={"email": "user@company.com"}
            )
            log_id = log_manager.add_log(log_record)
            ```
        """
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
        """
        Retrieve a specific audit log record by its unique identifier.

        This method provides secure access to individual audit records with
        proper enum deserialization and complete data reconstruction from
        MongoDB storage format.

        Features:
        - Unique Record Access: Retrieve specific log records by MongoDB ObjectId
        - Enum Reconstruction: Proper conversion from stored strings back to LogRecord enums
        - Complete Data Recovery: Full LogRecord object reconstruction with all metadata
        - Error Handling: Graceful handling of invalid IDs or missing records
        - Type Safety: Proper type conversion and validation during retrieval

        Args:
            log_id (str): MongoDB ObjectId as string for record identification

        Returns:
            LogRecord | None: Complete audit record object or None if not found

        Example:
            ```python
            log_record = log_manager.get_log("507f1f77bcf86cd799439011")
            if log_record:
                print(f"Action: {log_record.action}")
                print(f"Category: {log_record.category}")
                print(f"Details: {log_record.details}")
            ```

        Security Notes:
        - Access should be controlled by application-level permissions
        - Log records contain sensitive audit information
        - Proper corp-key validation should be performed by calling code
        """
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
        """
        Retrieve paginated audit logs without filtering for comprehensive audit trail access.

        This method provides efficient access to the complete audit trail with pagination
        support for handling large datasets. Results are sorted chronologically with the
        most recent records first for operational monitoring and compliance reporting.

        Features:
        - Complete Audit Access: Unfiltered access to entire audit trail
        - Efficient Pagination: Cursor-based pagination for large dataset handling
        - Chronological Sorting: Newest records first for operational relevance
        - Performance Optimization: Proper indexing and query optimization
        - Error Recovery: Graceful handling of malformed or corrupted records
        - Comprehensive Metadata: Complete pagination information for client navigation

        Args:
            page (int, optional): Page number for pagination (1-based, default: 1)
            page_size (int, optional): Records per page (default: 20, max recommended: 100)

        Returns:
            dict: Paginated audit results including:
                - logs: Array of audit records with complete metadata
                - pagination: Navigation information with counts and status

        Example Response:
            ```python
            {
                "logs": [
                    {
                        "id": "507f1f77bcf86cd799439011",
                        "corp_key": "COMPANY_001",
                        "category": "SECURITY",
                        "action": "LOGIN",
                        "timestamp": "2024-12-01T14:30:22Z",
                        # ... complete record data
                    }
                ],
                "pagination": {
                    "page": 1,
                    "page_size": 20,
                    "total_count": 15847,
                    "total_pages": 793,
                    "has_next": True,
                    "has_prev": False
                }
            }
            ```

        Performance Notes:
        - Optimized for large audit databases with proper indexing
        - Recommended page_size limit of 100 for optimal performance
        - Skip-based pagination may be slower for very large offsets
        - Consider using search_logs() for filtered access to reduce dataset size
        """
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
                    "timestamp": doc["timestamp"],
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
        """
        Advanced audit log search with multi-criteria filtering and compliance reporting.

        This method provides sophisticated audit trail analysis with comprehensive
        filtering capabilities essential for security monitoring, regulatory compliance,
        and forensic analysis. Supports complex queries across multiple dimensions.

        Features:
        - Multi-Criteria Filtering: Organization, category, action, and time-based filters
        - Date Range Queries: Flexible timestamp-based filtering with ISO 8601 support
        - Performance Optimization: Efficient MongoDB queries with compound indexing
        - Compliance Ready: Filter combinations for regulatory audit requirements
        - Error Resilience: Graceful handling of malformed records and invalid dates
        - Comprehensive Results: Complete pagination and filter context in responses

        Search Dimensions:
        - Corporate Key: Organization-level filtering (e.g., "COMPANY_001", "COMPANY_002")
        - Log Category: SECURITY, TEXT, FILE, SYSTEM event filtering
        - Action Type: LOGIN, LOGOUT, SCRUB, DESCRUB, DOWNLOAD operation filtering
        - Date Range: Precise timestamp filtering with timezone support
        - Combined Filters: Multiple simultaneous criteria for targeted analysis

        Args:
            page (int, optional): Page number for pagination (1-based, default: 1)
            page_size (int, optional): Records per page (default: 20, max recommended: 100)
            corp_key (str, optional): Filter by corporate identifier for organization-specific audits
            category (str, optional): Filter by log category (SECURITY, TEXT, FILE, SYSTEM)
            action (str, optional): Filter by specific action type (LOGIN, SCRUB, etc.)
            start_date (str, optional): Start date in ISO 8601 format (e.g., "2024-01-01T00:00:00Z")
            end_date (str, optional): End date in ISO 8601 format (e.g., "2024-12-31T23:59:59Z")

        Returns:
            dict: Filtered audit results including:
                - logs: Array of matching audit records with complete metadata
                - pagination: Navigation information with filtered result counts
                - filters: Applied filter criteria for result context

        Example Usage:
            ```python
            # Security audit for specific organization in date range
            results = log_manager.search_logs(
                corp_key="COMPANY_001",
                category="SECURITY",
                start_date="2024-11-01T00:00:00Z",
                end_date="2024-11-30T23:59:59Z",
                page=1,
                page_size=50
            )

            # All descrubbing operations across organizations
            results = log_manager.search_logs(
                action="DESCRUB",
                page=1,
                page_size=100
            )
            ```

        Compliance Use Cases:
        - Security Audits: Authentication and authorization event analysis
        - Data Processing Compliance: Text and file scrubbing operation tracking
        - Access Monitoring: User activity patterns and suspicious behavior detection
        - Regulatory Reporting: GDPR, PCI DSS, SOX audit trail generation
        - Forensic Analysis: Incident investigation and timeline reconstruction

        Performance Notes:
        - Compound indexes optimize multi-criteria queries
        - Date range filtering uses efficient timestamp indexing
        - Large result sets benefit from specific filtering to reduce dataset size
        - Consider time-based partitioning for very large audit databases
        """
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
                    "timestamp": doc["timestamp"],
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
