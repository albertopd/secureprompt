from pathlib import Path
import pandas as pd
from typing import List, Tuple


# Pointe vers le dossier backend/tests/data/prompts 
_DEFAULT_PROMPTS_DIR = Path(__file__).parent.parent / "data" / "prompts"
_PROMPT_COLUMN = "Prompt"
_SANITIZED_COLUMN = "Sanitized_Prompt"


def load_test_cases_from_excels(
    data_dir: str = _DEFAULT_PROMPTS_DIR
) -> List[Tuple[str, str, str]]:
    """
    Load (file, input_prompt, sanitized_prompt) tuples from all Excel files in a folder.

    Files missing the required columns ('Prompt' and 'Sanitized Prompt') are skipped.

    Args:
        data_dir (str): Directory containing Excel files with prompt data.

    Returns:
        list: List of tuples (filename, input_prompt, sanitized_prompt) for each row in valid Excel files.
    """
    base_path = Path(data_dir)
    all_cases: List[Tuple[str, str, str]] = []

    for excel_file in base_path.glob("*.xlsx"):
        df = pd.read_excel(excel_file)
        missing_columns = [col for col in [_PROMPT_COLUMN, _SANITIZED_COLUMN] if col not in df.columns]

        if missing_columns:
            print(f"Skipping {excel_file.name}: missing columns {missing_columns}")
            continue  

        for _, row in df.iterrows():
            input_prompt = str(row[_PROMPT_COLUMN])
            sanitized_prompt = str(row[_SANITIZED_COLUMN])
            all_cases.append((excel_file.name, input_prompt, sanitized_prompt))

    return all_cases

def load_test_cases_from_csv(
    data_dir: str = _DEFAULT_PROMPTS_DIR
) -> List[Tuple[str, str, str]]:
    """
    Load (file, input_prompt, sanitized_prompt) tuples from all CSV files in a folder.

    Files missing the required columns ('Prompt' and 'Sanitized Prompt' or 'Sanitized_Prompt') are skipped.

    Args:
        data_dir (str): Directory containing CSV files with prompt data.

    Returns:
        list: List of tuples (filename, input_prompt, sanitized_prompt) for each row in valid CSV files.
    """
    base_path = Path(data_dir)
    all_cases: List[Tuple[str, str, str]] = []

    for csv_file in base_path.glob("*.csv"):
        try:
            df = pd.read_csv(csv_file)
            
            # Check for both possible sanitized column names
            sanitized_col = None
            if "Sanitized_Prompt" in df.columns:
                sanitized_col = "Sanitized_Prompt"
            elif "Sanitized Prompt" in df.columns:
                sanitized_col = "Sanitized Prompt"
            
            # Skip if required columns are missing
            if _PROMPT_COLUMN not in df.columns or sanitized_col is None:
                continue

            for _, row in df.iterrows():
                input_prompt = str(row[_PROMPT_COLUMN])
                sanitized_prompt = str(row[sanitized_col])
                all_cases.append((csv_file.name, input_prompt, sanitized_prompt))
            
        except Exception as e:
            # Silently skip problematic files
            continue

    return all_cases