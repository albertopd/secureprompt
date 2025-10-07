import hashlib
import logging
import os
import pandas as pd
import random
from pymongo import MongoClient
from core.config import settings


class UserManager:
    def __init__(self, client: MongoClient):
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
        Create mocked users from a CSV file and insert them into MongoDB.
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
        Retrieve a user document by email.
        """
        if self.users is None:
            raise Exception("Database connection is not established.")

        return self.users.find_one({"email": email})

    def check_user_credentials(self, email: str, password: str):
        """
        Check if the provided email and password match a user in the database.
        """
        user = self.get_user_by_email(email)
        if not user:
            return None
        hash_password = hashlib.sha256(password.encode()).hexdigest()
        return user if user["password"] == hash_password else None
