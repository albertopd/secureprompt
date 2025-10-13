"""
User Management Module

This module provides comprehensive user authentication and management capabilities
for the SecurePrompt banking application. It handles user data storage, password
authentication, and role-based access control with secure credential management.

Key Features:
- Secure Authentication: SHA-256 password hashing for credential protection
- Role-Based Access Control: Support for admin, auditor, descrubber, and scrubber roles
- CSV User Import: Automated user provisioning from employee CSV files
- Database Integration: MongoDB-based user storage with proper indexing

User Roles Hierarchy:
- Admin: Full system access
- Auditor: Read-only access to audit logs
- Descrubber: Access to both scrubbing and descrubbing operations (high privilege)
- Scrubber: Limited access to scrubbing operations only (standard user)
"""

import hashlib
import logging
import os
import pandas as pd
import random
from pymongo import MongoClient
from core.config import settings


class UserManager:
    def __init__(self, client: MongoClient):
        """
        Initialize UserManager with MongoDB client and automatic user provisioning.

        Sets up the user management infrastructure with database connections and
        automatically provisions mock users from CSV data if the collection is empty.
        Creates proper database indexes for optimal query performance and data integrity.

        Args:
            client (MongoClient): Configured MongoDB client for database access

        Raises:
            FileNotFoundError: When required CSV file is missing for user provisioning
            Exception: Database connection or initialization failures

        Example:
            ```python
            from pymongo import MongoClient
            client = MongoClient("mongodb://localhost:27017")
            user_manager = UserManager(client)
            ```
        """
        self.client = client
        self.db = client[settings.MONGO_DB]
        self.users = self.db[settings.MONGO_USERS_COLLECTION]

        # Check if table is empty
        if self.users.count_documents({}) == 0:
            logging.info("Users collection is empty. Creating mocked users.")
            self._create_mocked_users_collection(settings.EMPLOYEES_CSV_PATH)
            self.users.create_index("email", unique=True)

    def _create_mocked_users_collection(self, employees_csv: str) -> None:
        """
        Create and provision mock users from employee CSV data for development and testing.

        This method processes employee CSV files to create a comprehensive user database
        with proper role distribution and secure password hashing. Essential for development
        environments and system testing with realistic user data.

        CSV Format Requirements:
        - Required Columns: "First Name", "Last Name", "e-mail", "CorpKey"
        - Delimiter: Semicolon (;) separated values
        - Encoding: UTF-8 compatible format

        Role Distribution Strategy:
        - Admin: 10 users with full system access
        - Auditor: 10 users with audit log access
        - Descrubber: 10 users with scrubbing and descrubbing capabilities
        - Scrubber: Remaining users with basic scrubbing access only

        Args:
            employees_csv (str): Absolute path to employee CSV file for user provisioning

        Raises:
            FileNotFoundError: When the specified CSV file does not exist
            pandas.errors.ParserError: When CSV format is invalid or corrupted
            pymongo.errors.BulkWriteError: When database insertion fails

        Example CSV Format:
            ```csv
            First Name;Last Name;e-mail;CorpKey;Phone Number(s)
            John;Doe;john.doe@company.com;COMP001;+32123456789
            Jane;Smith;jane.smith@company.com;COMP002;+32987654321
            ```
        """
        if not os.path.exists(employees_csv):
            raise FileNotFoundError(f"File not found: {employees_csv}")

        df = pd.read_csv(employees_csv, sep=";")

        if "Phone Number(s)" in df.columns:
            df.drop(columns=["Phone Number(s)"], inplace=True)

        column_mapping = {
            "First Name": "first_name",
            "Last Name": "last_name",
            "e-mail": "email",
            "CorpKey": "corp_key",
        }
        df.rename(columns=column_mapping, inplace=True)

        df["password"] = df["corp_key"].apply(
            lambda x: hashlib.sha256(x.encode()).hexdigest()
        )

        roles = ["admin"] * 10 + ["auditor"] * 10 + ["descrubber"] * 10
        roles += ["scrubber"] * (len(df) - len(roles))
        random.shuffle(roles)
        df["role"] = roles

        self.users.delete_many({})
        self.users.insert_many(df.to_dict("records"))

        logging.info(f"{len(df)} users inserted into MongoDB.")

    def get_user_by_email(self, email: str):
        """
        Retrieve a complete user document by email address for authentication and authorization.

        This method provides secure user lookup functionality with proper database connection
        validation and comprehensive user data retrieval for authentication workflows.

        Args:
            email (str): User email address for lookup (case-sensitive)

        Returns:
            dict | None: Complete user document with all fields or None if not found

        Raises:
            Exception: When database connection is not established or unavailable

        User Document Structure:
            ```python
            {
                "_id": ObjectId("..."),
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@company.com",
                "corp_key": "COMPANY_001",
                "password": "sha256_hash...",
                "role": "scrubber"
            }
            ```

        Example:
            ```python
            user = user_manager.get_user_by_email("john.doe@company.com")
            if user:
                print(f"User: {user['first_name']} {user['last_name']}")
                print(f"Role: {user['role']}")
                print(f"Corporate Key: {user['corp_key']}")
            ```
        """
        if self.users is None:
            raise Exception("Database connection is not established.")

        return self.users.find_one({"email": email})

    def check_user_credentials(self, email: str, password: str):
        """
        Authenticate user credentials with secure password verification and comprehensive validation.

        This method provides the core authentication functionality for the SecurePrompt banking
        application with SHA-256 password verification and complete user data retrieval for
        successful authentications.

        Args:
            email (str): User email address for authentication
            password (str): Plaintext password for verification

        Returns:
            dict | None: Complete user document for valid credentials, None for invalid

        Authentication Flow:
            1. User lookup by email address
            2. Password hashing with SHA-256
            3. Hash comparison with stored password
            4. Return user document or None based on verification result

        Example:
            ```python
            user = user_manager.check_user_credentials("john.doe@company.com", "password123")
            if user:
                print(f"Authentication successful for {user['email']}")
                print(f"Role: {user['role']}, Corp: {user['corp_key']}")
                # Proceed with JWT token generation
            else:
                print("Invalid credentials")
                # Return authentication error
            ```
        """
        user = self.get_user_by_email(email)
        if not user:
            return None
        hash_password = hashlib.sha256(password.encode()).hexdigest()
        return user if user["password"] == hash_password else None
