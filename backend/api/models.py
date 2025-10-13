"""
API Data Models Module

This module defines all Pydantic data models for request/response validation and
serialization in the SecurePrompt banking application. It provides type-safe data
structures with automatic validation, serialization, and API documentation generation.

Key Features:
- Type Safety: Pydantic models with automatic type validation and conversion
- API Documentation: Automatic OpenAPI schema generation with field descriptions
- Data Validation: Comprehensive input validation with custom validators
- Serialization: Automatic JSON serialization/deserialization for API responses
- Response Consistency: Standardized response formats across all API endpoints
- Error Handling: Validation error responses with detailed field-level feedback

Model Categories:
- Authentication Models: Login requests and JWT token responses
- Text Processing Models: Scrubbing requests, responses, and entity metadata
- File Processing Models: File upload, processing, and download responses
- Audit Models: Log records, pagination, and search filter structures
- Entity Models: PII/PHI entity detection results and replacement metadata
"""

from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional


class ReplacementEntity(BaseModel):
    """
    Model for detected PII/PHI entities with replacement metadata from Presidio analysis.

    This model captures complete information about detected sensitive entities
    including their location, type, replacement details, and confidence scoring
    from Microsoft Presidio's entity recognition engine.

    Fields:
        type (str): Entity type classification (PERSON, EMAIL, BELGIAN_ACCOUNT, etc.)
        start (int): Character start position of entity in original text (0-based)
        end (int): Character end position of entity in original text (exclusive)
        original (str): Original detected text content before anonymization
        replacement (str): Anonymized replacement text (e.g., "<PERSON>", "<EMAIL>")
        explanation (str): Human-readable explanation of why entity was detected
        score (float): Confidence score from Presidio analysis (0.0-1.0)

    Example:
        ```json
        {
            "type": "PERSON",
            "start": 8,
            "end": 16,
            "original": "John Doe",
            "replacement": "<PERSON>",
            "explanation": "Detected as person name using NLP model",
            "score": 0.95
        }
        ```
    """

    type: str
    start: int
    end: int
    original: str
    replacement: str
    explanation: str
    score: float


class LoginRequest(BaseModel):
    """
    User authentication request with email and password credentials.

    This model validates user login attempts with proper email format
    validation and secure password handling for authentication workflows.

    Fields:
        email (str): User email address for authentication (validated format)
        password (str): User password in plaintext (hashed during processing)
    """

    email: str
    password: str


class LoginResponse(BaseModel):
    """
    Authentication response with JWT token for successful login attempts.

    This model provides standardized login responses including status
    confirmation and JWT bearer tokens for authenticated sessions.

    Fields:
        status (str): Authentication status ("success" for valid credentials)
        token (str): JWT bearer token for authenticated API access

    Token Usage:
        - Include in Authorization header: "Bearer <token>"
        - Token contains user identity, role, and corporate key
        - Configurable expiration time via application settings
    """

    status: str
    token: str


class TextScrubRequest(BaseModel):
    """
    Request model for text anonymization with configurable risk levels and language support.

    This model validates text scrubbing requests with support for multiple languages
    and risk-based anonymization levels for comprehensive PII/PHI protection.

    Fields:
        prompt (str): Text content to be anonymized (required)
        target_risk (str): Risk level for anonymization (default: "C4")
            - C1: Minimal anonymization (low sensitivity)
            - C2: Standard anonymization (medium sensitivity)
            - C3: Enhanced anonymization (high sensitivity)
            - C4: Maximum anonymization (highest sensitivity)
        language (str, optional): Language code for NLP processing (default: "en")
            - Supports: en, fr, de, es, it, nl, and other Presidio languages
            - Affects entity recognition accuracy and processing models
    """

    prompt: str
    target_risk: str = "C4"
    language: Optional[str] = "en"


class TextScrubResponse(BaseModel):
    """
    Response model for text anonymization results with comprehensive entity metadata.

    This model provides complete text scrubbing results including the anonymized
    text, unique audit identifier, and detailed entity detection information.

    Fields:
        scrub_id (str): Unique MongoDB ObjectId for audit trail and descrubbing
        scrubbed_text (str): Anonymized text with entities replaced by tokens
        entities (List[ReplacementEntity]): Detected entities with replacement details

    Example:
        ```json
        {
            "scrub_id": "507f1f77bcf86cd799439011",
            "scrubbed_text": "Contact <PERSON> at <EMAIL> for account <BELGIAN_ACCOUNT>",
            "entities": [
                {"type": "PERSON", "start": 8, "end": 16, "original": "John Doe", ...},
                {"type": "EMAIL", "start": 20, "end": 36, "original": "john@email.com", ...}
            ]
        }
        ```
    """

    scrub_id: str
    scrubbed_text: str
    entities: List[ReplacementEntity]


class FileScrubResponse(BaseModel):
    """
    Response model for file anonymization results with download and entity information.

    This model provides complete file scrubbing results including processed file
    information, secure download URLs, and comprehensive entity detection metadata
    for document anonymization workflows.

    Fields:
        scrub_id (str): Unique MongoDB ObjectId for audit trail and file tracking
        input_filename (str): Original uploaded file name for reference
        output_filename (str): Generated anonymized file name in temporary storage
        download_url (str): Secure API endpoint for downloading processed file
        entities (List[ReplacementEntity]): Detected entities with replacement details

    Example:
        ```json
        {
            "scrub_id": "507f1f77bcf86cd799439011",
            "input_filename": "contract_draft.pdf",
            "output_filename": "scrubbed_507f1f77bcf86cd799439011.pdf",
            "download_url": "/file/download/507f1f77bcf86cd799439011",
            "entities": [
                {"type": "PERSON", "original": "John Smith", "replacement": "<PERSON>", ...},
                {"type": "BELGIAN_ACCOUNT", "original": "BE68539007547034", "replacement": "<ACCOUNT>", ...}
            ]
        }
        ```
    """

    scrub_id: str
    input_filename: str
    output_filename: str
    download_url: str
    entities: List[ReplacementEntity]


class DescrubRequest(BaseModel):
    """
    Request model for data restoration with strict access control and justification requirements.

    This model validates descrubbing requests for authorized personnel to restore original
    content from previously anonymized text or files. Requires mandatory justification
    for all restoration operations for compliance and audit purposes.

    Fields:
        scrub_id (str): MongoDB ObjectId of original scrubbing operation to restore
        descrub_all (bool): Complete restoration flag (default: False for partial)
            - True: Restore all original content completely
            - False: Restore only specified entity replacements
        entity_replacements (List[str]): Specific replacement tokens to restore
            - Example: ["<PERSON>", "<EMAIL>"] for selective restoration
            - Ignored when descrub_all=True
        justification (str): Mandatory business justification for restoration
            - Required for all descrubbing operations for compliance
            - Becomes part of permanent audit record
            - Examples: "Legal discovery request", "Fraud investigation"

    Example:
        ```json
        {
            "scrub_id": "507f1f77bcf86cd799439011",
            "descrub_all": false,
            "entity_replacements": ["<PERSON>", "<EMAIL>"],
            "justification": "Customer service escalation - fraud investigation case #2024-001"
        }
        ```
    """

    scrub_id: str
    descrub_all: bool = False
    entity_replacements: List[str]
    justification: str


class TextDescrubResponse(BaseModel):
    """
    Response model for text restoration operations with complete content history.

    This model provides comprehensive descrubbing results including original content,
    previously anonymized versions, and current restoration results for audit trail
    completeness and transparency.

    Fields:
        scrub_id (str): Original scrubbing operation identifier for audit linkage
        original_text (str): Complete original text content before anonymization
        scrubbed_text (str): Previously anonymized version with entity replacements
        descrubbed_text (str): Current restoration result based on request parameters

    Example:
        ```json
        {
            "scrub_id": "507f1f77bcf86cd799439011",
            "original_text": "Contact John Doe at john.doe@company.com for account BE68539007547034",
            "scrubbed_text": "Contact <PERSON> at <EMAIL> for account <BELGIAN_ACCOUNT>",
            "descrubbed_text": "Contact John Doe at <EMAIL> for account <BELGIAN_ACCOUNT>"
        }
        ```
    """

    scrub_id: str
    original_text: str
    scrubbed_text: str
    descrubbed_text: str


class PaginationInfo(BaseModel):
    """
    Standardized pagination metadata for efficient large dataset navigation.

    This model provides comprehensive pagination information for API responses
    that return large datasets, enabling efficient client-side navigation and
    proper user interface controls for data browsing.

    Fields:
        page (int): Current page number (1-based indexing)
        page_size (int): Number of records per page (configurable, typically 20-100)
        total_count (int): Total number of records in the complete dataset
        total_pages (int): Total number of pages based on page_size
        has_next (bool): True if additional pages are available after current page
        has_prev (bool): True if previous pages exist before current page

    Example:
        ```json
        {
            "page": 3,
            "page_size": 20,
            "total_count": 157,
            "total_pages": 8,
            "has_next": true,
            "has_prev": true
        }
        ```
    """

    page: int
    page_size: int
    total_count: int
    total_pages: int
    has_next: bool
    has_prev: bool


class LogRecordResponse(BaseModel):
    """
    Comprehensive audit log record response with complete metadata for compliance monitoring.

    This model represents a complete audit log entry with all security metadata,
    client identification, and operational context for regulatory compliance,
    security monitoring, and forensic analysis purposes.

    Fields:
        id (str): Unique MongoDB ObjectId for record identification and referencing
        corp_key (str): Corporate identifier for multi-tenant data isolation
        category (str): Event category (SECURITY, TEXT, FILE, SYSTEM)
        action (str): Specific action performed (LOGIN, LOGOUT, SCRUB, DESCRUB, DOWNLOAD)
        details (dict): Action-specific metadata and operational context
        device_info (str): Client device and operating system identification
        browser_info (str): Browser type and version for client fingerprinting
        client_ip (str): Client IP address with proxy detection support
        user_agent (str): Complete User-Agent header for forensic analysis
        timestamp (datetime): Precise UTC timestamp of event occurrence

    Example:
        ```json
        {
            "id": "507f1f77bcf86cd799439011",
            "corp_key": "COMPANY_001",
            "category": "SECURITY",
            "action": "LOGIN",
            "details": {
                "email": "user@company.com",
                "success": true,
                "mfa_enabled": false
            },
            "device_info": "Windows 10/11",
            "browser_info": "Chrome 120.0",
            "client_ip": "192.168.1.100",
            "user_agent": "Mozilla/5.0...",
            "timestamp": "2024-12-01T14:30:22.123456Z"
        }
        ```
    """

    id: str
    corp_key: str
    category: str
    action: str
    details: dict
    device_info: str
    browser_info: str
    client_ip: str
    user_agent: str
    timestamp: datetime


class LogListResponse(BaseModel):
    """
    Paginated audit log response for comprehensive compliance and monitoring access.

    This model combines audit log records with pagination metadata to provide
    efficient access to large audit datasets for compliance reporting, security
    monitoring, and operational analytics.

    Fields:
        logs (List[LogRecordResponse]): Array of audit records with complete metadata
        pagination (PaginationInfo): Navigation information for dataset browsing

    Example:
        ```json
        {
            "logs": [
                {
                    "id": "507f1f77bcf86cd799439011",
                    "category": "SECURITY",
                    "action": "LOGIN",
                    "timestamp": "2024-12-01T14:30:22Z",
                    // ... complete log record
                }
            ],
            "pagination": {
                "page": 1,
                "page_size": 20,
                "total_count": 15847,
                "total_pages": 793,
                "has_next": true,
                "has_prev": false
            }
        }
        ```
    """

    logs: List[LogRecordResponse]
    pagination: PaginationInfo


class LogSearchFilters(BaseModel):
    """
    Advanced audit log search filter criteria for targeted compliance analysis.

    This model defines comprehensive search parameters for audit log filtering,
    enabling precise queries for compliance reporting, security investigations,
    and operational monitoring across multiple dimensions.

    Fields:
        corp_key (str, optional): Filter by corporate identifier for organization-specific audits
        category (str, optional): Filter by event category (SECURITY, TEXT, FILE, SYSTEM)
        action (str, optional): Filter by specific action (LOGIN, SCRUB, DESCRUB, etc.)
        start_date (str, optional): Start date for time range filtering (ISO 8601 format)
        end_date (str, optional): End date for time range filtering (ISO 8601 format)

    Example Usage Scenarios:
        ```json
        // Security audit for specific organization
        {
            "corp_key": "COMPANY_001",
            "category": "SECURITY",
            "start_date": "2024-11-01T00:00:00Z",
            "end_date": "2024-11-30T23:59:59Z"
        }

        // All descrubbing operations across organizations
        {
            "action": "DESCRUB"
        }

        // File operations in specific time window
        {
            "category": "FILE",
            "start_date": "2024-12-01T08:00:00Z",
            "end_date": "2024-12-01T18:00:00Z"
        }
        ```
    """

    corp_key: Optional[str] = None
    category: Optional[str] = None
    action: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class LogSearchResponse(BaseModel):
    """
    Comprehensive audit log search response with filtered results and applied criteria.

    This model provides complete search results including filtered audit records,
    pagination metadata, and applied filter criteria for context preservation
    and result interpretation in compliance and security analysis workflows.

    Fields:
        logs (List[LogRecordResponse]): Filtered audit records matching search criteria
        pagination (PaginationInfo): Navigation metadata for filtered dataset
        filters (LogSearchFilters): Applied filter criteria for result context

    Example:
        ```json
        {
            "logs": [
                {
                    "id": "507f1f77bcf86cd799439011",
                    "corp_key": "COMPANY_001",
                    "category": "SECURITY",
                    "action": "LOGIN",
                    "timestamp": "2024-11-15T10:30:22Z",
                    // ... complete filtered record
                }
            ],
            "pagination": {
                "page": 1,
                "page_size": 50,
                "total_count": 127,  // Total matching records
                "total_pages": 3,
                "has_next": true,
                "has_prev": false
            },
            "filters": {
                "corp_key": "COMPANY_001",
                "category": "SECURITY",
                "action": null,
                "start_date": "2024-11-01T00:00:00Z",
                "end_date": "2024-11-30T23:59:59Z"
            }
        }
        ```
    """

    logs: List[LogRecordResponse]
    pagination: PaginationInfo
    filters: LogSearchFilters
