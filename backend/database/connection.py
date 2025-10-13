"""
Database Connection Management Module

This module provides singleton-based MongoDB connection management for the SecurePrompt
banking application. It ensures efficient connection pooling, proper resource management,
and reliable database connectivity across all application components.

Key Features:
- Singleton Pattern: Single MongoDB client instance across the application lifecycle
- Connection Pooling: Efficient connection reuse with MongoDB's built-in pooling
- Lazy Initialization: Database connections established only when needed
- Resource Management: Proper connection lifecycle management with cleanup
- Configuration Integration: Seamless integration with application configuration settings

Singleton Architecture:
- Single Instance: One DatabaseManager instance per application process
- Thread Safety: MongoDB client handles concurrent access safely
- Resource Efficiency: Shared connection pool reduces database overhead
- State Management: Centralized connection state for monitoring and control
"""

from typing import Optional
from pymongo import MongoClient
from core.config import settings


class DatabaseManager:
    """
    Singleton MongoDB connection manager for centralized database access.

    This class implements the singleton pattern to ensure a single MongoDB client
    instance across the entire application lifecycle. It provides efficient connection
    management with proper initialization and cleanup capabilities.

    Design Pattern:
    - Singleton Implementation: Ensures single instance per application process
    - Lazy Loading: Client creation deferred until first database access
    - State Management: Centralized connection state tracking and control
    - Resource Control: Proper connection lifecycle with explicit cleanup

    Thread Safety:
    - MongoDB Client: PyMongo client handles concurrent access internally
    - Singleton Safety: Class-level instance management with proper initialization
    - Connection Pooling: Built-in MongoDB connection pooling for concurrent requests
    """

    _instance: Optional["DatabaseManager"] = None
    _client: Optional[MongoClient] = None

    def __new__(cls) -> "DatabaseManager":
        """
        Create or return existing DatabaseManager singleton instance.

        Implements the singleton pattern to ensure only one instance exists
        per application process for efficient resource management.

        Returns:
            DatabaseManager: Singleton instance of the database manager
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self) -> None:
        """
        Initialize MongoDB connection with configuration-driven setup.

        Creates a new MongoDB client connection using application settings if one
        doesn't already exist. Implements idempotent initialization to safely
        handle multiple initialization calls.

        Example Usage:
            ```python
            db_manager = DatabaseManager()
            db_manager.initialize()  # Safe to call multiple times
            client = db_manager.client  # Ready for database operations
            ```

        Raises:
            pymongo.errors.ConnectionFailure: When unable to connect to MongoDB
            pymongo.errors.ConfigurationError: When URI configuration is invalid

        Note:
            This method should be called during application startup to ensure
            database connectivity is established before handling requests.
        """
        if self._client is None:
            self._client = MongoClient(settings.MONGO_URI)

    def close(self) -> None:
        """
        Properly close MongoDB connection and clean up resources.

        Gracefully shuts down the MongoDB client connection and clears the
        internal client reference. Essential for proper application shutdown
        and resource cleanup in containerized environments.

        Example Usage:
            ```python
            # During application shutdown
            try:
                db_manager.close()
                logger.info("Database connection closed successfully")
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")
            ```

        Best Practices:
        - Call during application shutdown for proper resource cleanup
        - Use in context managers for automatic resource management
        - Include in exception handlers for error recovery scenarios
        - Essential for clean container termination in Kubernetes environments
        """
        if self._client is not None:
            self._client.close()
            self._client = None

    @property
    def client(self) -> MongoClient:
        """
        Get the active MongoDB client instance with proper initialization validation.

        Provides access to the MongoDB client for database operations with
        initialization state validation to ensure the client is ready for use.

        Returns:
            MongoClient: Active MongoDB client instance ready for database operations

        Raises:
            RuntimeError: When accessed before calling initialize() method

        Example Usage:
            ```python
            db_manager = DatabaseManager()
            db_manager.initialize()

            # Now safe to access client
            client = db_manager.client
            database = client[settings.MONGO_DB]
            collection = database[settings.MONGO_USERS_COLLECTION]
            ```
        """
        if self._client is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._client


# Global database manager instance for application-wide use
db_manager = DatabaseManager()


def get_mongo_client() -> MongoClient:
    """
    FastAPI dependency function to provide MongoDB client for dependency injection.

    This function serves as a FastAPI dependency provider to inject MongoDB
    client instances into route handlers and other application components
    through the dependency injection system.

    Returns:
        MongoClient: Active MongoDB client instance for database operations

    Raises:
        RuntimeError: When database manager is not properly initialized

    Example Usage:
        ```python
        from fastapi import Depends

        # In route handlers
        @router.get("/users")
        def get_users(client: MongoClient = Depends(get_mongo_client)):
            db = client[settings.MONGO_DB]
            users = db[settings.MONGO_USERS_COLLECTION]
            return list(users.find({}))

        # In service classes
        class SomeService:
            def __init__(self, client: MongoClient = Depends(get_mongo_client)):
                self.client = client
        ```
    """
    return db_manager.client
