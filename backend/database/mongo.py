import os
import pandas as pd
import random
from pymongo import MongoClient


def get_collection(collection_name: str):
    """
    Connect to MongoDB and return the specified collection.

    Args:
        collection_name (str): The name of the MongoDB collection to connect to.

    Returns:
        Collection: A pymongo collection object.
    """
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME = os.getenv("MONGO_DB", "secureprompt")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db[collection_name]


def create_mocked_users_collection(employees_csv: str) -> None:
    """
    Create mocked users from a CSV file and insert them into MongoDB.
    """
    if not os.path.exists(employees_csv):
        raise FileNotFoundError(f"File not found: {employees_csv}")

    # Load employees with correct separator
    df = pd.read_csv(employees_csv, sep=";")

    # Drop unnecessary columns if they exist
    if "Phone Number(s)" in df.columns:
        df.drop(columns=["Phone Number(s)"], inplace=True)

    # Rename columns to match MongoDB schema using a mapping dictionary
    column_mapping = {
        "First Name": "first_name",
        "Last Name": "last_name",
        "e-mail": "email",
        "CorpKey": "corp_key"
    }
    df.rename(columns=column_mapping, inplace=True)

    # Create new column password using content of corp_key
    df["password"] = df["corp_key"]

    # Create roles: 10 admin, 10 auditor, rest user
    roles = ["admin"] * 10 + ["auditor"] * 10 + ["descrubber"] * 10
    roles += ["scrubber"] * (len(df) - len(roles))

    # Shuffle roles randomly
    random.shuffle(roles)

    # Add role column
    df["role"] = roles

    # Clean existing collection before inserting new data
    users = get_collection("users")
    users.delete_many({})

    # Insert all rows as documents in a single batch
    users.insert_many(df.to_dict("records"))

    print(f"{len(df)} users inserted into MongoDB.")


if __name__ == "__main__":
    create_mocked_users_collection("data/employees/04_c2_employee_data.csv")