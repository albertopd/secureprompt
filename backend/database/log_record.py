"""
Log Record Data Structures Module

This module defines the core data structures and enumerations for the audit logging 
system in the SecurePrompt banking application. It provides standardized log record 
formats with comprehensive metadata for compliance and security monitoring.

Audit Categories:
- SECURITY: Authentication, authorization, and access control events
- TEXT: Text processing, scrubbing, and descrubbing operations
- FILE: Document processing, uploads, downloads, and file operations

Action Types:
- LOGIN/LOGOUT: User authentication and session management events
- SCRUB/DESCRUB: Data anonymization and restoration operations
- DOWNLOAD: File access and retrieval operations
"""

from enum import Enum
from dataclasses import dataclass
from typing import Any
from datetime import datetime, timezone


class LogRecordCategory(Enum):
    """
    Enumeration of audit log categories for systematic event classification.

    This enum provides type-safe categorization of all audit events within the
    SecurePrompt banking application. Each category represents a major functional
    area with specific compliance and security monitoring requirements.

    Categories:
    - SECURITY: Authentication, authorization, and access control events
    - TEXT: Text scrubbing and de-scrubbing operations
    - FILE: File scrubbing/de-scrubbing and file download operations

    Usage Example:
        ```python
        log_record = LogRecord(
            corp_key="COMPANY_001",
            category=LogRecordCategory.SECURITY,
            action=LogRecordAction.LOGIN,
            # ... other fields
        )
        ```
    """
    SECURITY = "auth"
    TEXT = "text"
    FILE = "file"


class LogRecordAction(Enum):
    """
    Enumeration of specific audit actions for detailed event tracking.

    This enum provides granular action classification for audit events, enabling
    precise tracking of user activities and system operations for compliance
    monitoring and security analysis.

    Actions:
    - LOGIN: User authentication success event
    - LOGOUT: User session termination events
    - SCRUB: Text/file scrubbing operations
    - DESCRUB: Text/file de-scrubbing operations
    - DOWNLOAD: File access and retrieval operations

    Usage Example:
        ```python
        # Security event logging
        log_record = LogRecord(
            category=LogRecordCategory.SECURITY,
            action=LogRecordAction.LOGIN,
            details={"email": "user@company.com", "success": True}
        )

        # Data processing event logging
        log_record = LogRecord(
            category=LogRecordCategory.TEXT,
            action=LogRecordAction.SCRUB,
            details={"entities_found": 5, "risk_level": "C3"}
        )
        ```
    """
    LOGIN = "login"
    LOGOUT = "logout"
    SCRUB = "scrub"
    DESCRUB = "descrub"
    DOWNLOAD = "download"


@dataclass
class LogRecord:
    """
    Comprehensive audit log record structure.

    This dataclass represents a complete audit event.
    Each record captures the full context of user actions and system operations.

    Fields:
        corp_key (str): User's corporate identifier

        category (LogRecordCategory): High-level event categorization

        action (LogRecordAction): Specific action performed within the category

        details (Any): Action-specific metadata and context information
            * Flexible dictionary structure for operation details
            * May include: user information, processing results, error details
            * Serialized to JSON for MongoDB storage compatibility
            * Examples: {"entities_found": 5}, {"file_size": 1024}, {"error": "timeout"}

        device_info (str): Client device and operating system identification
            * Format: "Windows 10/11", "macOS 14.1", "iPhone iOS 17.1"
            * Extracted from User-Agent header with version detection
            * Critical for security monitoring and access pattern analysis

        browser_info (str): Client browser identification and version
            * Format: "Chrome 120.0", "Firefox 119.0", "Safari 17.1"
            * Parsed from User-Agent with version extraction
            * Enables browser-specific security policy enforcement

        client_ip (str): Client IP address with proxy detection support
            * Real client IP extracted from X-Forwarded-For headers when available
            * Falls back to direct connection IP for non-proxied connections
            * Essential for geolocation analysis and access pattern monitoring

        user_agent (str): Complete User-Agent header for forensic analysis
            * Full browser/device identification string preservation
            * Enables detailed forensic analysis and device fingerprinting
            * Critical for advanced security monitoring and threat detection

        timestamp (datetime): Precise UTC timestamp of event occurrence

    Example Usage:
        ```python
        # Security event logging
        security_log = LogRecord(
            corp_key="COMPANY_001",
            category=LogRecordCategory.SECURITY,
            action=LogRecordAction.LOGIN,
            details={
                "email": "user@company.com",
                "success": True,
                "mfa_used": False
            },
            device_info="Windows 10/11",
            browser_info="Chrome 120.0",
            client_ip="192.168.1.100",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)..."
        )

        # Text processing event logging
        text_log = LogRecord(
            corp_key="COMPANY_002",
            category=LogRecordCategory.TEXT,
            action=LogRecordAction.SCRUB,
            details={
                "entities_detected": ["PERSON", "EMAIL", "BELGIAN_ACCOUNT"],
                "entities_count": 3,
                "risk_level": "C3",
                "language": "en"
            },
            device_info="macOS 14.1",
            browser_info="Safari 17.1",
            client_ip="10.0.1.50",
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)..."
        )
        ```
    """
    corp_key: str
    category: LogRecordCategory
    action: LogRecordAction
    details: Any
    device_info: str
    browser_info: str
    client_ip: str
    user_agent: str
    timestamp: datetime = datetime.now(timezone.utc)
