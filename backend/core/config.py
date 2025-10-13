"""
Application Configuration Settings

This module defines the configuration settings for the SecurePrompt application
using Pydantic Settings for validation and environment variable management.

The settings include:
- Application metadata and API configuration
- JWT authentication parameters
- MongoDB database connection settings
- File storage paths and security keys
- Environment-specific configurations

Settings can be overridden via environment variables or .env file.
Security-sensitive values are auto-generated with secure defaults.

Author: SecurePrompt Development Team
"""

import secrets
from typing import Literal
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings configuration with validation and environment support.

    This class defines all configuration parameters for the SecurePrompt application,
    including database connections, authentication keys, file paths, and security settings.

    Settings are loaded from:
    1. Environment variables (highest priority)
    2. .env file in parent directory
    3. Default values defined in class attributes

    Attributes:
        PROJECT_NAME (str): Application name for API documentation
        ENVIRONMENT (Literal): Deployment environment (local/staging/production)
        API_V1_STR (str): API version prefix for endpoint routing
        JWT_SECRET_KEY (str): Secret key for JWT token signing
        JWT_ALGORITHM (str): Algorithm used for JWT token signing
        ACCESS_TOKEN_EXPIRE_MINUTES (int): JWT token expiration time in minutes
        MONGO_URI (str): MongoDB connection string
        MONGO_DB (str): MongoDB database name
        MONGO_USERS_COLLECTION (str): Collection name for user data
        MONGO_LOGS_COLLECTION (str): Collection name for audit logs
        MONGO_FILES_COLLECTION (str): Collection name for file metadata
        LOG_INTEGRITY_KEY (str): HMAC key for tamper-proof logging
        EMPLOYEES_CSV_PATH (str): Path to employee mock data file
        TMP_FILES_PATH (str): Temporary file storage directory
    """

    model_config = SettingsConfigDict(
        env_file="../.env",  # Use top level .env file (one level above ./backend/)
        env_file_encoding="utf-8",
    )

    # Application Configuration
    PROJECT_NAME: str = "SecurePrompt"  # Application name for API docs and logging
    ENVIRONMENT: Literal["local", "staging", "production"] = (
        "local"  # Deployment environment
    )
    API_V1_STR: str = "/api/v1"  # API version prefix for endpoint routing

    # Authentication & Security Settings
    JWT_SECRET_KEY: str = secrets.token_urlsafe(32)  # Auto-generated JWT signing key
    JWT_ALGORITHM: str = "HS256"  # JWT signing algorithm (HMAC with SHA-256)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # Token validity: 8 days
    LOG_INTEGRITY_KEY: str = secrets.token_urlsafe(32)  # HMAC key for tamper-proof logs

    # MongoDB Database Configuration
    MONGO_URI: str = "mongodb://localhost:27017"  # MongoDB connection string
    MONGO_DB: str = "secureprompt"  # Primary database name
    MONGO_USERS_COLLECTION: str = "users"  # User accounts and roles collection
    MONGO_LOGS_COLLECTION: str = "logs"  # Audit logs with integrity protection
    MONGO_FILES_COLLECTION: str = "files"  # File metadata and processing history

    # File System Paths
    EMPLOYEES_CSV_PATH: str = (
        "data/mock_employees.csv"  # Mock employee data for testing
    )
    TMP_FILES_PATH: str = (
        "C:/tmp/secureprompt_files"  # Temporary file storage directory
    )


# Global settings instance - imported throughout the application
settings = Settings()
