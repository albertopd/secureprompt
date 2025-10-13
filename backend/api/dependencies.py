"""
Dependency Injection Module

This module provides FastAPI dependency injection functions for the SecurePrompt
banking application. It implements a clean separation of concerns by centralizing
service instantiation and dependency management for database connections,
business logic services, and data processing components.

Key Features:
- Centralized Service Management: Single source for all application dependencies
- FastAPI Integration: Native dependency injection compatible with FastAPI framework
- Database Connection Management: Proper MongoDB client lifecycle and connection pooling
- Service Instantiation: Consistent service creation with proper dependency resolution
- Testability: Easy mocking and testing support through dependency injection
- Performance Optimization: Efficient service reuse and connection sharing

Dependency Categories:
- Database Layer: MongoDB client and data manager services
- Authentication: User management and credential validation services
- Audit System: Tamper-proof logging and compliance tracking services
- Text Processing: PII/PHI detection and anonymization engines
- File Processing: Document handling and multi-format processing services

Architecture Benefits:
- Loose Coupling: Services depend on abstractions rather than concrete implementations
- Single Responsibility: Each dependency function has a focused, single purpose
- Dependency Graph: Clear dependency relationships and proper initialization order
- Resource Management: Proper lifecycle management for database connections and services
- Configuration Integration: Seamless integration with application configuration settings

FastAPI Integration:
- Dependency Provider Functions: Compatible with FastAPI's Depends() mechanism
- Automatic Injection: Services automatically injected into route handlers
- Type Safety: Full type annotation support for IDE assistance and validation
- Request Scope: Proper service lifecycle management per HTTP request
- Error Handling: Graceful dependency resolution failure management
"""

from fastapi import Depends
from pymongo import MongoClient

from database.connection import get_mongo_client
from database.user_manager import UserManager
from database.log_manager import LogManager
from database.file_manager import FileManager
from scrubbers.text_scrubber import TextScrubber
from scrubbers.file_scrubber import FileScrubber


def get_mongo_client_dep() -> MongoClient:
    """
    FastAPI dependency provider for MongoDB client with connection pooling and lifecycle management.

    This function serves as the primary database connection dependency for all FastAPI
    route handlers and services requiring MongoDB access. It provides access to the
    singleton database manager with proper connection pooling and error handling.

    Features:
    - Connection Pooling: Leverages MongoDB's built-in connection pooling for efficiency
    - Singleton Access: Returns the same client instance across all dependency injections
    - Lifecycle Management: Proper connection initialization and cleanup handling
    - Error Recovery: Graceful handling of connection failures with appropriate exceptions
    - Performance Optimization: Efficient connection reuse across concurrent requests

    Returns:
        MongoClient: Active MongoDB client instance ready for database operations

    Raises:
        RuntimeError: When database manager is not properly initialized
        pymongo.errors.ConnectionFailure: When unable to connect to MongoDB

    Usage in Route Handlers:
        ```python
        @router.get("/users")
        async def get_users(client: MongoClient = Depends(get_mongo_client_dep)):
            db = client[settings.MONGO_DB]
            users_collection = db[settings.MONGO_USERS_COLLECTION]
            return list(users_collection.find({}))
        ```

    Dependency Graph:
        - No Dependencies: Root-level dependency for database access
        - Used By: All database manager services (UserManager, LogManager, FileManager)
        - Lifecycle: Application-scoped singleton with request-level injection

    Configuration:
        - MongoDB URI from application settings (MONGO_URI)
        - Connection parameters configured via URI string
        - SSL/TLS and authentication settings handled by URI configuration
    """
    return get_mongo_client()


def get_user_manager_dep(
    client: MongoClient = Depends(get_mongo_client_dep),
) -> UserManager:
    """
    FastAPI dependency provider for user authentication and management services.

    This function creates UserManager instances with proper MongoDB client injection
    for handling user authentication, credential validation, and role-based access
    control throughout the application.

    Features:
    - User Authentication: Secure credential validation with SHA-256 password hashing
    - Role Management: Support for admin, auditor, descrubber, and scrubber roles
    - Multi-Tenant Support: Corporate key-based user organization and data isolation
    - Database Integration: Seamless MongoDB user collection management
    - Auto-Provisioning: Automatic user creation from CSV data for development/testing

    Dependencies:
        client (MongoClient): MongoDB client from get_mongo_client_dep for database operations

    Returns:
        UserManager: Configured user management service with database connectivity

    Usage in Route Handlers:
        ```python
        @router.post("/login")
        async def login(
            credentials: LoginRequest,
            user_manager: UserManager = Depends(get_user_manager_dep)
        ):
            user = user_manager.check_user_credentials(credentials.email, credentials.password)
            if user:
                # Generate JWT token and return success
                return {"status": "success", "token": generate_token(user)}
            raise HTTPException(401, "Invalid credentials")
        ```

    Service Capabilities:
        - get_user_by_email(): Retrieve user by email for authentication
        - check_user_credentials(): Validate email/password combinations
        - User provisioning from employee CSV files for development environments
        - Role-based user classification for RBAC implementation

    Security Features:
        - SHA-256 password hashing for secure credential storage
        - Email uniqueness constraint enforcement at database level
        - Corporate key isolation for multi-tenant security
        - Secure user lookup with proper error handling for failed authentication
    """
    return UserManager(client)


def get_log_manager_dep(
    client: MongoClient = Depends(get_mongo_client_dep),
) -> LogManager:
    """
    FastAPI dependency provider for tamper-proof audit logging and compliance services.

    This function creates LogManager instances with MongoDB client injection for
    comprehensive audit trail management, compliance reporting, and security
    monitoring throughout the SecurePrompt banking application.

    Features:
    - Tamper-Proof Logging: Append-only audit records with hash chain integrity
    - Comprehensive Auditing: Complete event tracking for security and compliance
    - Advanced Search: Multi-criteria filtering with pagination for large datasets
    - Compliance Ready: GDPR, PCI DSS, SOX, and HIPAA audit trail requirements
    - Performance Optimized: Efficient MongoDB operations with proper indexing

    Dependencies:
        client (MongoClient): MongoDB client from get_mongo_client_dep for audit storage

    Returns:
        LogManager: Configured audit logging service with tamper-proof capabilities

    Usage in Route Handlers:
        ```python
        @router.post("/scrub")
        async def scrub_text(
            request: Request,
            scrub_request: TextScrubRequest,
            session: dict = Depends(require_auth),
            log_manager: LogManager = Depends(get_log_manager_dep)
        ):
            # Process text scrubbing
            result = process_text(scrub_request.prompt)

            # Log the operation with comprehensive metadata
            client_info = extract_client_info(request)
            log_id = log_manager.add_log(LogRecord(
                corp_key=session["corp_key"],
                category=LogRecordCategory.TEXT,
                action=LogRecordAction.SCRUB,
                details={"entities_found": len(result.entities)},
                device_info=client_info.device_info,
                browser_info=client_info.browser_info,
                client_ip=client_info.client_ip,
                user_agent=client_info.user_agent
            ))

            return {"scrub_id": str(log_id), "result": result}
        ```

    Service Capabilities:
        - add_log(): Create immutable audit records with comprehensive metadata
        - get_log(): Retrieve specific audit records by ID for reference
        - list_logs(): Paginated access to complete audit trail
        - search_logs(): Advanced filtering for compliance and security analysis

    Security & Compliance:
        - Immutable Records: Append-only structure prevents audit trail tampering
        - Comprehensive Metadata: Complete client identification and operational context
        - Multi-Tenant Isolation: Corp-key based data separation and access control
        - Regulatory Compliance: Structured audit format for regulatory requirements
    """
    return LogManager(client)


def get_file_manager_dep(
    client: MongoClient = Depends(get_mongo_client_dep),
) -> FileManager:
    """
    FastAPI dependency provider for secure file management and storage services.

    This function creates FileManager instances with MongoDB client injection for
    handling secure file storage, access control, and metadata management for
    document processing workflows in the banking application.

    Features:
    - Secure File Storage: Controlled access to processed and temporary files
    - Metadata Management: File information tracking with audit trail integration
    - Access Control: Authentication and authorization for file operations
    - Temporary File Handling: Secure temporary storage with automatic cleanup
    - Multi-Format Support: Integration with various document processing capabilities

    Dependencies:
        client (MongoClient): MongoDB client from get_mongo_client_dep for file metadata storage

    Returns:
        FileManager: Configured file management service with secure storage capabilities

    Usage in Route Handlers:
        ```python
        @router.post("/file/upload")
        async def upload_file(
            file: UploadFile = File(...),
            session: dict = Depends(require_auth),
            file_manager: FileManager = Depends(get_file_manager_dep)
        ):
            # Process file upload with security validation
            file_metadata = file_manager.store_file(
                file_content=await file.read(),
                filename=file.filename,
                corp_key=session["corp_key"],
                user_id=session["email"]
            )

            return {"file_id": file_metadata["id"], "status": "uploaded"}
        ```

    Service Capabilities:
        - store_file(): Secure file storage with metadata tracking
        - get_file(): Retrieve files with access control validation
        - list_files(): File listing with corporate key isolation
        - delete_file(): Secure file removal with audit logging
        - File metadata management with MongoDB integration

    Security Features:
        - Access Control: Corp-key based file access isolation
        - Audit Integration: File operations logged for compliance
        - Secure Storage: Protected file system access with path validation
        - Temporary File Management: Automatic cleanup of processed files
        - Authentication: Integration with JWT-based access control
    """
    return FileManager(client)


def get_text_scrubber_dep() -> TextScrubber:
    """
    FastAPI dependency provider for advanced text anonymization and PII/PHI detection services.

    This function creates TextScrubber instances for Microsoft Presidio-based text
    processing with specialized Belgian banking entity recognition and configurable
    risk-level anonymization for comprehensive data protection.

    Features:
    - PII/PHI Detection: Advanced entity recognition using Microsoft Presidio NLP models
    - Belgian Banking Support: Custom recognizers for Belgian account numbers and financial data
    - Multi-Language Processing: Support for multiple languages with language-specific models
    - Risk-Level Configuration: Configurable anonymization levels (C1-C4) for different sensitivity requirements
    - Entity Transparency: Detailed entity detection results with confidence scoring

    Returns:
        TextScrubber: Configured text anonymization service with Presidio integration

    Usage in Route Handlers:
        ```python
        @router.post("/text/scrub")
        async def scrub_text(
            scrub_request: TextScrubRequest,
            text_scrubber: TextScrubber = Depends(get_text_scrubber_dep)
        ):
            # Process text with configurable risk level and language
            result = text_scrubber.scrub_text(
                text=scrub_request.prompt,
                risk_level=scrub_request.target_risk,
                language=scrub_request.language
            )

            return {
                "scrubbed_text": result["scrubbed_text"],
                "entities": result["entities"],
                "confidence_scores": result["scores"]
            }
        ```

    Service Capabilities:
        - scrub_text(): Anonymize text with entity detection and replacement
        - descrub_text(): Restore original content from anonymized text (restricted access)
        - Entity recognition for multiple PII/PHI types including Belgian banking data
        - Configurable risk levels for different anonymization requirements
        - Multi-language support with language-specific NLP models

    Entity Detection:
        - Personal Information: Names, addresses, phone numbers, email addresses
        - Financial Data: Belgian account numbers, IBAN, credit card numbers
        - Government IDs: Passport numbers, national IDs, social security numbers
        - Healthcare Information: Medical record numbers, health insurance IDs
        - Custom Patterns: Extensible recognition patterns for specialized data types

    Performance Features:
        - Stateless Service: Thread-safe processing for concurrent request handling
        - Model Caching: Efficient NLP model loading and reuse for performance
        - Batch Processing: Optimized for processing multiple text inputs
        - Memory Management: Efficient memory usage for large text processing
    """
    return TextScrubber()


def get_file_scrubber_dep() -> FileScrubber:
    """
    FastAPI dependency provider for comprehensive document processing and multi-format file anonymization.

    This function creates FileScrubber instances for processing various document formats
    including PDF, Microsoft Word, RTF, and plain text files with integrated text
    anonymization and secure file handling capabilities.

    Features:
    - Multi-Format Support: PDF, Word (.docx), RTF, and plain text document processing
    - Text Extraction: Advanced text extraction from structured documents with layout preservation
    - Integrated Anonymization: TextScrubber integration for comprehensive PII/PHI protection
    - Secure Processing: Temporary file handling with automatic cleanup and access controls
    - Format Preservation: Maintains document structure and formatting during anonymization

    Returns:
        FileScrubber: Configured document processing service with multi-format capabilities

    Usage in Route Handlers:
        ```python
        @router.post("/file/scrub")
        async def scrub_file(
            file: UploadFile = File(...),
            target_risk: str = "C4",
            language: str = "en",
            file_scrubber: FileScrubber = Depends(get_file_scrubber_dep)
        ):
            # Process uploaded file with anonymization
            file_content = await file.read()
            result = file_scrubber.scrub_file(
                filename=file.filename,
                file_content=file_content,
                risk_level=target_risk,
                language=language
            )

            return {
                "file_id": result["file_id"],
                "output_filename": result["output_filename"],
                "entities_found": result["entities"],
                "download_url": f"/file/download/{result['file_id']}"
            }
        ```

    Service Capabilities:
        - scrub_file(): Process and anonymize documents with format preservation
        - Text extraction from PDF, Word, RTF, and plain text formats
        - Integrated TextScrubber for comprehensive entity detection and anonymization
        - Secure temporary file storage with automatic cleanup
        - File format detection and appropriate processing pipeline selection

    Supported Formats:
        - PDF Documents: Text extraction with layout awareness and anonymization
        - Microsoft Word (.docx): Content processing with formatting preservation
        - Rich Text Format (RTF): Text extraction and processing capabilities
        - Plain Text Files: Direct text processing with encoding detection
        - Extensible Architecture: Easy addition of new document format support

    Processing Pipeline:
        1. File Format Detection: Automatic format identification and validation
        2. Text Extraction: Format-specific text extraction with structure preservation
        3. Entity Detection: PII/PHI recognition using integrated TextScrubber
        4. Anonymization: Entity replacement with configurable risk levels
        5. Document Reconstruction: Format-appropriate output generation
        6. Secure Storage: Temporary file storage with access controls

    Security Features:
        - Temporary File Management: Secure processing with automatic cleanup
        - Access Controls: Integration with authentication and authorization systems
        - Path Validation: Secure file system operations with path sanitization
        - Memory Management: Efficient processing of large documents
    """
    return FileScrubber()
