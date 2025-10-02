import os
import pandas as pd
import random
from pymongo import MongoClient

def add_roles_and_save_csv(input_file: str, output_file: str) -> None:
    """
    Add roles to employees from the input CSV and save to a new CSV.

    Roles are assigned as follows:
    - 10 employees get "Administrator"
    - 10 employees get "Auditor"
    - The rest are assigned "User"

    Args:
        input_file (str): Path to the input employee CSV file.
        output_file (str): Path to the output CSV file with roles.

    Returns:
        None. A new CSV file is created with an additional 'role' column.
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"File not found: {input_file}")

    # Load employees with correct separator
    df = pd.read_csv(input_file, sep=";")

    # Create roles: 10 admin, 10 auditor, rest user
    roles = ["Administrator"] * 10 + ["Auditor"] * 10 + ["Advanced User"] * 10
    roles += ["User"] * (len(df) - len(roles))

    # Shuffle roles randomly
    random.shuffle(roles)

    # Add role column
    df["role"] = roles

    # Save to new CSV
    df.to_csv(output_file, index=False)
    print(f"New CSV with roles saved to {output_file}")

def import_employees_to_mongo(csv_file: str) -> None:
    """
    Import employees from a CSV and insert into MongoDB.

    Args:
        csv_file (str): Path to the input employee CSV file.

    Returns:
        None. Employees are inserted into MongoDB.
    """
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"File not found: {csv_file}")

    # Load employees
    df = pd.read_csv(csv_file)

    # Connect to MongoDB
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME = os.getenv("MONGO_DB", "secureprompt")

    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db["employees"]

    # Clean existing collection (optional, only if you want to reset each time)
    collection.delete_many({})

    # Insert each row as a separate document
    for _, row in df.iterrows():
        document = row.to_dict()  # Convert row to dictionary
        collection.insert_one(document)

    print("Employees inserted into MongoDB with proper structure.")

# Example usage
if __name__ == "__main__":
    input_file = "data\\DATA\\04_c2_employee_data.csv"
    output_file = "data\\DATA\\04_c2_employee_data_with_roles.csv"

    # Add roles and save to new CSV
    add_roles_and_save_csv(input_file, output_file)

    # Import data from new CSV to MongoDB
    import_employees_to_mongo(output_file)
