import hashlib
import logging
import os
import pandas as pd
import random
from pymongo import MongoClient


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB", "secureprompt")
MONGO_DB_USER_COLLECTION = os.getenv("MONGO_DB_USER_COLLECTION", "users")


class UsersDatabase:
    def __init__(self, uri: str = MONGO_URI, db_name: str = MONGO_DB_NAME):
        self.uri = uri
        self.db_name = db_name
        self.client = None
        self.db = None
        self.users = None

    def __enter__(self):
        self.client = MongoClient(self.uri)
        self.db = self.client[self.db_name]
        self.users = self.db[MONGO_DB_USER_COLLECTION]
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            self.client.close()

    def create_mocked_users_collection(self, employees_csv: str) -> None:
        """
        Create mocked users from a CSV file and insert them into MongoDB.
        """
        if self.users is None:
            raise Exception("Database connection is not established.")
        
        if not os.path.exists(employees_csv):
            raise FileNotFoundError(f"File not found: {employees_csv}")

        df = pd.read_csv(employees_csv, sep=";")

        if "Phone Number(s)" in df.columns:
            df.drop(columns=["Phone Number(s)"], inplace=True)

        column_mapping = {
            "First Name": "first_name",
            "Last Name": "last_name",
            "e-mail": "email",
            "CorpKey": "corp_key"
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


if __name__ == "__main__":
    with UsersDatabase() as users_db:
        employees_csv = os.getenv("EMPLOYEES_CSV", "data/employees/04_c2_employee_data.csv")
        users_db.create_mocked_users_collection(employees_csv)