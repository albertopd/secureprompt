from enum import Enum
import pandas as pd
import os

# --- Constants ---
API_URL = os.environ.get("SECUREPROMPT_API", "http://localhost:8000/api/v1")


# --- Helpers ---
def load_css(css_file_path) -> str:
    """Reads a CSS file and returns its content as a string."""
    try:
        with open(css_file_path) as f:
           return f.read()
    except FileNotFoundError:
        return ""

def create_scrubbed_entity_report(entities):
    """
    Creates a pandas DataFrame report from a list of scrubbed entities.
    """
    rows = []
    for e in entities:
        score_val = e.get("score", "")
        # try to coerce to float and format: as percent if 0..1, otherwise rounded number
        score_display = ""
        try:
            s = float(score_val)
            if 0.0 <= s <= 1.0:
                score_display = f"{s:.1%}"  # e.g. 0.87 -> "87.0%"
            else:
                score_display = f"{s:.3f}"  # e.g. 123 -> "123.000"
        except Exception:
            score_display = score_val  # keep original if not numeric

        rows.append(
            {
                "Original": e.get("original", ""),
                "Replacement": e.get("replacement", ""),
                "Reason": e.get("explanation", ""),
                "Score": score_display
            }
        )

    df = pd.DataFrame(
        rows,
        columns=["Original", "Replacement", "Reason", "Score"]
    )

    return df


class RiskLevel(Enum):
    C1 = "C1 Public"
    C2 = "C2 Restricted"
    C3 = "C3 Confidential"
    C4 = "C4 Secret / C3 Sensitive"

risk_options = [m.name for m in RiskLevel]

def get_risk_label(option: str) -> str:
    """
    Returns the display label for a given risk level option.
    """
    try:
        return RiskLevel[option].value
    except KeyError:
        return option