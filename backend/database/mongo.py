import os
import re
import csv
import pandas as pd
import random
from pymongo import MongoClient
from typing import Dict


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


def get_collection(collection_name: str):
    """
    Connect to MongoDB and return the specified collection.

    Args:
        collection_name (str): The name of the MongoDB collection to connect to.

    Returns:
        Collection: A pymongo collection object.
    """
    # Default to localhost for local (non-Docker) runs
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME = os.getenv("MONGO_DB", "secureprompt")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db[collection_name]


# -----------------------------
# LLM MongoDB Structures
# -----------------------------


def get_db():
    # Default to localhost for local (non-Docker) runs
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME = os.getenv("MONGO_DB", "secureprompt")
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]


def parse_security_from_filename(filename: str) -> str:
    """Extract c1/c2/c3/c4 from names like '07_c2_guidelines.csv'. Defaults to 'c1'."""
    m = re.search(r"_c([1-4])_", filename.lower())
    if m:
        return f"c{m.group(1)}"
    return "c1"


def derive_collection_name_from_filename(filename: str) -> str:
    """
    Derive a Mongo collection name from the ORIGINAL base filename (without extension)
    to preserve traceability. We only perform minimal sanitization to avoid
    problematic characters for MongoDB:
      - remove the file extension
      - trim whitespace
      - replace '$' with '_' (Mongo restriction)
      - avoid names starting with 'system.' by prefixing 'x_'

    Examples:
      04_c2_employee_data_with_roles.csv -> 04_c2_employee_data_with_roles
      11_c2_product_specifications.csv   -> 11_c2_product_specifications
      07_c2_ing_transfer_orders (IBAN!).csv -> 07_c2_ing_transfer_orders (IBAN!)
      plain.csv -> plain
    """
    base = os.path.splitext(os.path.basename(filename))[0]
    name = base.strip()
    # Replace Mongo-reserved character
    name = name.replace("$", "_")
    # Guard against reserved prefix
    if name.lower().startswith("system."):
        name = f"x_{name}"
    # Fallback name if empty
    return name or "data"


def import_collection(csv_file: str, collection_name: str | None = None, clear: bool = True) -> Dict[str, int]:
    """
    Import a CSV into a MongoDB collection under DB 'secureprompt'.
    - collection per file (derived from filename if not provided)
    - add per-row security tag based on filename (c1..c4)
    - optionally clear the collection before inserting
    Returns counts.
    """
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"File not found: {csv_file}")

    sec = parse_security_from_filename(os.path.basename(csv_file))
    coll_name = collection_name or derive_collection_name_from_filename(csv_file)

    # Read CSV with robust delimiter inference
    df = None
    # First try Python engine with automatic sep inference
    try:
        df = pd.read_csv(csv_file, sep=None, engine="python", encoding="utf-8-sig")
    except (UnicodeDecodeError, pd.errors.ParserError, OSError, ValueError):
        df = None
    # If still single column or failed, sniff delimiter and re-read
    if df is None or df.shape[1] == 1:
        # Sniff delimiter from a sample
        delimiter = ","
        try:
            with open(csv_file, "r", encoding="utf-8-sig", newline="") as f:
                sample = f.read(8192)
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
                delimiter = dialect.delimiter
        except Exception:
            # Heuristic fallback: count delimiters in header
            try:
                with open(csv_file, "r", encoding="utf-8-sig", newline="") as f:
                    header = f.readline()
                    counts = {";": header.count(";"), ",": header.count(","), "\t": header.count("\t")}
                    delimiter = max(counts, key=counts.get) if any(counts.values()) else ","
            except Exception:
                delimiter = ","
        # Re-read with the chosen delimiter; fallback encoding cp1252 if needed
        try:
            df = pd.read_csv(csv_file, sep=delimiter, encoding="utf-8-sig")
        except UnicodeDecodeError:
            df = pd.read_csv(csv_file, sep=delimiter, encoding="cp1252")

    # Optional: common normalization for known columns
    if "e-mail" in df.columns and "email" not in df.columns:
        df.rename(columns={"e-mail": "email"}, inplace=True)

    # Add security column to each row
    df["security"] = sec
    df["source_file"] = os.path.basename(csv_file)
    df.reset_index(drop=True, inplace=True)
    df["row_idx"] = df.index

    col = get_collection(coll_name)
    if clear:
        col.delete_many({})

    records = df.to_dict(orient="records")
    if records:
        col.insert_many(records)

    return {"collection": coll_name, "rows": len(records), "security": sec}


def import_all_collections(data_folder: str, clear_each: bool = True) -> Dict[str, Dict[str, int]]:
    """Import all CSV files in data_folder into per-file collections."""
    results: Dict[str, Dict[str, int]] = {}
    if not os.path.isdir(data_folder):
        return results
    for fname in os.listdir(data_folder):
        if not fname.lower().endswith(".csv"):
            continue
        path = os.path.join(data_folder, fname)
        try:
            res = import_collection(path, clear=clear_each)
            results[fname] = res
        except (pd.errors.ParserError, UnicodeDecodeError, OSError, ValueError) as e:
            results[fname] = {"error": str(e)}
    return results


# Example usage
if __name__ == "__main__":
    # Local runner: import all CSVs in data/DATA into per-file collections
    # Resolve DATA folder: env var DATA_FOLDER wins, else try repo-root/data/DATA
    env_dir = os.environ.get("DATA_FOLDER")
    if env_dir and os.path.isdir(env_dir):
        data_dir = env_dir
    else:
        here = os.path.abspath(__file__)
        backend_dir = os.path.dirname(os.path.dirname(here))  # .../secureprompt/backend
        repo_root = os.path.dirname(backend_dir)              # .../secureprompt
        candidates = [
            os.path.join(repo_root, "data", "DATA"),       # preferred
            os.path.join(backend_dir, "data", "DATA"),     # fallback
        ]
        data_dir = next((p for p in candidates if os.path.isdir(p)), None)

    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    mongo_db = os.getenv("MONGO_DB", "secureprompt")
    print(f"[mongo.py] MONGO_URI={mongo_uri} DB={mongo_db}")

    if not data_dir or not os.path.isdir(data_dir):
        raise SystemExit("[mongo.py] Could not find data/DATA. Set DATA_FOLDER or create data/DATA at repo root.")

    csvs = [f for f in os.listdir(data_dir) if f.lower().endswith(".csv")]
    print(f"[mongo.py] Importing from: {data_dir}")
    print(f"[mongo.py] Found {len(csvs)} CSV(s): {', '.join(csvs) if csvs else '(none)'}")

    summary = import_all_collections(data_dir, clear_each=True)
    print("[mongo.py] Import summary:")
    print(summary)
